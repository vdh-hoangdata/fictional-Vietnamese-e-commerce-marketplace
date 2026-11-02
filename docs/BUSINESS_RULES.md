# Simulation contract

## Relational grains and ownership

The schema registry in `src/models/schema.py` is authoritative and generates the
field dictionary, SQL DDL and Mermaid ERD. Business keys remain stable across
canonical snapshots, source extracts and CDC. The 23 requested tables plus
`shipment_items` normalize split shipment item/quantity assignments. Customers
have multiple addresses; products belong to one seller and leaf category.

## Financial invariants

All money is nonnegative integer VND; no floating point accounting is used.
`item_gmv = quantity * unit_price`, where unit_price is the catalog promotional
price if present, otherwise listed price, at the purchase instant. The immutable
captured selling price is not today's price. `line_discount` is a quantity offer.
`order_discount` is a coupon allocated proportionally across discounted lines by
the largest remainder method, with line position breaking ties.
`item_amount = item_gmv - line_discount - allocated_order_discount`.
`total_payable = SUM(item_amount) + shipping_fee`.
`orders.order_discount = SUM(order_discounts.discount_amount)`; that table is
an audit of the same header discount and must not be subtracted again.

Only payment status `captured` counts as collected cash. COD pending settlement
is not collected. Failed/retried/authorized attempts are not additive revenue.
At most one captured payment exists per order. A paid pre-dispatch cancellation
or complete delivery failure receives a full refund including shipping. Item
returns refund `floor(item_amount * returned_quantity / original_quantity)`;
there is at most one return per line, so cumulative rounding cannot over-refund.
Returned shipping is not refunded. Pending/rejected refunds collect zero.
Net collected cash = captures minus completed refunds. GMV, cash and accounting
revenue are separate. Seller payout, tax, platform revenue and contribution
profit are deliberately not modeled; product cost alone cannot establish profit.

## Chronology and lifecycles

Customers register before ordering. A customer can lapse after an inactive date.
Product availability is launch <= order < discontinued_at. Price intervals are
half-open [effective_from, effective_to), contiguous and non-overlapping.
Orders follow created -> confirmed -> processing -> shipped -> delivered or
delivery_failed. Created may terminate as payment_failed/payment_abandoned;
confirmed/processing may terminate as cancelled. Delivered and other terminal
states do not reopen; item returns are a separate workflow. Shipment delivery
failures are returned to origin. Status snapshots contain only events at cutoff.
Payment attempts begin pending, become authorized on provider acceptance, then
captured on collection; COD capture follows delivery. Reviews
require delivered purchases. Returns require delivery and available quantity.

## Inventory

`quantity_delta` changes physical on-hand inventory. `reserved_delta` changes
reserved inventory. Availability = on-hand minus reserved. Receiving and returned
restocking add physical stock, reservation adds reserved units, fulfillment
subtracts both, cancellation releases only reservations. A timestamp-ordered
queue applies future inventory effects before the next order. Low inventory
triggers receiving; some shortages cause explicit stockout cancellations.
Nonnegative on-hand, reserved and available balances hold at every event.
On-hand denotes sellable stock. Signed adjustments can quarantine unreserved
units during a supplier hold; release receiving entries restore them. Existing
reservations remain protected. Other adjustments are positive count corrections.

## Demand and inference limits

Weighted day sampling combines growth, weekends, payday, January/February
seasonal demand, recurring sale dates and campaign spend. Category weights vary
with season; popular items and customers are heavy-tailed. Marketing intensity
affects demand, acquisition channels and abandoned-session traffic. An outage
can reduce completed checkouts without removing failed orders. Attribution can
be missing or cross-device, and journeys can touch multiple campaigns.
Administrative labels are coarse historical reporting regions. The process is a
controlled synthetic scenario, not a fitted estimate of Vietnamese market shares.
