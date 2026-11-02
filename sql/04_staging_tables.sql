USE [VietCommerce];
GO
IF SCHEMA_ID('staging') IS NULL EXEC('CREATE SCHEMA staging');
GO
CREATE TABLE staging.[customers] (
    [customer_id] NVARCHAR(MAX) NULL,
    [customer_name] NVARCHAR(MAX) NULL,
    [email] NVARCHAR(MAX) NULL,
    [phone] NVARCHAR(MAX) NULL,
    [registered_at] NVARCHAR(MAX) NULL,
    [inactive_at] NVARCHAR(MAX) NULL,
    [status] NVARCHAR(MAX) NULL,
    [acquisition_channel] NVARCHAR(MAX) NULL,
    [spending_segment] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[customer_addresses] (
    [address_id] NVARCHAR(MAX) NULL,
    [customer_id] NVARCHAR(MAX) NULL,
    [province] NVARCHAR(MAX) NULL,
    [district] NVARCHAR(MAX) NULL,
    [address_line] NVARCHAR(MAX) NULL,
    [postal_code] NVARCHAR(MAX) NULL,
    [is_default] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[sellers] (
    [seller_id] NVARCHAR(MAX) NULL,
    [seller_name] NVARCHAR(MAX) NULL,
    [seller_type] NVARCHAR(MAX) NULL,
    [registered_at] NVARCHAR(MAX) NULL,
    [province] NVARCHAR(MAX) NULL,
    [status] NVARCHAR(MAX) NULL,
    [warehouse_id] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[categories] (
    [category_id] NVARCHAR(MAX) NULL,
    [category_name] NVARCHAR(MAX) NULL,
    [parent_category_id] NVARCHAR(MAX) NULL,
    [category_level] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[products] (
    [product_id] NVARCHAR(MAX) NULL,
    [seller_id] NVARCHAR(MAX) NULL,
    [category_id] NVARCHAR(MAX) NULL,
    [brand] NVARCHAR(MAX) NULL,
    [product_name] NVARCHAR(MAX) NULL,
    [unit_cost] NVARCHAR(MAX) NULL,
    [attributes] NVARCHAR(MAX) NULL,
    [launched_at] NVARCHAR(MAX) NULL,
    [discontinued_at] NVARCHAR(MAX) NULL,
    [is_active] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[product_price_history] (
    [price_history_id] NVARCHAR(MAX) NULL,
    [product_id] NVARCHAR(MAX) NULL,
    [effective_from] NVARCHAR(MAX) NULL,
    [effective_to] NVARCHAR(MAX) NULL,
    [listed_price] NVARCHAR(MAX) NULL,
    [promotional_price] NVARCHAR(MAX) NULL,
    [change_reason] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[orders] (
    [order_id] NVARCHAR(MAX) NULL,
    [customer_id] NVARCHAR(MAX) NULL,
    [address_id] NVARCHAR(MAX) NULL,
    [ordered_at] NVARCHAR(MAX) NULL,
    [sales_channel] NVARCHAR(MAX) NULL,
    [status] NVARCHAR(MAX) NULL,
    [currency] NVARCHAR(MAX) NULL,
    [item_gmv] NVARCHAR(MAX) NULL,
    [line_discount] NVARCHAR(MAX) NULL,
    [order_discount] NVARCHAR(MAX) NULL,
    [shipping_fee] NVARCHAR(MAX) NULL,
    [total_payable] NVARCHAR(MAX) NULL,
    [campaign_id] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[order_items] (
    [order_item_id] NVARCHAR(MAX) NULL,
    [order_id] NVARCHAR(MAX) NULL,
    [product_id] NVARCHAR(MAX) NULL,
    [seller_id] NVARCHAR(MAX) NULL,
    [quantity] NVARCHAR(MAX) NULL,
    [unit_price] NVARCHAR(MAX) NULL,
    [item_gmv] NVARCHAR(MAX) NULL,
    [line_discount] NVARCHAR(MAX) NULL,
    [allocated_order_discount] NVARCHAR(MAX) NULL,
    [item_amount] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[order_status_history] (
    [status_event_id] NVARCHAR(MAX) NULL,
    [order_id] NVARCHAR(MAX) NULL,
    [previous_status] NVARCHAR(MAX) NULL,
    [new_status] NVARCHAR(MAX) NULL,
    [event_at] NVARCHAR(MAX) NULL,
    [source_system] NVARCHAR(MAX) NULL,
    [change_reason] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[coupons] (
    [coupon_id] NVARCHAR(MAX) NULL,
    [campaign_id] NVARCHAR(MAX) NULL,
    [coupon_code] NVARCHAR(MAX) NULL,
    [discount_type] NVARCHAR(MAX) NULL,
    [discount_value] NVARCHAR(MAX) NULL,
    [minimum_spend] NVARCHAR(MAX) NULL,
    [maximum_discount] NVARCHAR(MAX) NULL,
    [category_id] NVARCHAR(MAX) NULL,
    [starts_at] NVARCHAR(MAX) NULL,
    [ends_at] NVARCHAR(MAX) NULL,
    [redemption_limit] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[order_discounts] (
    [order_discount_id] NVARCHAR(MAX) NULL,
    [order_id] NVARCHAR(MAX) NULL,
    [coupon_id] NVARCHAR(MAX) NULL,
    [allocation_method] NVARCHAR(MAX) NULL,
    [discount_amount] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[payments] (
    [payment_id] NVARCHAR(MAX) NULL,
    [order_id] NVARCHAR(MAX) NULL,
    [provider] NVARCHAR(MAX) NULL,
    [method] NVARCHAR(MAX) NULL,
    [attempt_number] NVARCHAR(MAX) NULL,
    [status] NVARCHAR(MAX) NULL,
    [attempted_at] NVARCHAR(MAX) NULL,
    [authorized_at] NVARCHAR(MAX) NULL,
    [captured_at] NVARCHAR(MAX) NULL,
    [amount] NVARCHAR(MAX) NULL,
    [failure_code] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[refunds] (
    [refund_id] NVARCHAR(MAX) NULL,
    [payment_id] NVARCHAR(MAX) NULL,
    [order_id] NVARCHAR(MAX) NULL,
    [return_id] NVARCHAR(MAX) NULL,
    [requested_amount] NVARCHAR(MAX) NULL,
    [refunded_amount] NVARCHAR(MAX) NULL,
    [status] NVARCHAR(MAX) NULL,
    [requested_at] NVARCHAR(MAX) NULL,
    [refunded_at] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[warehouses] (
    [warehouse_id] NVARCHAR(MAX) NULL,
    [warehouse_name] NVARCHAR(MAX) NULL,
    [province] NVARCHAR(MAX) NULL,
    [warehouse_type] NVARCHAR(MAX) NULL,
    [status] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[inventory_movements] (
    [movement_id] NVARCHAR(MAX) NULL,
    [product_id] NVARCHAR(MAX) NULL,
    [warehouse_id] NVARCHAR(MAX) NULL,
    [movement_type] NVARCHAR(MAX) NULL,
    [quantity_delta] NVARCHAR(MAX) NULL,
    [reserved_delta] NVARCHAR(MAX) NULL,
    [reference_type] NVARCHAR(MAX) NULL,
    [reference_id] NVARCHAR(MAX) NULL,
    [event_at] NVARCHAR(MAX) NULL,
    [reason] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[shipments] (
    [shipment_id] NVARCHAR(MAX) NULL,
    [order_id] NVARCHAR(MAX) NULL,
    [seller_id] NVARCHAR(MAX) NULL,
    [warehouse_id] NVARCHAR(MAX) NULL,
    [delivery_partner] NVARCHAR(MAX) NULL,
    [shipping_fee] NVARCHAR(MAX) NULL,
    [status] NVARCHAR(MAX) NULL,
    [created_at] NVARCHAR(MAX) NULL,
    [shipped_at] NVARCHAR(MAX) NULL,
    [expected_delivery_at] NVARCHAR(MAX) NULL,
    [delivered_at] NVARCHAR(MAX) NULL,
    [closed_at] NVARCHAR(MAX) NULL,
    [sla_days] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[shipment_items] (
    [shipment_item_id] NVARCHAR(MAX) NULL,
    [shipment_id] NVARCHAR(MAX) NULL,
    [order_item_id] NVARCHAR(MAX) NULL,
    [quantity] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[shipment_events] (
    [shipment_event_id] NVARCHAR(MAX) NULL,
    [shipment_id] NVARCHAR(MAX) NULL,
    [event_at] NVARCHAR(MAX) NULL,
    [event_type] NVARCHAR(MAX) NULL,
    [event_location] NVARCHAR(MAX) NULL,
    [event_sequence] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[returns] (
    [return_id] NVARCHAR(MAX) NULL,
    [order_id] NVARCHAR(MAX) NULL,
    [order_item_id] NVARCHAR(MAX) NULL,
    [requested_quantity] NVARCHAR(MAX) NULL,
    [reason] NVARCHAR(MAX) NULL,
    [requested_at] NVARCHAR(MAX) NULL,
    [received_at] NVARCHAR(MAX) NULL,
    [status] NVARCHAR(MAX) NULL,
    [outcome] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[marketing_campaigns] (
    [campaign_id] NVARCHAR(MAX) NULL,
    [campaign_name] NVARCHAR(MAX) NULL,
    [objective] NVARCHAR(MAX) NULL,
    [channel] NVARCHAR(MAX) NULL,
    [starts_at] NVARCHAR(MAX) NULL,
    [ends_at] NVARCHAR(MAX) NULL,
    [budget] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[marketing_spend_daily] (
    [spend_id] NVARCHAR(MAX) NULL,
    [campaign_id] NVARCHAR(MAX) NULL,
    [spend_date] NVARCHAR(MAX) NULL,
    [channel] NVARCHAR(MAX) NULL,
    [spend_amount] NVARCHAR(MAX) NULL,
    [impressions] NVARCHAR(MAX) NULL,
    [clicks] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[web_events] (
    [event_id] NVARCHAR(MAX) NULL,
    [anonymous_visitor_id] NVARCHAR(MAX) NULL,
    [session_id] NVARCHAR(MAX) NULL,
    [customer_id] NVARCHAR(MAX) NULL,
    [event_type] NVARCHAR(MAX) NULL,
    [event_at] NVARCHAR(MAX) NULL,
    [product_id] NVARCHAR(MAX) NULL,
    [device_type] NVARCHAR(MAX) NULL,
    [traffic_source] NVARCHAR(MAX) NULL,
    [campaign_id] NVARCHAR(MAX) NULL,
    [properties] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[reviews] (
    [review_id] NVARCHAR(MAX) NULL,
    [customer_id] NVARCHAR(MAX) NULL,
    [product_id] NVARCHAR(MAX) NULL,
    [order_item_id] NVARCHAR(MAX) NULL,
    [rating] NVARCHAR(MAX) NULL,
    [reviewed_at] NVARCHAR(MAX) NULL,
    [review_text] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE TABLE staging.[support_tickets] (
    [ticket_id] NVARCHAR(MAX) NULL,
    [customer_id] NVARCHAR(MAX) NULL,
    [order_id] NVARCHAR(MAX) NULL,
    [issue_category] NVARCHAR(MAX) NULL,
    [priority] NVARCHAR(MAX) NULL,
    [created_at] NVARCHAR(MAX) NULL,
    [first_response_at] NVARCHAR(MAX) NULL,
    [resolved_at] NVARCHAR(MAX) NULL,
    [status] NVARCHAR(MAX) NULL,
    [_ingested_at] NVARCHAR(MAX) NULL,
    [_batch_id] NVARCHAR(MAX) NULL,
    [_source_version] NVARCHAR(MAX) NULL,
    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL,
    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
