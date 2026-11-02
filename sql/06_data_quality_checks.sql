USE [VietCommerce];
GO
-- Diagnostic result sets return violations. Do not UPDATE records to hide them.
SELECT o.order_id
FROM dbo.orders o JOIN (
 SELECT order_id,SUM(item_gmv) AS g,SUM(line_discount) AS l,
 SUM(allocated_order_discount) AS d,SUM(item_amount) AS n
 FROM dbo.order_items GROUP BY order_id
) i ON o.order_id=i.order_id
WHERE o.item_gmv<>i.g OR o.line_discount<>i.l OR o.order_discount<>i.d
 OR o.total_payable<>i.n+o.shipping_fee;

SELECT p.order_id,COUNT(*) AS captures FROM dbo.payments p
WHERE p.status=N'captured' GROUP BY p.order_id HAVING COUNT(*)>1;

SELECT p.payment_id FROM dbo.payments p JOIN dbo.refunds r ON r.payment_id=p.payment_id
GROUP BY p.payment_id,p.amount,p.status
HAVING SUM(r.requested_amount)>p.amount OR SUM(r.refunded_amount)>p.amount OR p.status<>N'captured';

SELECT i.order_item_id FROM dbo.order_items i JOIN dbo.orders o ON o.order_id=i.order_id
LEFT JOIN dbo.product_price_history p ON p.product_id=i.product_id
 AND o.ordered_at>=p.effective_from AND o.ordered_at<p.effective_to
GROUP BY i.order_item_id,i.unit_price
HAVING COUNT(p.price_history_id)<>1 OR MIN(COALESCE(p.promotional_price,p.listed_price))<>i.unit_price;

WITH balances AS (
 SELECT movement_id,
 SUM(CAST(quantity_delta AS BIGINT)) OVER(PARTITION BY product_id,warehouse_id ORDER BY event_at,movement_id ROWS UNBOUNDED PRECEDING) AS on_hand,
 SUM(CAST(reserved_delta AS BIGINT)) OVER(PARTITION BY product_id,warehouse_id ORDER BY event_at,movement_id ROWS UNBOUNDED PRECEDING) AS reserved
 FROM dbo.inventory_movements
)
SELECT * FROM balances WHERE on_hand<0 OR reserved<0 OR on_hand-reserved<0;

SELECT o.order_id FROM dbo.orders o JOIN dbo.customers c ON c.customer_id=o.customer_id
WHERE o.ordered_at<c.registered_at;

SELECT shipment_id FROM dbo.shipments
WHERE delivered_at<shipped_at OR shipped_at<created_at;

SELECT payment_id FROM dbo.payments
WHERE (status=N'captured' AND captured_at IS NULL)
 OR (status<>N'captured' AND captured_at IS NOT NULL);

-- Staging defects are separate from canonical failures. A failed payment or
-- optional NULL is valid. These rows need a conversion/normalization decision.
SELECT staging_row_id,customer_id FROM staging.customers
WHERE TRY_CONVERT(BIGINT,NULLIF(customer_id,N'')) IS NULL;
SELECT order_id,COUNT(*) AS ingestions FROM staging.orders
GROUP BY order_id HAVING COUNT(*)>1;
