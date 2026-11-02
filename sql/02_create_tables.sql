-- SQL Server 2017+; run 01 first, then select VietCommerce. No server connection is made by Python.
USE [VietCommerce];
GO
CREATE TABLE dbo.[customers] (
    [customer_id] BIGINT NOT NULL,
    [customer_name] NVARCHAR(200) NOT NULL,
    [email] NVARCHAR(200) NULL,
    [phone] NVARCHAR(200) NULL,
    [registered_at] DATETIME2(0) NOT NULL,
    [inactive_at] DATETIME2(0) NULL,
    [status] NVARCHAR(200) NOT NULL,
    [acquisition_channel] NVARCHAR(200) NOT NULL,
    [spending_segment] NVARCHAR(200) NOT NULL,
    CONSTRAINT [PK_customers] PRIMARY KEY CLUSTERED ([customer_id])
);
GO
CREATE TABLE dbo.[customer_addresses] (
    [address_id] BIGINT NOT NULL,
    [customer_id] BIGINT NOT NULL,
    [province] NVARCHAR(200) NOT NULL,
    [district] NVARCHAR(200) NULL,
    [address_line] NVARCHAR(200) NOT NULL,
    [postal_code] NVARCHAR(200) NULL,
    [is_default] BIT NOT NULL,
    CONSTRAINT [PK_customer_addresses] PRIMARY KEY CLUSTERED ([address_id])
);
GO
CREATE TABLE dbo.[sellers] (
    [seller_id] BIGINT NOT NULL,
    [seller_name] NVARCHAR(200) NOT NULL,
    [seller_type] NVARCHAR(200) NOT NULL,
    [registered_at] DATETIME2(0) NOT NULL,
    [province] NVARCHAR(200) NOT NULL,
    [status] NVARCHAR(200) NOT NULL,
    [warehouse_id] BIGINT NOT NULL,
    CONSTRAINT [PK_sellers] PRIMARY KEY CLUSTERED ([seller_id])
);
GO
CREATE TABLE dbo.[categories] (
    [category_id] BIGINT NOT NULL,
    [category_name] NVARCHAR(200) NOT NULL,
    [parent_category_id] BIGINT NULL,
    [category_level] INT NOT NULL,
    CONSTRAINT [PK_categories] PRIMARY KEY CLUSTERED ([category_id])
);
GO
CREATE TABLE dbo.[products] (
    [product_id] BIGINT NOT NULL,
    [seller_id] BIGINT NOT NULL,
    [category_id] BIGINT NOT NULL,
    [brand] NVARCHAR(200) NOT NULL,
    [product_name] NVARCHAR(200) NOT NULL,
    [unit_cost] BIGINT NOT NULL,
    [attributes] NVARCHAR(MAX) NOT NULL,
    [launched_at] DATETIME2(0) NOT NULL,
    [discontinued_at] DATETIME2(0) NULL,
    [is_active] BIT NOT NULL,
    CONSTRAINT [PK_products] PRIMARY KEY CLUSTERED ([product_id])
);
GO
CREATE TABLE dbo.[product_price_history] (
    [price_history_id] BIGINT NOT NULL,
    [product_id] BIGINT NOT NULL,
    [effective_from] DATETIME2(0) NOT NULL,
    [effective_to] DATETIME2(0) NOT NULL,
    [listed_price] BIGINT NOT NULL,
    [promotional_price] BIGINT NULL,
    [change_reason] NVARCHAR(200) NOT NULL,
    CONSTRAINT [PK_product_price_history] PRIMARY KEY CLUSTERED ([price_history_id])
);
GO
CREATE TABLE dbo.[orders] (
    [order_id] BIGINT NOT NULL,
    [customer_id] BIGINT NOT NULL,
    [address_id] BIGINT NOT NULL,
    [ordered_at] DATETIME2(0) NOT NULL,
    [sales_channel] NVARCHAR(200) NOT NULL,
    [status] NVARCHAR(200) NOT NULL,
    [currency] NVARCHAR(200) NOT NULL,
    [item_gmv] BIGINT NOT NULL,
    [line_discount] BIGINT NOT NULL,
    [order_discount] BIGINT NOT NULL,
    [shipping_fee] BIGINT NOT NULL,
    [total_payable] BIGINT NOT NULL,
    [campaign_id] BIGINT NULL,
    CONSTRAINT [PK_orders] PRIMARY KEY CLUSTERED ([order_id])
);
GO
CREATE TABLE dbo.[order_items] (
    [order_item_id] BIGINT NOT NULL,
    [order_id] BIGINT NOT NULL,
    [product_id] BIGINT NOT NULL,
    [seller_id] BIGINT NOT NULL,
    [quantity] INT NOT NULL,
    [unit_price] BIGINT NOT NULL,
    [item_gmv] BIGINT NOT NULL,
    [line_discount] BIGINT NOT NULL,
    [allocated_order_discount] BIGINT NOT NULL,
    [item_amount] BIGINT NOT NULL,
    CONSTRAINT [PK_order_items] PRIMARY KEY CLUSTERED ([order_item_id])
);
GO
CREATE TABLE dbo.[order_status_history] (
    [status_event_id] BIGINT NOT NULL,
    [order_id] BIGINT NOT NULL,
    [previous_status] NVARCHAR(200) NULL,
    [new_status] NVARCHAR(200) NOT NULL,
    [event_at] DATETIME2(0) NOT NULL,
    [source_system] NVARCHAR(200) NOT NULL,
    [change_reason] NVARCHAR(200) NOT NULL,
    CONSTRAINT [PK_order_status_history] PRIMARY KEY CLUSTERED ([status_event_id])
);
GO
CREATE TABLE dbo.[coupons] (
    [coupon_id] BIGINT NOT NULL,
    [campaign_id] BIGINT NULL,
    [coupon_code] NVARCHAR(200) NOT NULL,
    [discount_type] NVARCHAR(200) NOT NULL,
    [discount_value] INT NOT NULL,
    [minimum_spend] BIGINT NOT NULL,
    [maximum_discount] BIGINT NOT NULL,
    [category_id] BIGINT NULL,
    [starts_at] DATETIME2(0) NOT NULL,
    [ends_at] DATETIME2(0) NOT NULL,
    [redemption_limit] INT NOT NULL,
    CONSTRAINT [PK_coupons] PRIMARY KEY CLUSTERED ([coupon_id])
);
GO
CREATE TABLE dbo.[order_discounts] (
    [order_discount_id] BIGINT NOT NULL,
    [order_id] BIGINT NOT NULL,
    [coupon_id] BIGINT NOT NULL,
    [allocation_method] NVARCHAR(200) NOT NULL,
    [discount_amount] BIGINT NOT NULL,
    CONSTRAINT [PK_order_discounts] PRIMARY KEY CLUSTERED ([order_discount_id])
);
GO
CREATE TABLE dbo.[payments] (
    [payment_id] BIGINT NOT NULL,
    [order_id] BIGINT NOT NULL,
    [provider] NVARCHAR(200) NOT NULL,
    [method] NVARCHAR(200) NOT NULL,
    [attempt_number] INT NOT NULL,
    [status] NVARCHAR(200) NOT NULL,
    [attempted_at] DATETIME2(0) NOT NULL,
    [authorized_at] DATETIME2(0) NULL,
    [captured_at] DATETIME2(0) NULL,
    [amount] BIGINT NOT NULL,
    [failure_code] NVARCHAR(200) NULL,
    CONSTRAINT [PK_payments] PRIMARY KEY CLUSTERED ([payment_id])
);
GO
CREATE TABLE dbo.[refunds] (
    [refund_id] BIGINT NOT NULL,
    [payment_id] BIGINT NOT NULL,
    [order_id] BIGINT NOT NULL,
    [return_id] BIGINT NULL,
    [requested_amount] BIGINT NOT NULL,
    [refunded_amount] BIGINT NOT NULL,
    [status] NVARCHAR(200) NOT NULL,
    [requested_at] DATETIME2(0) NOT NULL,
    [refunded_at] DATETIME2(0) NULL,
    CONSTRAINT [PK_refunds] PRIMARY KEY CLUSTERED ([refund_id])
);
GO
CREATE TABLE dbo.[warehouses] (
    [warehouse_id] BIGINT NOT NULL,
    [warehouse_name] NVARCHAR(200) NOT NULL,
    [province] NVARCHAR(200) NOT NULL,
    [warehouse_type] NVARCHAR(200) NOT NULL,
    [status] NVARCHAR(200) NOT NULL,
    CONSTRAINT [PK_warehouses] PRIMARY KEY CLUSTERED ([warehouse_id])
);
GO
CREATE TABLE dbo.[inventory_movements] (
    [movement_id] BIGINT NOT NULL,
    [product_id] BIGINT NOT NULL,
    [warehouse_id] BIGINT NOT NULL,
    [movement_type] NVARCHAR(200) NOT NULL,
    [quantity_delta] INT NOT NULL,
    [reserved_delta] INT NOT NULL,
    [reference_type] NVARCHAR(200) NOT NULL,
    [reference_id] BIGINT NOT NULL,
    [event_at] DATETIME2(0) NOT NULL,
    [reason] NVARCHAR(200) NOT NULL,
    CONSTRAINT [PK_inventory_movements] PRIMARY KEY CLUSTERED ([movement_id])
);
GO
CREATE TABLE dbo.[shipments] (
    [shipment_id] BIGINT NOT NULL,
    [order_id] BIGINT NOT NULL,
    [seller_id] BIGINT NOT NULL,
    [warehouse_id] BIGINT NOT NULL,
    [delivery_partner] NVARCHAR(200) NOT NULL,
    [shipping_fee] BIGINT NOT NULL,
    [status] NVARCHAR(200) NOT NULL,
    [created_at] DATETIME2(0) NOT NULL,
    [shipped_at] DATETIME2(0) NULL,
    [expected_delivery_at] DATETIME2(0) NOT NULL,
    [delivered_at] DATETIME2(0) NULL,
    [closed_at] DATETIME2(0) NULL,
    [sla_days] INT NOT NULL,
    CONSTRAINT [PK_shipments] PRIMARY KEY CLUSTERED ([shipment_id])
);
GO
CREATE TABLE dbo.[shipment_items] (
    [shipment_item_id] BIGINT NOT NULL,
    [shipment_id] BIGINT NOT NULL,
    [order_item_id] BIGINT NOT NULL,
    [quantity] INT NOT NULL,
    CONSTRAINT [PK_shipment_items] PRIMARY KEY CLUSTERED ([shipment_item_id])
);
GO
CREATE TABLE dbo.[shipment_events] (
    [shipment_event_id] BIGINT NOT NULL,
    [shipment_id] BIGINT NOT NULL,
    [event_at] DATETIME2(0) NOT NULL,
    [event_type] NVARCHAR(200) NOT NULL,
    [event_location] NVARCHAR(200) NOT NULL,
    [event_sequence] INT NOT NULL,
    CONSTRAINT [PK_shipment_events] PRIMARY KEY CLUSTERED ([shipment_event_id])
);
GO
CREATE TABLE dbo.[returns] (
    [return_id] BIGINT NOT NULL,
    [order_id] BIGINT NOT NULL,
    [order_item_id] BIGINT NOT NULL,
    [requested_quantity] INT NOT NULL,
    [reason] NVARCHAR(200) NOT NULL,
    [requested_at] DATETIME2(0) NOT NULL,
    [received_at] DATETIME2(0) NULL,
    [status] NVARCHAR(200) NOT NULL,
    [outcome] NVARCHAR(200) NOT NULL,
    CONSTRAINT [PK_returns] PRIMARY KEY CLUSTERED ([return_id])
);
GO
CREATE TABLE dbo.[marketing_campaigns] (
    [campaign_id] BIGINT NOT NULL,
    [campaign_name] NVARCHAR(200) NOT NULL,
    [objective] NVARCHAR(200) NOT NULL,
    [channel] NVARCHAR(200) NOT NULL,
    [starts_at] DATETIME2(0) NOT NULL,
    [ends_at] DATETIME2(0) NOT NULL,
    [budget] BIGINT NOT NULL,
    CONSTRAINT [PK_marketing_campaigns] PRIMARY KEY CLUSTERED ([campaign_id])
);
GO
CREATE TABLE dbo.[marketing_spend_daily] (
    [spend_id] BIGINT NOT NULL,
    [campaign_id] BIGINT NOT NULL,
    [spend_date] DATE NOT NULL,
    [channel] NVARCHAR(200) NOT NULL,
    [spend_amount] BIGINT NOT NULL,
    [impressions] INT NOT NULL,
    [clicks] INT NOT NULL,
    CONSTRAINT [PK_marketing_spend_daily] PRIMARY KEY CLUSTERED ([spend_id])
);
GO
CREATE TABLE dbo.[web_events] (
    [event_id] BIGINT NOT NULL,
    [anonymous_visitor_id] NVARCHAR(200) NOT NULL,
    [session_id] NVARCHAR(200) NOT NULL,
    [customer_id] BIGINT NULL,
    [event_type] NVARCHAR(200) NOT NULL,
    [event_at] DATETIME2(0) NOT NULL,
    [product_id] BIGINT NULL,
    [device_type] NVARCHAR(200) NOT NULL,
    [traffic_source] NVARCHAR(200) NOT NULL,
    [campaign_id] BIGINT NULL,
    [properties] NVARCHAR(MAX) NOT NULL,
    CONSTRAINT [PK_web_events] PRIMARY KEY CLUSTERED ([event_id])
);
GO
CREATE TABLE dbo.[reviews] (
    [review_id] BIGINT NOT NULL,
    [customer_id] BIGINT NOT NULL,
    [product_id] BIGINT NOT NULL,
    [order_item_id] BIGINT NOT NULL,
    [rating] INT NOT NULL,
    [reviewed_at] DATETIME2(0) NOT NULL,
    [review_text] NVARCHAR(200) NULL,
    CONSTRAINT [PK_reviews] PRIMARY KEY CLUSTERED ([review_id])
);
GO
CREATE TABLE dbo.[support_tickets] (
    [ticket_id] BIGINT NOT NULL,
    [customer_id] BIGINT NOT NULL,
    [order_id] BIGINT NULL,
    [issue_category] NVARCHAR(200) NOT NULL,
    [priority] NVARCHAR(200) NOT NULL,
    [created_at] DATETIME2(0) NOT NULL,
    [first_response_at] DATETIME2(0) NULL,
    [resolved_at] DATETIME2(0) NULL,
    [status] NVARCHAR(200) NOT NULL,
    CONSTRAINT [PK_support_tickets] PRIMARY KEY CLUSTERED ([ticket_id])
);
GO
