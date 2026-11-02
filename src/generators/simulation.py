import bisect
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from src.business_rules.finance import allocate, returned_value
from src.generators.behavior import Behavior
from src.generators.inventory import Inventory
from src.generators.masters import day_intensity, masters, marketing
from src.utils.core import CUTOFF, END, START, VN, UTC, incident, local_date, parse, rng, stamp


class Simulation:
    def __init__(self, sink, cdc, settings):
        self.sink, self.cdc, self.settings = sink, cdc, settings
        self.random = rng(settings.seed, "order_simulation")
        self.payment_random = rng(settings.seed, "payments")
        self.logistics_random = rng(settings.seed, "logistics")
        self.experience_random = rng(settings.seed, "customer_experience")
        self.campaigns, self.daily = marketing(sink, settings)
        self.master = masters(sink, cdc, settings, self.daily)
        self.inventory = Inventory(sink, self.master["products"])
        self.behavior = Behavior(sink, settings, self.daily)
        self.redemptions = Counter()
        self.metrics = Counter()

    def run(self):
        demand_random = rng(self.settings.seed, "daily_demand")
        days = int((END - START).days)
        weights = []
        for offset in range(days):
            when = START + timedelta(days=offset)
            spend = sum(value for _, value in self.daily[str(local_date(when))])
            baseline = max(10000, self.settings.counts["orders"] * 10)
            weights.append(day_intensity(local_date(when)) * (1 + .45 * offset / days) * (1 + .22 * spend / baseline))
        counts = Counter(demand_random.choices(range(days), weights=weights, k=self.settings.counts["orders"]))
        for offset in range(days):
            seconds = sorted(demand_random.randrange(86400) for _ in range(counts[offset]))
            for second in seconds:
                when = START + timedelta(days=offset, seconds=second)
                self.inventory.advance(when)
                self.order(when)
        self.inventory.finish()
        # Small, explained positive cycle count corrections after all reservations settle.
        for product in list(self.master["products"].values())[:6]:
            self.inventory.apply(CUTOFF, product, "adjustment", 1, 0, "product", product["product_id"], "positive_cycle_count_correction")
        return dict(self.metrics)

    def choose_customer(self, when):
        limit = bisect.bisect_right(self.master["join_times"], when)
        for _ in range(200):
            customer = self.master["customer_pool"].pick(self.random, limit)
            if customer["lapse"] is None or when < customer["lapse"]:
                return customer
        return next(c for c in self.master["customers"][:limit] if c["lapse"] is None or when < c["lapse"])

    def choose_product(self, when, customer, used):
        weights = [25, 22, 17, 12, 16, 8]
        if local_date(when).month in {1, 2}:
            weights[4] *= 2
        if local_date(when).month in {11, 12}:
            weights[0] *= 1.7
        if customer["spending_segment"] == "premium":
            weights[0] *= 2.5
        if customer["spending_segment"] == "budget":
            weights[4] *= 2
        for _ in range(200):
            dept = self.random.choices(range(1, 7), weights=weights)[0]
            product = self.master["product_pools"][dept].pick(self.random)
            if product["product_id"] not in used and product["launch"] <= when - timedelta(minutes=16) and (product["discontinued"] is None or when < product["discontinued"]):
                return product
        return next(p for p in self.master["products"].values() if p["product_id"] not in used and p["launch"] <= when and (p["discontinued"] is None or when < p["discontinued"]))

    def order(self, when):
        random, sink = self.random, self.sink
        oid = sink.next_id("orders")
        customer = self.choose_customer(when)
        address = random.choice(customer["addresses"])
        flights = self.daily[str(local_date(when))]
        spend = sum(value for _, value in flights)
        paid_chance = min(.8, .25 + .10 * spend / max(10000, self.settings.counts["orders"] * 10))
        campaign = random.choices([c for c, _ in flights], weights=[v for _, v in flights])[0] if flights and random.random() < paid_chance else None
        items, product_rows, groups = [], {}, defaultdict(list)
        line_count = random.choices([1, 2, 3, 4, 5], [25, 32, 25, 13, 5])[0]
        for _ in range(line_count):
            product = self.choose_product(when, customer, product_rows)
            product_rows[product["product_id"]] = product
            price = next(price for start, end, price in product["prices"] if start <= when < end)
            qty = random.choices([1, 2, 3, 4], [72, 20, 6, 2])[0]
            gross = qty * price
            line = dict(order_item_id=sink.next_id("order_items"), order_id=oid, product_id=product["product_id"], seller_id=product["seller_id"],
                        quantity=qty, unit_price=price, item_gmv=gross, line_discount=gross * 2 // 100 if qty >= 3 else 0,
                        allocated_order_discount=0, item_amount=0)
            items.append(line)
            groups[product["seller_id"]].append(line)
        fees = {seller: (18000 if self.master["sellers"][seller]["province"] == address["province"] else 32000) for seller in groups}
        eligible = sum(i["item_gmv"] - i["line_discount"] for i in items)
        coupon, discount = campaign["coupon"] if campaign else None, 0
        if coupon and eligible >= coupon["minimum_spend"] and self.redemptions[coupon["coupon_id"]] < coupon["redemption_limit"] and random.random() < .62:
            if coupon["category_id"] is None or all(p["department"] == coupon["category_id"] for p in product_rows.values()):
                percent = coupon["discount_value"]
                # Discount is contractual: the margin campaign's stronger coupons are configured below.
                discount = min(coupon["maximum_discount"], eligible * percent // 100)
                self.redemptions[coupon["coupon_id"]] += 1
        allocations = allocate(discount, [i["item_gmv"] - i["line_discount"] for i in items])
        for item, allocation in zip(items, allocations):
            item["allocated_order_discount"] = allocation
            item["item_amount"] = item["item_gmv"] - item["line_discount"] - allocation
            sink.emit("order_items", item)
        order = dict(order_id=oid, customer_id=customer["customer_id"], address_id=address["address_id"], ordered_at=stamp(when),
                     sales_channel=random.choices(["website", "android", "ios"], [25, 48, 27])[0], status="created", currency="VND",
                     item_gmv=sum(i["item_gmv"] for i in items), line_discount=sum(i["line_discount"] for i in items), order_discount=discount,
                     shipping_fee=sum(fees.values()), total_payable=eligible - discount + sum(fees.values()),
                     campaign_id=campaign["campaign_id"] if campaign and random.random() > .18 else None)
        if discount:
            sink.emit("order_discounts", dict(order_discount_id=sink.next_id("order_discounts"), order_id=oid, coupon_id=coupon["coupon_id"],
                      allocation_method="largest_remainder", discount_amount=discount))
        payment_info = self.payment_plan(when, order)
        confirmed = payment_info["confirmed"]
        stages = [(when, "created", "checkout_submitted")]
        cancel_time = failure_end = last_delivery = None
        shipments = []
        if not confirmed:
            terminal_time = payment_info["decision_at"]
            if terminal_time <= CUTOFF:
                stages.append((terminal_time, payment_info["terminal"], "payment_not_completed"))
        else:
            if confirmed <= CUTOFF:
                stages.append((confirmed, "confirmed", "payment_accepted"))
            process = confirmed + timedelta(minutes=30)
            if incident(self.settings, "inventory_shortage", when) and random.random() < .38:
                release = datetime.fromisoformat(self.settings.incidents["inventory_shortage"][1]).replace(tzinfo=VN).astimezone(UTC) + timedelta(days=1)
                for product in product_rows.values():
                    if product["department"] == 1:
                        self.inventory.supplier_hold(when, product, release)
            shortage = any(self.inventory.holds.get(i["product_id"], when) > when and self.inventory.available(product_rows[i["product_id"]]) < i["quantity"] for i in items)
            ordinary_stockout = any(self.inventory.available(product_rows[i["product_id"]]) < i["quantity"] for i in items) and random.random() < .30
            cancelled = shortage or ordinary_stockout or random.random() < self.settings.cancellation_rate
            if cancelled:
                cancel_time = confirmed + timedelta(minutes=random.randint(10, 180))
                if process < cancel_time:
                    stages.append((process, "processing", "warehouse_acceptance"))
                stages.append((cancel_time, "cancelled", "inventory_shortage" if shortage or ordinary_stockout else "customer_cancellation"))
                if shortage:
                    self.metrics["shortage_cancellations"] += 1
                if not (shortage or ordinary_stockout):
                    for item in items:
                        product = product_rows[item["product_id"]]
                        self.inventory.reserve(when, product, item["quantity"], item["order_item_id"])
                        self.inventory.schedule(cancel_time, product, "cancellation_release", 0, -item["quantity"], "order_item", item["order_item_id"], "order_cancelled")
            else:
                stages.append((process, "processing", "warehouse_acceptance"))
                delivery_fail = self.logistics_random.random() < .025
                for seller_id, lines in groups.items():
                    shipment = self.shipment(when, confirmed, order, seller_id, lines, fees[seller_id], address, delivery_fail)
                    shipments.append(shipment)
                    for item in lines:
                        product = product_rows[item["product_id"]]
                        self.inventory.reserve(when, product, item["quantity"], item["order_item_id"])
                        self.inventory.schedule(shipment["ship_time"], product, "fulfillment", -item["quantity"], -item["quantity"],
                                                "order_item", item["order_item_id"], "carrier_handover")
                first_ship = min(s["ship_time"] for s in shipments)
                stages.append((first_ship, "shipped", "first_parcel_handover"))
                last_close = max(s["close_time"] for s in shipments)
                if delivery_fail:
                    failure_end = last_close
                    stages.append((last_close, "delivery_failed", "all_parcels_returned_to_sender"))
                    for item in items:
                        product = product_rows[item["product_id"]]
                        self.inventory.schedule(last_close + timedelta(days=1), product, "return_restock", item["quantity"], 0, "order_item", item["order_item_id"], "undelivered_parcel_restock")
                else:
                    last_delivery = last_close
                    stages.append((last_close, "delivered", "all_parcels_delivered"))
        # COD settlement and authorization state depend on fulfillment outcome.
        payment = self.emit_payments(payment_info, order, last_delivery, cancel_time, failure_end)
        valid_stages = [s for s in stages if s[0] <= CUTOFF]
        order["status"] = valid_stages[-1][1]
        sink.emit("orders", order)
        previous = None
        cdc_states = []
        for time, status, reason in valid_stages:
            sink.emit("order_status_history", dict(status_event_id=sink.next_id("order_status_history"), order_id=oid,
                      previous_status=previous, new_status=status, event_at=stamp(time), source_system="ecommerce_app", change_reason=reason))
            cdc_states.append((time, {"status": status}, reason))
            previous = status
        # A real attribution linkage is corrected after the checkout, never a financial mutation.
        if order["campaign_id"] and oid % 19 == 0:
            correction_time = min(CUTOFF, max(t for t, _, _ in valid_stages) + timedelta(seconds=1))
            cdc_states = [(t, dict(fields, campaign_id=None), reason) for t, fields, reason in cdc_states]
            cdc_states.append((correction_time, {}, "attribution_link_reconciled"))
        self.cdc.history("orders", order, cdc_states)
        self.behavior.for_order(when, customer, items, order, confirmed if confirmed and confirmed <= CUTOFF else None, campaign)
        if payment and payment["status"] == "captured":
            refund_time = cancel_time or failure_end
            if refund_time and refund_time <= CUTOFF:
                self.refund(order, payment, None, order["total_payable"], max(refund_time, payment_info["capture_time"]))
        if last_delivery and last_delivery <= CUTOFF:
            self.experience(order, customer, items, product_rows, last_delivery, payment)
        if payment_info["had_failure"]:
            self.ticket(order, "payment_failure", min(CUTOFF, when + timedelta(minutes=10)), "high" if payment_info["outage"] else "normal")
        for shipment in shipments:
            if shipment["close_time"] > shipment["expected"] and shipment["expected"] <= CUTOFF and self.experience_random.random() < .48:
                self.ticket(order, "delivery_delay", min(CUTOFF, shipment["expected"] + timedelta(hours=2)), "high")
        if oid % 143 == 0:
            self.ticket(order, "account", when, "normal", account=True)
        self.metrics[f"orders_{order['status']}"] += 1

    def payment_plan(self, when, order):
        random = self.payment_random
        method = random.choices(["cod", "bank_transfer", "card", "ewallet"], [42, 16, 15, 27])[0]
        provider = {"cod": "CarrierClearing", "bank_transfer": "BankSim", "card": "CardSim", "ewallet": "PayLotus"}[method]
        outage = method == "ewallet" and incident(self.settings, "payment_outage", when)
        failure_rate = .70 if outage else self.settings.payment_failure_rate
        failed = method != "cod" and random.random() < failure_rate
        retried = failed and random.random() < (.25 if outage else .65)
        success = not failed or (retried and random.random() < (.3 if outage else .9))
        abandoned = not success and random.random() < .32
        attempts = 2 if retried else 1
        confirmed = when + timedelta(minutes=3 + (5 if retried else 0)) if success else None
        capture = when + timedelta(minutes=2 + (5 if retried else 0))
        return dict(method=method, provider=provider, outage=outage, had_failure=failed, success=success,
                    attempts=attempts, confirmed=confirmed, capture_time=capture, when=when,
                    terminal="payment_abandoned" if abandoned else "payment_failed", decision_at=when + timedelta(minutes=10))

    def emit_payments(self, plan, order, delivered, cancelled, failed_delivery):
        last = None
        for attempt in range(1, plan["attempts"] + 1):
            when = plan["when"] + timedelta(seconds=30, minutes=5 * (attempt - 1))
            if when > CUTOFF:
                continue
            success = plan["success"] and attempt == plan["attempts"]
            cod = plan["method"] == "cod"
            authorization = when + timedelta(seconds=20) if success and not cod else None
            capture = (delivered + timedelta(days=self.payment_random.randint(2, 5))) if cod and delivered else (plan["capture_time"] if success and not cod else None)
            if success:
                if cod and (cancelled or failed_delivery):
                    status = "cancelled" if (cancelled or failed_delivery) <= CUTOFF else "pending_settlement"
                else:
                    status = "captured" if capture and capture <= CUTOFF else ("pending_settlement" if cod else "authorized" if authorization and authorization <= CUTOFF else "pending")
            else:
                status = "cancelled" if plan["terminal"] == "payment_abandoned" and attempt == plan["attempts"] else "failed"
            row = dict(payment_id=self.sink.next_id("payments"), order_id=order["order_id"], provider=plan["provider"], method=plan["method"],
                       attempt_number=attempt, status=status, attempted_at=stamp(when), authorized_at=stamp(authorization) if authorization and authorization <= CUTOFF else None,
                       captured_at=stamp(capture) if status == "captured" else None, amount=order["total_payable"],
                       failure_code=None if success else ("PROVIDER_UNAVAILABLE" if plan["outage"] else "USER_ABANDONED" if status == "cancelled" else "DECLINED"))
            self.sink.emit("payments", row)
            states = [(when, dict(status="pending_settlement" if cod else "pending",
                       captured_at=None, authorized_at=None, failure_code=None), "attempt_started")]
            if authorization and authorization <= CUTOFF:
                states.append((authorization, dict(status="authorized", captured_at=None), "provider_authorized"))
            final_time = capture if status == "captured" else ((cancelled or failed_delivery) if status == "cancelled" and success else when)
            if final_time and final_time <= CUTOFF:
                states.append((final_time, {}, "cash_captured" if status == "captured" else "attempt_closed"))
            self.cdc.history("payments", row, states)
            last = row
        return last

    def shipment(self, when, confirmed, order, seller, lines, fee, address, failed):
        random = self.logistics_random
        created = confirmed + timedelta(minutes=30)
        ship_time = created + timedelta(hours=random.randint(6, 30))
        region = self.master["sellers"][seller]["province"]
        partner = random.choices(["LotusExpress", "MekongParcel", "BambooShip"], [45, 35, 20])[0]
        sla = (2 if region == address["province"] else 4) + (1 if partner == "BambooShip" else 0)
        expected = ship_time + timedelta(days=sla)
        disrupted = partner == "MekongParcel" and incident(self.settings, "carrier_disruption", when)
        delay = random.randint(4, 9) if disrupted else (random.randint(1, 4) if random.random() < .12 else 0)
        failed_attempt = failed or delay > 0 or random.random() < .055
        close = ship_time + timedelta(days=max(1, sla - 1) + delay, hours=random.randint(0, 20))
        events = [(created, "ready"), (ship_time, "shipped"), (ship_time + timedelta(hours=12), "in_transit")]
        if failed_attempt:
            events.append((ship_time + timedelta(days=1), "delivery_attempt_failed"))
        events.append((close, "returned_to_sender" if failed else "delivered"))
        seen = [(t, state) for t, state in events if t <= CUTOFF]
        # If parcel creation is beyond cutoff there is no shipment yet; preserve a ready snapshot
        # only for a real creation. The maximum confirmation offset makes this a rare boundary.
        if created > CUTOFF:
            return dict(ship_time=ship_time, close_time=close, expected=expected)
        final_state = seen[-1][1]
        status = "delivered" if final_state == "delivered" else "returned_to_sender" if final_state == "returned_to_sender" else "ready" if final_state == "ready" else "shipped"
        shipment = dict(shipment_id=self.sink.next_id("shipments"), order_id=order["order_id"], seller_id=seller,
                        warehouse_id=self.master["sellers"][seller]["warehouse_id"], delivery_partner=partner, shipping_fee=fee, status=status,
                        created_at=stamp(created), shipped_at=stamp(ship_time) if ship_time <= CUTOFF else None, expected_delivery_at=stamp(expected),
                        delivered_at=stamp(close) if not failed and close <= CUTOFF else None, closed_at=stamp(close) if close <= CUTOFF else None, sla_days=sla)
        self.sink.emit("shipments", shipment)
        for line in lines:
            self.sink.emit("shipment_items", dict(shipment_item_id=self.sink.next_id("shipment_items"), shipment_id=shipment["shipment_id"],
                           order_item_id=line["order_item_id"], quantity=line["quantity"]))
        states = []
        for seq, (time, state) in enumerate(seen, 1):
            self.sink.emit("shipment_events", dict(shipment_event_id=self.sink.next_id("shipment_events"), shipment_id=shipment["shipment_id"], event_at=stamp(time),
                           event_type=state, event_location=address["province"] if seq > 2 else region, event_sequence=seq))
            snapshot_state = "ready" if state == "ready" else state if state in {"delivered", "returned_to_sender"} else "shipped"
            fields = dict(status=snapshot_state, shipped_at=stamp(ship_time) if time >= ship_time else None,
                          delivered_at=shipment["delivered_at"] if state == "delivered" else None, closed_at=shipment["closed_at"] if time >= close else None)
            states.append((time, fields, state))
        self.cdc.history("shipments", shipment, states)
        if disrupted:
            self.metrics["disrupted_shipments"] += 1
        return dict(ship_time=ship_time, close_time=close, expected=expected)

    def refund(self, order, payment, return_id, amount, requested):
        if requested > CUTOFF:
            return
        done = requested + timedelta(days=self.experience_random.randint(1, 5))
        complete = done <= CUTOFF
        self.sink.emit("refunds", dict(refund_id=self.sink.next_id("refunds"), payment_id=payment["payment_id"], order_id=order["order_id"], return_id=return_id,
                       requested_amount=amount, refunded_amount=amount if complete else 0, status="completed" if complete else "pending",
                       requested_at=stamp(requested), refunded_at=stamp(done) if complete else None))
        if self.experience_random.random() < .34:
            self.ticket(order, "refund_status", min(CUTOFF, requested + timedelta(hours=20)), "normal")

    def experience(self, order, customer, items, products, delivery, payment):
        random = self.experience_random
        for item in items:
            product = products[item["product_id"]]
            quality = product["department"] == 3 and incident(self.settings, "quality_issue", parse(order["ordered_at"]))
            return_rate = .40 if quality else self.settings.return_rate * (1.7 if product["department"] == 2 else 1)
            returned = random.random() < return_rate
            if returned:
                requested = delivery + timedelta(days=random.randint(1, 8))
                received = requested + timedelta(days=random.randint(2, 5))
                rejected = random.random() < .10
                qty = random.randint(1, item["quantity"])
                if requested <= CUTOFF:
                    rid = self.sink.next_id("returns")
                    accepted = not rejected and received <= CUTOFF
                    self.sink.emit("returns", dict(return_id=rid, order_id=order["order_id"], order_item_id=item["order_item_id"], requested_quantity=qty,
                                   reason="quality" if quality else random.choice(["size_fit", "changed_mind", "quality"]), requested_at=stamp(requested),
                                   received_at=stamp(received) if accepted else None, status="received" if accepted else "rejected" if rejected else "requested",
                                   outcome="refund_and_restock" if accepted else "rejected" if rejected else "awaiting_inspection"))
                    if accepted:
                        self.inventory.schedule(received, product, "return_restock", qty, 0, "return", rid, "accepted_item_return")
                        if payment and payment["status"] == "captured":
                            refund_time = max(received, parse(payment["captured_at"]))
                            self.refund(order, payment, rid, returned_value(item["item_amount"], item["quantity"], qty), refund_time)
                    if quality or random.random() < .35:
                        self.ticket(order, "product_quality", requested, "high" if quality else "normal")
                    if quality:
                        self.metrics["quality_incident_returns"] += 1
            if random.random() < .22:
                reviewed = delivery + timedelta(days=random.randint(1, 18))
                if reviewed <= CUTOFF:
                    rating = random.choices([1, 2, 3, 4, 5], [35, 30, 20, 10, 5] if returned or quality else [2, 3, 10, 32, 53])[0]
                    self.sink.emit("reviews", dict(review_id=self.sink.next_id("reviews"), customer_id=customer["customer_id"], product_id=item["product_id"], order_item_id=item["order_item_id"],
                                   rating=rating, reviewed_at=stamp(reviewed), review_text="San pham mo phong: can cai thien" if rating < 3 else "Danh gia gia lap: hai long"))

    def ticket(self, order, category, created, priority, account=False):
        response = created + timedelta(hours=self.experience_random.randint(1, 30))
        resolved = response + timedelta(hours=self.experience_random.randint(2, 96))
        self.sink.emit("support_tickets", dict(ticket_id=self.sink.next_id("support_tickets"), customer_id=order["customer_id"], order_id=None if account else order["order_id"],
                       issue_category=category, priority=priority, created_at=stamp(created), first_response_at=stamp(response) if response <= CUTOFF else None,
                       resolved_at=stamp(resolved) if resolved <= CUTOFF else None, status="resolved" if resolved <= CUTOFF else "in_progress" if response <= CUTOFF else "open"))
