"""Single field-level contract used by writers, validators, docs and SQL DDL."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    name: str
    kind: str
    meaning: str
    nullable: bool = False
    foreign_key: str | None = None

    @property
    def sql_type(self):
        return {"id": "BIGINT", "int": "INT", "money": "BIGINT", "bool": "BIT",
                "text": "NVARCHAR(200)", "long": "NVARCHAR(1000)",
                "timestamp": "DATETIME2(0)", "date": "DATE", "json": "NVARCHAR(MAX)"}[self.kind]


@dataclass(frozen=True)
class Table:
    name: str
    source: str
    grain: str
    columns: tuple[Column, ...]

    @property
    def pk(self):
        return self.columns[0].name


TABLES = {}


def table(name, source, grain, definition):
    columns = []
    for line in definition.strip().splitlines():
        spec, meaning = line.strip().split(" | ", 1)
        tokens = spec.split()
        column, kind = tokens[:2]
        columns.append(Column(column, kind, meaning, "?" in tokens,
                              next((t[1:] for t in tokens[2:] if t.startswith("@")), None)))
    TABLES[name] = Table(name, source, grain, tuple(columns))


table("customers", "customer_crm", "one registered fictional customer", """
customer_id id | Stable customer business key
customer_name text | Synthetic Vietnamese-style full name
email text ? | Fictional contact at reserved example.invalid domain
phone text ? | Deliberately non-dialable synthetic phone token
registered_at timestamp | Account registration instant
inactive_at timestamp ? | Lapse instant after which no new orders are generated
status text | active or inactive at snapshot cutoff
acquisition_channel text | First observed acquisition channel, not causal credit
spending_segment text | budget, mainstream or premium preference
"""
)
table("customer_addresses", "customer_crm", "one saved customer address", """
address_id id | Stable address key
customer_id id @customers.customer_id | Owning customer
province text | Historical coarse Vietnamese reporting region
district text ? | Unknown administrative subdivision; intentionally null
address_line text | Explicitly fictional street and building token
postal_code text ? | Unknown postal information; intentionally null
is_default bool | Exactly one default address per customer
"""
)
table("sellers", "product_catalog", "one fictional merchant", """
seller_id id | Stable merchant key
seller_name text | Fictional merchant display name
seller_type text | independent or company_operated
registered_at timestamp | Marketplace onboarding instant
province text | Seller reporting region
status text | active at the observation cutoff
warehouse_id id @warehouses.warehouse_id | Primary fulfillment warehouse
"""
)
table("categories", "product_catalog", "one taxonomy node", """
category_id id | Stable taxonomy key
category_name text | Display name of department or leaf category
parent_category_id id ? @categories.category_id | Parent taxonomy node; null for root
category_level int | 1 for department, 2 for leaf
"""
)
table("products", "product_catalog", "one seller-owned SKU", """
product_id id | Stable product key
seller_id id @sellers.seller_id | Merchant owning the SKU
category_id id @categories.category_id | Leaf taxonomy assignment
brand text | Synthetic product brand
product_name text | Synthetic product description and model
unit_cost money | Synthetic unit procurement cost in VND; excludes platform overhead
attributes json | JSON color, size and model attributes
launched_at timestamp | First availability instant
discontinued_at timestamp ? | Exclusive end of availability
is_active bool | Whether available at observation cutoff
"""
)
table("product_price_history", "product_catalog", "one non-overlapping SKU price interval", """
price_history_id id | Price interval key
product_id id @products.product_id | SKU whose historical price is defined
effective_from timestamp | Inclusive validity start
effective_to timestamp | Exclusive validity end, possibly beyond observation cutoff
listed_price money | Listed unit price in VND
promotional_price money ? | Promotional price when lower than listed price
change_reason text | launch, repricing or seasonal_offer
"""
)
table("orders", "ecommerce_app", "one placed order including unsuccessful checkout", """
order_id id | Stable order key
customer_id id @customers.customer_id | Registered purchaser
address_id id @customer_addresses.address_id | Delivery address belonging to purchaser
ordered_at timestamp | Order placement instant
sales_channel text | website, android or ios
status text | Latest order lifecycle state at cutoff
currency text | VND
item_gmv money | Sum of quantity times captured unit price before discounts
line_discount money | Sum of quantity-level line discounts
order_discount money | Coupon discount allocated to items; do not subtract twice
shipping_fee money | Sum of quoted shipment fees, also retained on cancelled orders
total_payable money | Item GMV less both discount classes plus shipping
campaign_id id ? @marketing_campaigns.campaign_id | Last observed campaign touch; nullable and not causal
"""
)
table("order_items", "ecommerce_app", "one SKU line within an order", """
order_item_id id | Stable line key
order_id id @orders.order_id | Parent order
product_id id @products.product_id | Purchased SKU
seller_id id @sellers.seller_id | Seller captured at purchase
quantity int | Purchased units, positive integer
unit_price money | Actual historical selling price before line/coupon discounts
item_gmv money | Quantity times unit price
line_discount money | Quantity offer discount
allocated_order_discount money | Share of header coupon using largest remainders
item_amount money | Net merchandise line value after all discounts
"""
)
table("order_status_history", "ecommerce_app", "one real order state transition", """
status_event_id id | Stable transition key
order_id id @orders.order_id | Order affected
previous_status text ? | Prior state; null for creation
new_status text | Resulting lifecycle state
event_at timestamp | Business transition instant
source_system text | System producing the state transition
change_reason text | Business explanation for state change
"""
)
table("coupons", "ecommerce_app", "one promotion eligibility contract", """
coupon_id id | Stable coupon key
campaign_id id ? @marketing_campaigns.campaign_id | Associated campaign
coupon_code text | Synthetic promotional token
discount_type text | percent
discount_value int | Integer percentage of eligible merchandise
minimum_spend money | Minimum merchandise after line discounts
maximum_discount money | Discount cap per order
category_id id ? @categories.category_id | Eligible department; null means all departments
starts_at timestamp | Inclusive redemption window start
ends_at timestamp | Exclusive redemption window end
redemption_limit int | Total permitted redemptions across customers
"""
)
table("order_discounts", "ecommerce_app", "one applied header promotion", """
order_discount_id id | Stable application key
order_id id @orders.order_id | Discounted order
coupon_id id @coupons.coupon_id | Applied coupon
allocation_method text | largest_remainder across all eligible net lines
discount_amount money | Header discount, already included in allocated line discounts
"""
)
table("payments", "payment_gateway", "one payment attempt rather than one order", """
payment_id id | Stable payment attempt key
order_id id @orders.order_id | Related order
provider text | Synthetic payment service or COD carrier clearing
method text | cod, bank_transfer, card or ewallet
attempt_number int | Sequential attempt count within an order
status text | pending, failed, cancelled, authorized, pending_settlement or captured
attempted_at timestamp | Payment attempt start
authorized_at timestamp ? | Authorization instant for non-COD successful attempts
captured_at timestamp ? | Actual collected cash instant
amount money | Attempted amount; recognized only when captured
failure_code text ? | Provider or user-abandonment failure reason
"""
)
table("refunds", "payment_gateway", "one refund request against a captured payment", """
refund_id id | Stable refund request key
payment_id id @payments.payment_id | Original captured payment
order_id id @orders.order_id | Original order
return_id id ? @returns.return_id | Item return, null for cancellation/non-delivery refund
requested_amount money | Amount requested in VND
refunded_amount money | Actual refund; zero for pending/rejected requests
status text | completed or pending
requested_at timestamp | Request instant
refunded_at timestamp ? | Completion instant
"""
)
table("warehouses", "warehouse_erp", "one synthetic fulfillment node", """
warehouse_id id | Stable fulfillment node key
warehouse_name text | Synthetic warehouse label
province text | Coarse location
warehouse_type text | regional or central
status text | operational
"""
)
table("inventory_movements", "warehouse_erp", "one physical or reservation ledger entry", """
movement_id id | Stable ledger entry key, also same-second ordering tie breaker
product_id id @products.product_id | Affected SKU
warehouse_id id @warehouses.warehouse_id | Holding warehouse
movement_type text | receiving, reservation, fulfillment, cancellation_release, return_restock or adjustment
quantity_delta int | Signed change in physical on-hand units
reserved_delta int | Signed change in reserved units
reference_type text | product, order_item or return, defining polymorphic reference
reference_id id | Key in the relation named by reference_type
event_at timestamp | Business inventory instant
reason text | Operational explanation
"""
)
table("shipments", "logistics_provider", "one seller/warehouse parcel in an order", """
shipment_id id | Stable parcel key
order_id id @orders.order_id | Parent order; may contain multiple parcels
seller_id id @sellers.seller_id | Fulfilling seller
warehouse_id id @warehouses.warehouse_id | Dispatch node
delivery_partner text | Synthetic carrier
shipping_fee money | Quoted parcel fee in VND
status text | ready, shipped, delivered or returned_to_sender at cutoff
created_at timestamp | Parcel created after confirmation
shipped_at timestamp ? | Carrier handover instant
expected_delivery_at timestamp | Promised delivery deadline
delivered_at timestamp ? | Successful delivery instant
closed_at timestamp ? | Delivered or returned-to-sender completion
sla_days int | Quoted days from dispatch to promised delivery
"""
)
table("shipment_items", "logistics_provider", "one item assignment to a parcel", """
shipment_item_id id | Stable parcel-line assignment key
shipment_id id @shipments.shipment_id | Parcel
order_item_id id @order_items.order_item_id | Order line
quantity int | Assigned units; equals purchased quantity for this simulation
"""
)
table("shipment_events", "logistics_provider", "one sequenced tracking observation", """
shipment_event_id id | Stable tracking observation key
shipment_id id @shipments.shipment_id | Parcel observed
event_at timestamp | Actual tracking instant
event_type text | ready, shipped, in_transit, delivery_attempt_failed, delivered or returned_to_sender
event_location text | Coarse synthetic hub or delivery region
event_sequence int | Strictly increasing sequence within parcel
"""
)
table("returns", "ecommerce_app", "one partial or complete item-line return request", """
return_id id | Stable item return key
order_id id @orders.order_id | Purchase order
order_item_id id @order_items.order_item_id | Returned line
requested_quantity int | Units requested, no more than purchased quantity
reason text | quality, size_fit or changed_mind
requested_at timestamp | Customer request after delivery
received_at timestamp ? | Warehouse acceptance instant
status text | received, requested or rejected
outcome text | refund_and_restock, awaiting_inspection or rejected
"""
)
table("marketing_campaigns", "marketing_platform", "one bounded advertising flight", """
campaign_id id | Stable advertising flight key
campaign_name text | Synthetic flight name
objective text | acquisition or promotion
channel text | social, search or affiliate
starts_at timestamp | Inclusive campaign start
ends_at timestamp | Exclusive campaign end
budget money | Planned spend cap in VND
"""
)
table("marketing_spend_daily", "marketing_platform", "one campaign/local reporting day", """
spend_id id | Stable daily spend key
campaign_id id @marketing_campaigns.campaign_id | Advertising flight
spend_date date | Vietnam local calendar date
channel text | Channel inherited from campaign
spend_amount money | Advertising spend in VND
impressions int | Synthetic impressions, greater than or equal to clicks
clicks int | Observable paid click count, not all instrumented sessions
"""
)
table("web_events", "web_analytics", "one instrumented behavioral event", """
event_id id | Stable event key
anonymous_visitor_id text | Device-scoped synthetic browser identity, not a person key
session_id text | Session identifier
customer_id id ? @customers.customer_id | Authenticated customer if known
event_type text | page_view, product_view, search, add_to_cart, remove_from_cart, checkout_started, payment_started or purchase
event_at timestamp | Business event instant
product_id id ? @products.product_id | Viewed or cart SKU when relevant
device_type text | desktop, android or ios
traffic_source text | direct, organic, social, search or affiliate
campaign_id id ? @marketing_campaigns.campaign_id | Observed campaign touch, often missing
properties json | Nested context; purchase.order_id joins an actual order
"""
)
table("reviews", "customer_support", "one verified purchase line review", """
review_id id | Stable review key
customer_id id @customers.customer_id | Purchaser submitting review
product_id id @products.product_id | Purchased SKU
order_item_id id @order_items.order_item_id | Delivered purchase line
rating int | Integer 1 through 5
reviewed_at timestamp | Submission after delivery
review_text text ? | Synthetic templated review, not scraped content
"""
)
table("support_tickets", "customer_support", "one customer service case", """
ticket_id id | Stable service case key
customer_id id @customers.customer_id | Requesting customer
order_id id ? @orders.order_id | Related order; null for account enquiries
issue_category text | delivery_delay, payment_failure, refund_status, product_quality or account
priority text | normal or high
created_at timestamp | Case opened
first_response_at timestamp ? | First human response, possibly not yet observed
resolved_at timestamp ? | Resolution, possibly not yet observed
status text | open, in_progress or resolved
"""
)

NUMERIC_KINDS = {"id", "int", "money", "bool"}
