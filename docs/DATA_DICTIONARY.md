# Data dictionary

Generated from `src/models/schema.py`. All IDs are positive integer business keys.
Money uses integer VND, with zero allowed. Timestamp fields are UTC ISO-8601 at second precision;
dates explicitly called reporting dates use Vietnam local time. Empty CSV fields mean SQL NULL.
JSON properties remain nested in JSONL and are JSON text in CSV/SQL. Source metadata is described below.

## customers

Grain: one registered fictional customer. Source: `customer_crm`. Primary key: `customer_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| customer_id | BIGINT | no | PK | Stable customer business key; required | `1` | — |
| customer_name | NVARCHAR(200) | no | — | Synthetic Vietnamese-style full name; required | `Pham Dung MoPhong-000001` | — |
| email | NVARCHAR(200) | yes | — | Fictional contact at reserved example.invalid domain; NULL is permitted | `kh0000001@example.invalid` | — |
| phone | NVARCHAR(200) | yes | — | Deliberately non-dialable synthetic phone token; NULL is permitted | `SYNTHETIC-PHONE-0000001` | — |
| registered_at | DATETIME2(0) | no | — | Account registration instant; required | `2023-12-10T17:00:00Z` | UTC |
| inactive_at | DATETIME2(0) | yes | — | Lapse instant after which no new orders are generated; NULL is permitted | `NULL` | UTC |
| status | NVARCHAR(200) | no | — | active or inactive at snapshot cutoff; required | `active` | — |
| acquisition_channel | NVARCHAR(200) | no | — | First observed acquisition channel, not causal credit; required | `direct` | — |
| spending_segment | NVARCHAR(200) | no | — | budget, mainstream or premium preference; required | `budget` | — |

## customer_addresses

Grain: one saved customer address. Source: `customer_crm`. Primary key: `address_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| address_id | BIGINT | no | PK | Stable address key; required | `1` | — |
| customer_id | BIGINT | no | FK customers.customer_id | Owning customer; required | `1` | — |
| province | NVARCHAR(200) | no | — | Historical coarse Vietnamese reporting region; required | `Ho Chi Minh City` | — |
| district | NVARCHAR(200) | yes | — | Unknown administrative subdivision; intentionally null; NULL is permitted | `NULL` | — |
| address_line | NVARCHAR(200) | no | — | Explicitly fictional street and building token; required | `Dia chi gia lap VC-000001-0; Pho Mo Phong` | — |
| postal_code | NVARCHAR(200) | yes | — | Unknown postal information; intentionally null; NULL is permitted | `NULL` | — |
| is_default | BIT | no | — | Exactly one default address per customer; required | `1` | — |

## sellers

Grain: one fictional merchant. Source: `product_catalog`. Primary key: `seller_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| seller_id | BIGINT | no | PK | Stable merchant key; required | `1` | — |
| seller_name | NVARCHAR(200) | no | — | Fictional merchant display name; required | `Cua hang Mo Phong 00001` | — |
| seller_type | NVARCHAR(200) | no | — | independent or company_operated; required | `independent` | — |
| registered_at | DATETIME2(0) | no | — | Marketplace onboarding instant; required | `2022-11-25T17:00:00Z` | UTC |
| province | NVARCHAR(200) | no | — | Seller reporting region; required | `Ha Noi` | — |
| status | NVARCHAR(200) | no | — | active at the observation cutoff; required | `active` | — |
| warehouse_id | BIGINT | no | FK warehouses.warehouse_id | Primary fulfillment warehouse; required | `1` | — |

## categories

Grain: one taxonomy node. Source: `product_catalog`. Primary key: `category_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| category_id | BIGINT | no | PK | Stable taxonomy key; required | `1` | — |
| category_name | NVARCHAR(200) | no | — | Display name of department or leaf category; required | `Electronics` | — |
| parent_category_id | BIGINT | yes | FK categories.category_id | Parent taxonomy node; null for root; NULL is permitted | `NULL` | — |
| category_level | INT | no | — | 1 for department, 2 for leaf; required | `1` | — |

## products

Grain: one seller-owned SKU. Source: `product_catalog`. Primary key: `product_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| product_id | BIGINT | no | PK | Stable product key; required | `1` | — |
| seller_id | BIGINT | no | FK sellers.seller_id | Merchant owning the SKU; required | `6` | — |
| category_id | BIGINT | no | FK categories.category_id | Leaf taxonomy assignment; required | `101` | — |
| brand | NVARCHAR(200) | no | — | Synthetic product brand; required | `MoPhong1` | — |
| product_name | NVARCHAR(200) | no | — | Synthetic product description and model; required | `Phones VC-00001` | — |
| unit_cost | BIGINT | no | — | Synthetic unit procurement cost in VND; excludes platform overhead; required | `1974700` | VND |
| attributes | NVARCHAR(MAX) | no | — | JSON color, size and model attributes; required | `{"color":"white","model":"S1","size":"L"}` | — |
| launched_at | DATETIME2(0) | no | — | First availability instant; required | `2023-07-31T17:00:00Z` | UTC |
| discontinued_at | DATETIME2(0) | yes | — | Exclusive end of availability; NULL is permitted | `NULL` | UTC |
| is_active | BIT | no | — | Whether available at observation cutoff; required | `1` | — |

## product_price_history

Grain: one non-overlapping SKU price interval. Source: `product_catalog`. Primary key: `price_history_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| price_history_id | BIGINT | no | PK | Price interval key; required | `1` | — |
| product_id | BIGINT | no | FK products.product_id | SKU whose historical price is defined; required | `1` | — |
| effective_from | DATETIME2(0) | no | — | Inclusive validity start; required | `2023-07-31T17:00:00Z` | UTC |
| effective_to | DATETIME2(0) | no | — | Exclusive validity end, possibly beyond observation cutoff; required | `2024-06-28T17:00:00Z` | UTC |
| listed_price | BIGINT | no | — | Listed unit price in VND; required | `2821000` | VND |
| promotional_price | BIGINT | yes | — | Promotional price when lower than listed price; NULL is permitted | `NULL` | VND |
| change_reason | NVARCHAR(200) | no | — | launch, repricing or seasonal_offer; required | `launch` | — |

## orders

Grain: one placed order including unsuccessful checkout. Source: `ecommerce_app`. Primary key: `order_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| order_id | BIGINT | no | PK | Stable order key; required | `1` | — |
| customer_id | BIGINT | no | FK customers.customer_id | Registered purchaser; required | `815` | — |
| address_id | BIGINT | no | FK customer_addresses.address_id | Delivery address belonging to purchaser; required | `1024` | — |
| ordered_at | DATETIME2(0) | no | — | Order placement instant; required | `2023-12-31T21:27:39Z` | UTC |
| sales_channel | NVARCHAR(200) | no | — | website, android or ios; required | `android` | — |
| status | NVARCHAR(200) | no | — | Latest order lifecycle state at cutoff; required | `delivered` | — |
| currency | NVARCHAR(200) | no | — | VND; required | `VND` | — |
| item_gmv | BIGINT | no | — | Sum of quantity times captured unit price before discounts; required | `1621000` | VND |
| line_discount | BIGINT | no | — | Sum of quantity-level line discounts; required | `0` | VND |
| order_discount | BIGINT | no | — | Coupon discount allocated to items; do not subtract twice; required | `0` | VND |
| shipping_fee | BIGINT | no | — | Sum of quoted shipment fees, also retained on cancelled orders; required | `32000` | VND |
| total_payable | BIGINT | no | — | Item GMV less both discount classes plus shipping; required | `1653000` | VND |
| campaign_id | BIGINT | yes | FK marketing_campaigns.campaign_id | Last observed campaign touch; nullable and not causal; NULL is permitted | `NULL` | — |

## order_items

Grain: one SKU line within an order. Source: `ecommerce_app`. Primary key: `order_item_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| order_item_id | BIGINT | no | PK | Stable line key; required | `1` | — |
| order_id | BIGINT | no | FK orders.order_id | Parent order; required | `1` | — |
| product_id | BIGINT | no | FK products.product_id | Purchased SKU; required | `94` | — |
| seller_id | BIGINT | no | FK sellers.seller_id | Seller captured at purchase; required | `8` | — |
| quantity | INT | no | — | Purchased units, positive integer; required | `1` | units |
| unit_price | BIGINT | no | — | Actual historical selling price before line/coupon discounts; required | `1621000` | VND |
| item_gmv | BIGINT | no | — | Quantity times unit price; required | `1621000` | VND |
| line_discount | BIGINT | no | — | Quantity offer discount; required | `0` | VND |
| allocated_order_discount | BIGINT | no | — | Share of header coupon using largest remainders; required | `0` | VND |
| item_amount | BIGINT | no | — | Net merchandise line value after all discounts; required | `1621000` | VND |

## order_status_history

Grain: one real order state transition. Source: `ecommerce_app`. Primary key: `status_event_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| status_event_id | BIGINT | no | PK | Stable transition key; required | `1` | — |
| order_id | BIGINT | no | FK orders.order_id | Order affected; required | `1` | — |
| previous_status | NVARCHAR(200) | yes | — | Prior state; null for creation; NULL is permitted | `NULL` | — |
| new_status | NVARCHAR(200) | no | — | Resulting lifecycle state; required | `created` | — |
| event_at | DATETIME2(0) | no | — | Business transition instant; required | `2023-12-31T21:27:39Z` | UTC |
| source_system | NVARCHAR(200) | no | — | System producing the state transition; required | `ecommerce_app` | — |
| change_reason | NVARCHAR(200) | no | — | Business explanation for state change; required | `checkout_submitted` | — |

## coupons

Grain: one promotion eligibility contract. Source: `ecommerce_app`. Primary key: `coupon_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| coupon_id | BIGINT | no | PK | Stable coupon key; required | `1` | — |
| campaign_id | BIGINT | yes | FK marketing_campaigns.campaign_id | Associated campaign; NULL is permitted | `1` | — |
| coupon_code | NVARCHAR(200) | no | — | Synthetic promotional token; required | `VC2024011` | — |
| discount_type | NVARCHAR(200) | no | — | percent; required | `percent` | — |
| discount_value | INT | no | — | Integer percentage of eligible merchandise; required | `7` | — |
| minimum_spend | BIGINT | no | — | Minimum merchandise after line discounts; required | `150000` | VND |
| maximum_discount | BIGINT | no | — | Discount cap per order; required | `200000` | VND |
| category_id | BIGINT | yes | FK categories.category_id | Eligible department; null means all departments; NULL is permitted | `NULL` | — |
| starts_at | DATETIME2(0) | no | — | Inclusive redemption window start; required | `2023-12-31T17:00:00Z` | UTC |
| ends_at | DATETIME2(0) | no | — | Exclusive redemption window end; required | `2024-01-31T17:00:00Z` | UTC |
| redemption_limit | INT | no | — | Total permitted redemptions across customers; required | `500` | — |

## order_discounts

Grain: one applied header promotion. Source: `ecommerce_app`. Primary key: `order_discount_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| order_discount_id | BIGINT | no | PK | Stable application key; required | `1` | — |
| order_id | BIGINT | no | FK orders.order_id | Discounted order; required | `9` | — |
| coupon_id | BIGINT | no | FK coupons.coupon_id | Applied coupon; required | `1` | — |
| allocation_method | NVARCHAR(200) | no | — | largest_remainder across all eligible net lines; required | `largest_remainder` | — |
| discount_amount | BIGINT | no | — | Header discount, already included in allocated line discounts; required | `200000` | VND |

## payments

Grain: one payment attempt rather than one order. Source: `payment_gateway`. Primary key: `payment_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| payment_id | BIGINT | no | PK | Stable payment attempt key; required | `1` | — |
| order_id | BIGINT | no | FK orders.order_id | Related order; required | `1` | — |
| provider | NVARCHAR(200) | no | — | Synthetic payment service or COD carrier clearing; required | `PayLotus` | — |
| method | NVARCHAR(200) | no | — | cod, bank_transfer, card or ewallet; required | `ewallet` | — |
| attempt_number | INT | no | — | Sequential attempt count within an order; required | `1` | — |
| status | NVARCHAR(200) | no | — | pending, failed, cancelled, authorized, pending_settlement or captured; required | `captured` | — |
| attempted_at | DATETIME2(0) | no | — | Payment attempt start; required | `2023-12-31T21:28:09Z` | UTC |
| authorized_at | DATETIME2(0) | yes | — | Authorization instant for non-COD successful attempts; NULL is permitted | `2023-12-31T21:28:29Z` | UTC |
| captured_at | DATETIME2(0) | yes | — | Actual collected cash instant; NULL is permitted | `2023-12-31T21:29:39Z` | UTC |
| amount | BIGINT | no | — | Attempted amount; recognized only when captured; required | `1653000` | VND |
| failure_code | NVARCHAR(200) | yes | — | Provider or user-abandonment failure reason; NULL is permitted | `NULL` | — |

## refunds

Grain: one refund request against a captured payment. Source: `payment_gateway`. Primary key: `refund_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| refund_id | BIGINT | no | PK | Stable refund request key; required | `1` | — |
| payment_id | BIGINT | no | FK payments.payment_id | Original captured payment; required | `2` | — |
| order_id | BIGINT | no | FK orders.order_id | Original order; required | `2` | — |
| return_id | BIGINT | yes | FK returns.return_id | Item return, null for cancellation/non-delivery refund; NULL is permitted | `1` | — |
| requested_amount | BIGINT | no | — | Amount requested in VND; required | `477000` | VND |
| refunded_amount | BIGINT | no | — | Actual refund; zero for pending/rejected requests; required | `477000` | VND |
| status | NVARCHAR(200) | no | — | completed or pending; required | `completed` | — |
| requested_at | DATETIME2(0) | no | — | Request instant; required | `2024-01-19T01:08:58Z` | UTC |
| refunded_at | DATETIME2(0) | yes | — | Completion instant; NULL is permitted | `2024-01-24T01:08:58Z` | UTC |

## warehouses

Grain: one synthetic fulfillment node. Source: `warehouse_erp`. Primary key: `warehouse_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| warehouse_id | BIGINT | no | PK | Stable fulfillment node key; required | `1` | — |
| warehouse_name | NVARCHAR(200) | no | — | Synthetic warehouse label; required | `VC Synthetic Hub 1` | — |
| province | NVARCHAR(200) | no | — | Coarse location; required | `Ha Noi` | — |
| warehouse_type | NVARCHAR(200) | no | — | regional or central; required | `central` | — |
| status | NVARCHAR(200) | no | — | operational; required | `operational` | — |

## inventory_movements

Grain: one physical or reservation ledger entry. Source: `warehouse_erp`. Primary key: `movement_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| movement_id | BIGINT | no | PK | Stable ledger entry key, also same-second ordering tie breaker; required | `1` | — |
| product_id | BIGINT | no | FK products.product_id | Affected SKU; required | `135` | — |
| warehouse_id | BIGINT | no | FK warehouses.warehouse_id | Holding warehouse; required | `1` | — |
| movement_type | NVARCHAR(200) | no | — | receiving, reservation, fulfillment, cancellation_release, return_restock or adjustment; required | `receiving` | — |
| quantity_delta | INT | no | — | Signed change in physical on-hand units; required | `60` | units |
| reserved_delta | INT | no | — | Signed change in reserved units; required | `0` | units |
| reference_type | NVARCHAR(200) | no | — | product, order_item or return, defining polymorphic reference; required | `product` | — |
| reference_id | BIGINT | no | — | Key in the relation named by reference_type; required | `135` | — |
| event_at | DATETIME2(0) | no | — | Business inventory instant; required | `2023-07-04T16:59:59Z` | UTC |
| reason | NVARCHAR(200) | no | — | Operational explanation; required | `opening_or_launch_stock` | — |

## shipments

Grain: one seller/warehouse parcel in an order. Source: `logistics_provider`. Primary key: `shipment_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| shipment_id | BIGINT | no | PK | Stable parcel key; required | `1` | — |
| order_id | BIGINT | no | FK orders.order_id | Parent order; may contain multiple parcels; required | `1` | — |
| seller_id | BIGINT | no | FK sellers.seller_id | Fulfilling seller; required | `8` | — |
| warehouse_id | BIGINT | no | FK warehouses.warehouse_id | Dispatch node; required | `2` | — |
| delivery_partner | NVARCHAR(200) | no | — | Synthetic carrier; required | `MekongParcel` | — |
| shipping_fee | BIGINT | no | — | Quoted parcel fee in VND; required | `32000` | VND |
| status | NVARCHAR(200) | no | — | ready, shipped, delivered or returned_to_sender at cutoff; required | `delivered` | — |
| created_at | DATETIME2(0) | no | — | Parcel created after confirmation; required | `2023-12-31T22:00:39Z` | UTC |
| shipped_at | DATETIME2(0) | yes | — | Carrier handover instant; NULL is permitted | `2024-01-01T04:00:39Z` | UTC |
| expected_delivery_at | DATETIME2(0) | no | — | Promised delivery deadline; required | `2024-01-05T04:00:39Z` | UTC |
| delivered_at | DATETIME2(0) | yes | — | Successful delivery instant; NULL is permitted | `2024-01-04T22:00:39Z` | UTC |
| closed_at | DATETIME2(0) | yes | — | Delivered or returned-to-sender completion; NULL is permitted | `2024-01-04T22:00:39Z` | UTC |
| sla_days | INT | no | — | Quoted days from dispatch to promised delivery; required | `4` | — |

## shipment_items

Grain: one item assignment to a parcel. Source: `logistics_provider`. Primary key: `shipment_item_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| shipment_item_id | BIGINT | no | PK | Stable parcel-line assignment key; required | `1` | — |
| shipment_id | BIGINT | no | FK shipments.shipment_id | Parcel; required | `1` | — |
| order_item_id | BIGINT | no | FK order_items.order_item_id | Order line; required | `1` | — |
| quantity | INT | no | — | Assigned units; equals purchased quantity for this simulation; required | `1` | units |

## shipment_events

Grain: one sequenced tracking observation. Source: `logistics_provider`. Primary key: `shipment_event_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| shipment_event_id | BIGINT | no | PK | Stable tracking observation key; required | `1` | — |
| shipment_id | BIGINT | no | FK shipments.shipment_id | Parcel observed; required | `1` | — |
| event_at | DATETIME2(0) | no | — | Actual tracking instant; required | `2023-12-31T22:00:39Z` | UTC |
| event_type | NVARCHAR(200) | no | — | ready, shipped, in_transit, delivery_attempt_failed, delivered or returned_to_sender; required | `ready` | — |
| event_location | NVARCHAR(200) | no | — | Coarse synthetic hub or delivery region; required | `Ho Chi Minh City` | — |
| event_sequence | INT | no | — | Strictly increasing sequence within parcel; required | `1` | — |

## returns

Grain: one partial or complete item-line return request. Source: `ecommerce_app`. Primary key: `return_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| return_id | BIGINT | no | PK | Stable item return key; required | `1` | — |
| order_id | BIGINT | no | FK orders.order_id | Purchase order; required | `2` | — |
| order_item_id | BIGINT | no | FK order_items.order_item_id | Returned line; required | `2` | — |
| requested_quantity | INT | no | — | Units requested, no more than purchased quantity; required | `1` | units |
| reason | NVARCHAR(200) | no | — | quality, size_fit or changed_mind; required | `changed_mind` | — |
| requested_at | DATETIME2(0) | no | — | Customer request after delivery; required | `2024-01-14T01:08:58Z` | UTC |
| received_at | DATETIME2(0) | yes | — | Warehouse acceptance instant; NULL is permitted | `2024-01-19T01:08:58Z` | UTC |
| status | NVARCHAR(200) | no | — | received, requested or rejected; required | `received` | — |
| outcome | NVARCHAR(200) | no | — | refund_and_restock, awaiting_inspection or rejected; required | `refund_and_restock` | — |

## marketing_campaigns

Grain: one bounded advertising flight. Source: `marketing_platform`. Primary key: `campaign_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| campaign_id | BIGINT | no | PK | Stable advertising flight key; required | `1` | — |
| campaign_name | NVARCHAR(200) | no | — | Synthetic flight name; required | `VietCommerce 2024-01 Discovery` | — |
| objective | NVARCHAR(200) | no | — | acquisition or promotion; required | `acquisition` | — |
| channel | NVARCHAR(200) | no | — | social, search or affiliate; required | `social` | — |
| starts_at | DATETIME2(0) | no | — | Inclusive campaign start; required | `2023-12-31T17:00:00Z` | UTC |
| ends_at | DATETIME2(0) | no | — | Exclusive campaign end; required | `2024-01-31T17:00:00Z` | UTC |
| budget | BIGINT | no | — | Planned spend cap in VND; required | `2553142` | VND |

## marketing_spend_daily

Grain: one campaign/local reporting day. Source: `marketing_platform`. Primary key: `spend_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| spend_id | BIGINT | no | PK | Stable daily spend key; required | `1` | — |
| campaign_id | BIGINT | no | FK marketing_campaigns.campaign_id | Advertising flight; required | `1` | — |
| spend_date | DATE | no | — | Vietnam local calendar date; required | `2024-01-01` | VN date |
| channel | NVARCHAR(200) | no | — | Channel inherited from campaign; required | `social` | — |
| spend_amount | BIGINT | no | — | Advertising spend in VND; required | `74770` | VND |
| impressions | INT | no | — | Synthetic impressions, greater than or equal to clicks; required | `6230` | — |
| clicks | INT | no | — | Observable paid click count, not all instrumented sessions; required | `115` | — |

## web_events

Grain: one instrumented behavioral event. Source: `web_analytics`. Primary key: `event_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| event_id | BIGINT | no | PK | Stable event key; required | `1` | — |
| anonymous_visitor_id | NVARCHAR(200) | no | — | Device-scoped synthetic browser identity, not a person key; required | `device-00000815-1` | — |
| session_id | NVARCHAR(200) | no | — | Session identifier; required | `session-0000000001` | — |
| customer_id | BIGINT | yes | FK customers.customer_id | Authenticated customer if known; NULL is permitted | `815` | — |
| event_type | NVARCHAR(200) | no | — | page_view, product_view, search, add_to_cart, remove_from_cart, checkout_started, payment_started or purchase; required | `page_view` | — |
| event_at | DATETIME2(0) | no | — | Business event instant; required | `2023-12-31T21:23:39Z` | UTC |
| product_id | BIGINT | yes | FK products.product_id | Viewed or cart SKU when relevant; NULL is permitted | `NULL` | — |
| device_type | NVARCHAR(200) | no | — | desktop, android or ios; required | `android` | — |
| traffic_source | NVARCHAR(200) | no | — | direct, organic, social, search or affiliate; required | `organic` | — |
| campaign_id | BIGINT | yes | FK marketing_campaigns.campaign_id | Observed campaign touch, often missing; NULL is permitted | `1` | — |
| properties | NVARCHAR(MAX) | no | — | Nested context; purchase.order_id joins an actual order; required | `{"context":{"currency":"VND","locale":"vi-VN"},"page":{"path":"/browse"}}` | — |

## reviews

Grain: one verified purchase line review. Source: `customer_support`. Primary key: `review_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| review_id | BIGINT | no | PK | Stable review key; required | `1` | — |
| customer_id | BIGINT | no | FK customers.customer_id | Purchaser submitting review; required | `955` | — |
| product_id | BIGINT | no | FK products.product_id | Purchased SKU; required | `111` | — |
| order_item_id | BIGINT | no | FK order_items.order_item_id | Delivered purchase line; required | `16` | — |
| rating | INT | no | — | Integer 1 through 5; required | `5` | — |
| reviewed_at | DATETIME2(0) | no | — | Submission after delivery; required | `2024-01-15T20:09:49Z` | UTC |
| review_text | NVARCHAR(200) | yes | — | Synthetic templated review, not scraped content; NULL is permitted | `Danh gia gia lap: hai long` | — |

## support_tickets

Grain: one customer service case. Source: `customer_support`. Primary key: `ticket_id`.

| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |
|---|---|---|---|---|---|---|
| ticket_id | BIGINT | no | PK | Stable service case key; required | `1` | — |
| customer_id | BIGINT | no | FK customers.customer_id | Requesting customer; required | `1302` | — |
| order_id | BIGINT | yes | FK orders.order_id | Related order; null for account enquiries; NULL is permitted | `2` | — |
| issue_category | NVARCHAR(200) | no | — | delivery_delay, payment_failure, refund_status, product_quality or account; required | `product_quality` | — |
| priority | NVARCHAR(200) | no | — | normal or high; required | `normal` | — |
| created_at | DATETIME2(0) | no | — | Case opened; required | `2024-01-14T01:08:58Z` | UTC |
| first_response_at | DATETIME2(0) | yes | — | First human response, possibly not yet observed; NULL is permitted | `2024-01-14T11:08:58Z` | UTC |
| resolved_at | DATETIME2(0) | yes | — | Resolution, possibly not yet observed; NULL is permitted | `2024-01-14T15:08:58Z` | UTC |
| status | NVARCHAR(200) | no | — | open, in_progress or resolved; required | `resolved` | — |

## Source envelope

Every raw record also carries `_ingested_at` (UTC ingestion timestamp), `_batch_id` (source extraction identifier),
and `_source_version` (integer record revision, 1 initially, 2 for a corrected snapshot).
These fields are transport metadata, not business keys. Staging permits duplicate business keys.
A correction outranks the original by source version; duplicate transport records can repeat the same version.
Different null encodings are not injected; all CSV sources consistently use an empty field.

| Column (all raw tables) | Type | Nullable | Meaning / constraint | Example | Unit | Key | Source |
|---|---|---|---|---|---|---|---|
| _ingested_at | DATETIME2(0) | no | Transport receipt; can follow the business cutoff | 2026-01-01T02:00:00Z | UTC | none | owning system |
| _batch_id | NVARCHAR(200) | no | Extraction identifier; not a business-event date | ecommerce_app:20260101:00001 | none | none | owning system |
| _source_version | INT | no | Positive snapshot revision; highest version wins | 1 | revision | part of revision identity | owning system |

## Nested JSON contract

Product attributes have required synthetic string keys model, color and size; examples are S1, blue and M.
The web_analytics properties object has the following conditional fields. Fields not applicable to an event are absent, not zero.

| Path within properties | Type | Presence | Meaning / constraint | Example | Unit / key |
|---|---|---|---|---|---|
| page.path | string | every event | Synthetic navigation path | /checkout | none |
| context.locale | string | every event | vi-VN locale | vi-VN | none |
| context.currency | string | every event | Reporting currency | VND | currency |
| query | string | search | Synthetic search phrase | ao | none |
| quantity | integer | add_to_cart/remove_from_cart | Instrumented cart units, positive | 1 | units |
| order_id | BIGINT | purchase | Required real order reference; event customer must match | 1 | FK orders.order_id |
| value_vnd | BIGINT | purchase | Order total payable, including shipping | 300000 | VND |
| instrumentation_latency_ms | string numeric | optional raw anomaly | Illustrative inconsistent numeric encoding | 125 | milliseconds |
