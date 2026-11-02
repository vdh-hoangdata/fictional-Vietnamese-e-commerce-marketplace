import bisect
from collections import defaultdict
from datetime import datetime, timedelta

from src.utils.core import CUTOFF, END, START, VN, UTC, incident, local_date, rng, stamp

REGIONS = ["Ha Noi", "Ho Chi Minh City", "Da Nang", "Can Tho", "Hai Phong", "Thua Thien Hue"]
DEPARTMENTS = ["Electronics", "Fashion", "Beauty", "Home Appliances", "Groceries", "Lifestyle"]
LEAVES = [("Phones", "Accessories"), ("Clothing", "Footwear"), ("Skincare", "Cosmetics"),
          ("Kitchen", "Home Care"), ("Pantry", "Beverages"), ("Sports", "Stationery")]
BASE_PRICES = [4500000, 290000, 240000, 1800000, 65000, 170000]


class WeightedPool:
    def __init__(self, entries, weights):
        self.entries = entries
        self.cumulative = []
        total = 0
        for weight in weights:
            total += weight
            self.cumulative.append(total)

    def pick(self, random, limit=None):
        count = len(self.entries) if limit is None else limit
        if count < 1:
            raise ValueError("No available candidates")
        return self.entries[bisect.bisect_right(self.cumulative, random.random() * self.cumulative[count - 1], 0, count)]


def day_intensity(day):
    factor = 1.16 if day.weekday() >= 5 else 1.0
    if day.day >= 25 or day.day <= 3:
        factor *= 1.32
    if day.month in {1, 2}:
        factor *= 1.20
    if day.month in {9, 10, 11, 12} and day.day == day.month:
        factor *= 4.2
    if day.month == 11 and day.weekday() == 4 and 23 <= day.day <= 29:
        factor *= 2.5
    if day.month == 12:
        factor *= 1.23
    return factor


def marketing(sink, settings):
    random = rng(settings.seed, "marketing")
    campaigns, daily = [], defaultdict(list)
    scale = settings.counts["orders"] / 100000
    for year in (2024, 2025):
        for month in range(1, 13):
            start = datetime(year, month, 1, tzinfo=VN).astimezone(UTC)
            end = (datetime(year + 1, 1, 1, tzinfo=VN) if month == 12 else datetime(year, month + 1, 1, tzinfo=VN)).astimezone(UTC)
            for mega in ([False, True] if month in {9, 10, 11, 12} else [False]):
                flight_start = start + timedelta(days=month - 4) if mega else start
                flight_end = min(end, flight_start + timedelta(days=9)) if mega else end
                if mega and year == 2025 and month == 11:
                    flight_start = datetime.fromisoformat(settings.incidents["margin_campaign"][0]).replace(tzinfo=VN).astimezone(UTC)
                    flight_end = datetime.fromisoformat(settings.incidents["margin_campaign"][1]).replace(tzinfo=VN).astimezone(UTC) + timedelta(days=1)
                cid = sink.next_id("marketing_campaigns")
                campaign = dict(campaign_id=cid, campaign_name=f"VietCommerce {year}-{month:02d} {'Mega' if mega else 'Discovery'}",
                                objective="promotion" if mega else "acquisition", channel=random.choice(["social", "search", "affiliate"]),
                                starts_at=stamp(flight_start), ends_at=stamp(flight_end), budget=0)
                rows, cursor = [], flight_start
                while cursor < flight_end:
                    spend = max(10000, int((2200000 if mega else 1000000) * scale * day_intensity(local_date(cursor)) * random.uniform(.85, 1.15)))
                    if incident(settings, "margin_campaign", cursor):
                        spend *= 3
                    row = dict(spend_id=sink.next_id("marketing_spend_daily"), campaign_id=cid,
                               spend_date=str(local_date(cursor)), channel=campaign["channel"], spend_amount=spend,
                               impressions=spend // 12, clicks=spend // 650)
                    rows.append(row)
                    daily[str(local_date(cursor))].append((campaign, spend))
                    cursor += timedelta(days=1)
                campaign["budget"] = sum(r["spend_amount"] for r in rows) * 12 // 10
                sink.emit("marketing_campaigns", campaign)
                for row in rows:
                    sink.emit("marketing_spend_daily", row)
                coupon = dict(coupon_id=cid, campaign_id=cid, coupon_code=f"VC{year}{month:02d}{cid}",
                              discount_type="percent", discount_value=22 if mega and year == 2025 and month == 11 else 15 if mega else 7, minimum_spend=150000,
                              maximum_discount=200000, category_id=None if cid % 5 else 2,
                              starts_at=campaign["starts_at"], ends_at=campaign["ends_at"],
                              redemption_limit=max(20, settings.counts["orders"] // 10))
                sink.emit("coupons", coupon)
                campaign["coupon"] = coupon
                campaigns.append(campaign)
    return campaigns, daily


def masters(sink, cdc, settings, daily_marketing):
    random = rng(settings.seed, "master_dimensions")
    warehouses, sellers, products, customers = {}, {}, {}, []
    for i, region in enumerate(REGIONS, 1):
        row = dict(warehouse_id=i, warehouse_name=f"VC Synthetic Hub {i}", province=region,
                   warehouse_type="central" if i <= 2 else "regional", status="operational")
        warehouses[i] = row
        sink.emit("warehouses", row)
    for i in range(1, settings.counts["sellers"] + 1):
        warehouse_id = (i - 1) % len(warehouses) + 1
        row = dict(seller_id=i, seller_name=f"Cua hang Mo Phong {i:05d}", seller_type="company_operated" if i % 11 == 0 else "independent",
                   registered_at=stamp(START - timedelta(days=400 + i % 100)), province=REGIONS[warehouse_id - 1], status="active", warehouse_id=warehouse_id)
        sellers[i] = row
        sink.emit("sellers", row)
    for dept, (name, leaves) in enumerate(zip(DEPARTMENTS, LEAVES), 1):
        sink.emit("categories", dict(category_id=dept, category_name=name, parent_category_id=None, category_level=1))
        for leaf, label in enumerate(leaves):
            sink.emit("categories", dict(category_id=dept * 100 + leaf + 1, category_name=label, parent_category_id=dept, category_level=2))
    pools = defaultdict(list)
    for i in range(1, settings.counts["products"] + 1):
        dept = (i - 1) % 6 + 1
        seller_id = random.randint(1, len(sellers))
        launch = START - timedelta(days=random.randint(2, 180)) if random.random() < .68 or i <= 6 else START + timedelta(days=random.randint(1, 650))
        discontinued = START + timedelta(days=random.randint(400, 705)) if launch < START and random.random() < .09 else None
        base_price = max(10000, int(BASE_PRICES[dept - 1] * random.lognormvariate(0, .62)) // 1000 * 1000)
        cost = base_price * random.randint(65, 94) // 100
        row = dict(product_id=i, seller_id=seller_id, category_id=dept * 100 + random.randint(1, 2), brand=f"MoPhong{dept}",
                   product_name=f"{LEAVES[dept - 1][(i // 6) % 2]} VC-{i:05d}", unit_cost=cost,
                   attributes={"model": f"S{i % 41}", "color": random.choice(["black", "white", "blue"]), "size": random.choice(["S", "M", "L", "standard"])},
                   launched_at=stamp(launch), discontinued_at=stamp(discontinued), is_active=int(discontinued is None))
        sink.emit("products", row)
        cdc_states = [(launch, dict(is_active=1, discontinued_at=None), "catalog_launch")]
        if discontinued:
            cdc_states.append((discontinued, {}, "catalog_discontinued"))
        cdc.history("products", row, cdc_states)
        bound = discontinued or END
        boundaries = [launch] + [point for point in (START + timedelta(days=180), START + timedelta(days=366), START + timedelta(days=600)) if launch < point < bound] + [bound]
        prices = []
        for interval, (begin, finish) in enumerate(zip(boundaries, boundaries[1:])):
            listed = base_price * (100 - interval * 3) // 100
            promo = listed * 93 // 100 if interval % 2 else None
            sink.emit("product_price_history", dict(price_history_id=sink.next_id("product_price_history"), product_id=i,
                      effective_from=stamp(begin), effective_to=stamp(finish), listed_price=listed, promotional_price=promo,
                      change_reason="launch" if not interval else ("seasonal_offer" if promo else "repricing")))
            prices.append((begin, finish, promo if promo is not None else listed))
        product = dict(row, department=dept, launch=launch, discontinued=discontinued, prices=prices,
                       warehouse_id=sellers[seller_id]["warehouse_id"], popularity=min(1500, random.paretovariate(1.25)))
        products[i] = product
        pools[dept].append(product)
    product_pools = {dept: WeightedPool(rows, [p["popularity"] for p in rows]) for dept, rows in pools.items()}
    family = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Vu", "Do", "Bui"]
    given = ["An", "Binh", "Chi", "Dung", "Giang", "Ha", "Lam", "Minh", "Phuong", "Trang"]
    for i in range(1, settings.counts["customers"] + 1):
        joined = START - timedelta(days=random.randint(1, 180)) if random.random() < .42 or i == 1 else START + timedelta(days=random.randint(0, 715), seconds=random.randint(0, 80000))
        lapse = joined + timedelta(days=random.randint(90, 400)) if random.random() < .16 and i != 1 else None
        if lapse and lapse > CUTOFF:
            lapse = None
        flights = daily_marketing.get(str(local_date(joined)), [])
        paid_chance = min(.8, .15 + sum(s for _, s in flights) / max(1, settings.counts["orders"] * 40))
        channel = random.choice(["social", "search", "affiliate"]) if flights and random.random() < paid_chance else random.choice(["organic", "referral", "direct"])
        row = dict(customer_id=i, customer_name=f"{random.choice(family)} {random.choice(given)} MoPhong-{i:06d}",
                   email=f"kh{i:07d}@example.invalid" if random.random() > .08 else None,
                   phone=f"SYNTHETIC-PHONE-{i:07d}" if random.random() > .2 else None,
                   registered_at=stamp(joined), inactive_at=stamp(lapse), status="inactive" if lapse else "active",
                   acquisition_channel=channel, spending_segment=random.choices(["budget", "mainstream", "premium"], [4, 5, 1])[0])
        sink.emit("customers", row)
        addresses = []
        for j in range(1 + (random.random() < .23)):
            aid = sink.next_id("customer_addresses")
            address = dict(address_id=aid, customer_id=i, province=random.choice(REGIONS), district=None,
                           address_line=f"Dia chi gia lap VC-{i:06d}-{j}; Pho Mo Phong", postal_code=None, is_default=int(j == 0))
            sink.emit("customer_addresses", address)
            addresses.append(address)
        customers.append(dict(row, joined=joined, lapse=lapse, addresses=addresses,
                              weight=min(1500, random.paretovariate(1.32))))
    customers.sort(key=lambda c: c["joined"])
    customer_pool = WeightedPool(customers, [c["weight"] for c in customers])
    return dict(products=products, product_pools=product_pools, customers=customers, customer_pool=customer_pool,
                join_times=[c["joined"] for c in customers], warehouses=warehouses, sellers=sellers)
