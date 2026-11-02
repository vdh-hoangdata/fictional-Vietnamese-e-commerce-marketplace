import heapq
from collections import defaultdict
from datetime import timedelta

from src.utils.core import CUTOFF, stamp


class Inventory:
    def __init__(self, sink, products):
        self.sink, self.stock, self.reserved = sink, defaultdict(int), defaultdict(int)
        self.queue, self.sequence = [], 0
        self.holds = {}
        for product in products.values():
            self.schedule(product["launch"] - timedelta(seconds=1), product, "receiving", 60, 0,
                          "product", product["product_id"], "opening_or_launch_stock")

    def apply(self, when, product, kind, physical, reserved, ref_type, ref_id, reason):
        key = (product["product_id"], product["warehouse_id"])
        self.stock[key] += physical
        self.reserved[key] += reserved
        if not 0 <= self.reserved[key] <= self.stock[key]:
            raise ValueError(f"Inventory invariant failed: {key} {when}")
        self.sink.emit("inventory_movements", dict(movement_id=self.sink.next_id("inventory_movements"), product_id=key[0],
                       warehouse_id=key[1], movement_type=kind, quantity_delta=physical, reserved_delta=reserved,
                       reference_type=ref_type, reference_id=ref_id, event_at=stamp(when), reason=reason))

    def schedule(self, when, *args):
        self.sequence += 1
        heapq.heappush(self.queue, (when, self.sequence, args))

    def advance(self, when):
        while self.queue and self.queue[0][0] <= when:
            event_at, _, args = heapq.heappop(self.queue)
            self.apply(event_at, *args)

    def reserve(self, when, product, quantity, item_id):
        key = (product["product_id"], product["warehouse_id"])
        available = self.stock[key] - self.reserved[key]
        held = self.holds.get(product["product_id"], when) > when
        if available < quantity and held:
            raise ValueError("A supplier-held stockout must cancel before reservation")
        if available < quantity + 4 and not held:
            self.apply(when, product, "receiving", max(40, quantity * 12), 0, "product", key[0], "scheduled_replenishment")
        self.apply(when, product, "reservation", 0, quantity, "order_item", item_id, "checkout_reservation")

    def available(self, product):
        key = (product["product_id"], product["warehouse_id"])
        return self.stock[key] - self.reserved[key]

    def supplier_hold(self, when, product, release_time):
        """Move unreserved units out of sellable stock; existing orders keep their allocation."""
        pid = product["product_id"]
        if self.holds.get(pid, when) > when:
            return
        self.holds[pid] = release_time
        quantity = self.available(product)
        if quantity:
            self.apply(when, product, "adjustment", -quantity, 0, "product", pid, "supplier_hold_quarantine")
            self.schedule(release_time, product, "receiving", quantity, 0, "product", pid, "supplier_hold_released")

    def finish(self):
        self.advance(CUTOFF)
