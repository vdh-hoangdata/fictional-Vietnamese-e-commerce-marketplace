TRANSITIONS = {
    None: {"created"}, "created": {"confirmed", "payment_failed", "payment_abandoned"},
    "confirmed": {"processing", "cancelled"}, "processing": {"shipped", "cancelled"},
    "shipped": {"delivered", "delivery_failed"},
}
TERMINAL = {"delivered", "delivery_failed", "cancelled", "payment_failed", "payment_abandoned"}


def allocate(amount, weights):
    """Integer largest-remainder allocation with stable line-position tie breaks."""
    total = sum(weights)
    if amount < 0 or amount > total:
        raise ValueError("Discount cannot exceed eligible merchandise")
    if not total:
        return [0] * len(weights)
    values = [amount * w // total for w in weights]
    order = sorted(range(len(weights)), key=lambda i: (-(amount * weights[i] % total), i))
    for i in order[:amount - sum(values)]:
        values[i] += 1
    return values


def returned_value(item_amount, quantity, returned_quantity):
    if not 0 < returned_quantity <= quantity:
        raise ValueError("Invalid return quantity")
    return item_amount * returned_quantity // quantity
