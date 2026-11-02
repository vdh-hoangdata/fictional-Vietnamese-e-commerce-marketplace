# Data analyst practice

Work from cleansed learner-built tables. State your grain, local timezone,
observation cutoff, treatment of failed orders and uncertainty in every result.
Each row below is a business request, not a SQL solution. GMV and cash are
different measures. The available data does not establish accounting revenue,
causal campaign ROI or fully costed profit.

## Beginner

| # | Business question | Stakeholder | Tables / scope | Expected deliverable | Difficulty | Common interpretation pitfall |
|---|---|---|---|---|---|---|
| 1 | How do monthly placed-order GMV and collected cash differ? | Finance manager | orders, order_items, payments, refunds | Monthly VND table and trend chart with metric definitions | Beginner | Counting every payment attempt or subtracting coupon discounts twice |
| 2 | What is average merchandise order value by web and app channel? | Commerce manager | orders, order_items | Channel comparison with successful-checkout and all-placed-order variants | Beginner | Mixing shipping into merchandise AOV without stating it |
| 3 | Which departments lead units and GMV? | Merchandising | items, products, category hierarchy | Ranked department chart and unit/value comparison | Beginner | Joining both parent and leaf categories multiplies rows |
| 4 | Which sellers have the most delivered merchandise value? | Seller operations | sellers, orders, items | Seller scorecard | Beginner | Split parcels inflate order counts |
| 5 | How does customer registration vary by acquisition channel? | CRM | customers | Monthly acquisition dashboard | Beginner | Acquisition channel is not necessarily a purchase attribution channel |
| 6 | What proportion of placed orders is cancelled? | Operations | orders, status history | Local-week rate by cancellation reason | Beginner | Grouping payment failures into customer cancellations |
| 7 | How often does each payment method fail? | Payments lead | payments, orders | Attempt-level and order-level failure rates | Beginner | Retry attempts change the denominator |
| 8 | How long does delivery take by region? | Logistics | shipments, orders, addresses | Median and 90th-percentile lead time | Beginner | Treating orders with multiple parcels as one delivered parcel |
| 9 | How much cash was refunded each month? | Treasury | refunds, payments | Refund cash movement schedule | Beginner | Summing requested amounts as completed refunds |
| 10 | Which products receive low ratings? | Customer experience | reviews, products, items | Rating distribution with review sample sizes | Beginner | Unreviewed purchases are not five-star reviews |
| 11 | How many support cases remain open at the cutoff? | Service manager | support_tickets | Backlog and aging report | Beginner | Missing resolution timestamps are valid open cases |
| 12 | How do sellable inventory and reservations differ? | Warehouse manager | inventory_movements, warehouses | End-of-day on-hand/reserved/available table | Beginner | Reservation delta is not physical stock consumption |

## Intermediate

| # | Business question | Stakeholder | Tables / scope | Expected deliverable | Difficulty | Common interpretation pitfall |
|---|---|---|---|---|---|---|
| 13 | Which customers are high-value repeat purchasers? | CRM lead | customers, orders, items, refunds | RFM segments with explicit qualifying-order definition | Intermediate | Counting abandoned checkout as repeat purchase |
| 14 | What is the 30/60/90-day repeat purchase rate? | Growth | customers, delivered orders | Repeat-rate cohort matrix | Intermediate | Recent cohorts have incomplete observation windows |
| 15 | How does retention vary by first-purchase cohort? | Executive team | orders, customers | Monthly retention heatmap | Intermediate | Registration cohort and purchase cohort answer different questions |
| 16 | Where do shoppers abandon the conversion funnel? | Product analytics | web_events, orders | Session-level ordered funnel by device | Intermediate | Anonymous visitors cannot be assumed to be unique people |
| 17 | Which campaigns have the best attributed merchandise return per VND spent? | Marketing | campaigns, spend, orders, discounts | Descriptive ROAS report with attribution caveats | Intermediate | Correlation is not causal ROI; spend is not the only cost |
| 18 | Are sale-day order spikes accompanied by lower product-level margin proxies? | Merchandising finance | items, product cost, coupons, spend | Gross product-margin proxy excluding logistics/overhead, with limitations | Intermediate | Product cost alone does not measure contribution profit or platform revenue |
| 19 | How much of reported sales growth comes from units versus price/mix? | Planning | orders, items, price history | Period comparison decomposing units and mix | Intermediate | Applying current prices to historical orders |
| 20 | Which product categories have the highest return rates? | Quality lead | returns, items, delivered orders | Quantity-based and line-based return rates | Intermediate | Return requests can be rejected or pending |
| 21 | Which delivery partners breach promises most often? | Carrier management | shipments, tracking, addresses | Geography-adjusted SLA dashboard | Intermediate | Pending parcels need exposure-based handling, not zero delay |
| 22 | How much COD cash remains unsettled? | Treasury | payments, shipments, orders | Aging buckets from delivery to settlement | Intermediate | Delivered GMV is not settled COD cash |
| 23 | Do support response times differ by issue and priority? | Service operations | tickets, refunds, shipment events | Response/resolution percentiles with censoring | Intermediate | Unresolved tickets must not disappear from service measures |
| 24 | Which products turn inventory slowly? | Supply planning | inventory movements, items, product costs | Unit inventory turnover / days-cover proxy | Intermediate | Opening receipts and sellable quarantine affect denominator; no daily valuation ledger exists |

## Advanced

| # | Business question | Stakeholder | Tables / scope | Expected deliverable | Difficulty | Common interpretation pitfall |
|---|---|---|---|---|---|---|
| 25 | What explains an unexpected checkout completion drop? | Incident manager | web events, payment attempts, support, orders | Time-bounded incident hypothesis with comparison groups | Advanced | An increase in traffic can change shopper mix |
| 26 | Does one carrier explain a regional delivery slowdown? | COO | shipments, tracking, geography, tickets | Carrier/region timeline and operational recommendation | Advanced | Order month and dispatch month are different exposures |
| 27 | Did a popular category lose sales because sellable stock was unavailable? | Supply director | inventory ledger, status reasons, products, orders | Availability timeline and demand-loss bounds | Advanced | Cancelled orders show attempted demand, not proven lost incremental sales |
| 28 | Does a quality problem propagate into returns, reviews and support? | Quality director | products, returns, reviews, tickets, orders | Purchase-cohort investigation with linked signals | Advanced | Reviews and returns are delayed and selectively observed |
| 29 | How much attribution changes under first-touch versus observed last-touch? | Growth science | event sessions, campaigns, orders | Comparison with an explicit unobserved-touch category | Advanced | Device identities are not cross-device person identities |
| 30 | Can finance reconcile placed GMV, discounts, payable cash, captures and refunds? | Controller | orders, items, discounts, payments, refunds | Reconciliation waterfall and exception register | Advanced | Payment attempts cannot be joined directly to lines without pre-aggregation |
| 31 | Are repeat shoppers more resilient to payment failures? | Product leadership | customers, historical orders, attempts, sessions | Cohort comparison using pre-order features only | Advanced | Future purchases leak into historical customer classification |
| 32 | Are seller scorecards fair after controlling for product mix and geography? | Marketplace lead | sellers, categories, items, shipments, returns | Standardized descriptive comparison with uncertainty | Advanced | Apparent performance may reflect selection rather than seller quality |
| 33 | How do dashboard KPIs change when late records and corrections arrive? | BI owner | raw source revisions, CDC, canonical contract | As-known-at-time versus latest-corrected comparison | Advanced | Using ingestion time as business time rewrites historical demand |
| 34 | Which metrics would be needed to calculate real platform revenue and contribution margin? | CFO | Current modeled finance and missing costs | Metric-gap assessment and proposed data contract | Advanced | Marketplace GMV and seller procurement cost do not define platform profit |

Recommended first exercise: #1. Define the measures before making a chart.
