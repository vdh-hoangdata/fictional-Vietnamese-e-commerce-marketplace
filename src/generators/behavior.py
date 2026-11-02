from datetime import timedelta

from src.utils.core import CUTOFF, START, VN, incident, rng, stamp


class Behavior:
    def __init__(self, sink, settings, daily):
        self.sink, self.settings, self.daily = sink, settings, daily
        self.random = rng(settings.seed, "behavior_events")
        self.session_id = 0

    def session(self, when, customer, items, order, confirmed_at, campaign):
        self.session_id += 1
        sid = f"session-{self.session_id:010d}"
        random = self.random
        registered = customer["joined"] if customer else when - timedelta(days=1)
        start = max(START, registered, when - timedelta(minutes=random.randint(3, 15)))
        steps = ["page_view", "product_view"]
        if random.random() < .32:
            steps.append("search")
        if items:
            steps += ["add_to_cart"]
            if random.random() < .22:
                steps += ["product_view", "add_to_cart", "remove_from_cart"]
        if order:
            steps += ["checkout_started", "payment_started"]
            if confirmed_at:
                steps.append("purchase")
        elif random.random() < .35:
            steps.append("checkout_started")
        source = campaign["channel"] if campaign else random.choice(["direct", "organic"])
        device = order["sales_channel"] if order else random.choice(["website", "android", "ios"])
        visitor = f"device-{customer['customer_id']:08d}-{random.randint(1, 3)}" if customer else f"anon-{self.session_id:010d}"
        for i, step in enumerate(steps):
            moment = start + (when - start) * i / max(1, len(steps) - 1)
            moment = moment.replace(microsecond=0)
            if step == "purchase":
                moment = confirmed_at
            if moment > CUTOFF:
                continue
            product = items[0]["product_id"] if items and step in {"product_view", "add_to_cart", "remove_from_cart"} else None
            properties = {"page": {"path": "/checkout" if "checkout" in step or step in {"purchase", "payment_started"} else "/browse"},
                          "context": {"locale": "vi-VN", "currency": "VND"}}
            if step == "search":
                properties["query"] = random.choice(["ao", "dien thoai", "do nha", "qua tang"])
            if step == "purchase":
                properties.update(order_id=order["order_id"], value_vnd=order["total_payable"])
            if step in {"add_to_cart", "remove_from_cart"}:
                properties["quantity"] = 1
            observed_campaign = campaign["campaign_id"] if campaign and random.random() > .20 else None
            # A pre-purchase touch can differ from the recorded last touch.
            if i == 0 and random.random() < .15:
                flights = self.daily.get(str(moment.astimezone(VN).date()), [])
                if flights:
                    observed_campaign = random.choice(flights)[0]["campaign_id"]
            if observed_campaign:
                active = [c for c, _ in self.daily.get(str(moment.astimezone(VN).date()), []) if c["campaign_id"] == observed_campaign]
                if not active or not active[0]["starts_at"] <= stamp(moment) < active[0]["ends_at"]:
                    observed_campaign = None
            self.sink.emit("web_events", dict(event_id=self.sink.next_id("web_events"), anonymous_visitor_id=visitor,
                           session_id=sid, customer_id=customer["customer_id"] if customer else None, event_type=step,
                           event_at=stamp(moment), product_id=product, device_type="desktop" if device == "website" else device,
                           traffic_source=source, campaign_id=observed_campaign, properties=properties))

    def for_order(self, when, customer, items, order, confirmed, campaign):
        self.session(when, customer, items, order, confirmed, campaign)
        rate = self.settings.anonymous_sessions_per_order
        if incident(self.settings, "margin_campaign", when):
            rate *= 1.9
        if incident(self.settings, "payment_outage", when):
            rate *= 1.5
        count = int(rate) + (self.random.random() < rate % 1)
        for _ in range(count):
            self.session(when, None if self.random.random() < .78 else customer, items, None, None, campaign)
