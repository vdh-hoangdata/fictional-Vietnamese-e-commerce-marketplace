USE [VietCommerce];
GO
-- Demonstration for one raw customers part. Replace the literal with a path
-- visible to the SQL Server service account. This block is intentionally manual.
-- Temporary columns exactly match the CSV header order; identity/default staging
-- columns are omitted so they cannot accidentally consume source fields.
/*
CREATE TABLE #customers_raw (
 customer_id NVARCHAR(MAX), customer_name NVARCHAR(MAX), email NVARCHAR(MAX),
 phone NVARCHAR(MAX), registered_at NVARCHAR(MAX), inactive_at NVARCHAR(MAX),
 status NVARCHAR(MAX), acquisition_channel NVARCHAR(MAX), spending_segment NVARCHAR(MAX),
 _ingested_at NVARCHAR(MAX), _batch_id NVARCHAR(MAX), _source_version NVARCHAR(MAX)
);
BULK INSERT #customers_raw
FROM 'C:\VietCommerce\raw\customer_crm\customers.csv'
WITH (FORMAT='CSV', FIRSTROW=2, FIELDQUOTE='"', CODEPAGE='65001', ROWTERMINATOR='0x0a', TABLOCK);
INSERT INTO staging.customers
 (customer_id,customer_name,email,phone,registered_at,inactive_at,status,
 acquisition_channel,spending_segment,_ingested_at,_batch_id,_source_version)
SELECT * FROM #customers_raw;
DROP TABLE #customers_raw;
*/
-- Conversion preview, not a full student ETL solution:
SELECT TOP (20) customer_id,
 TRY_CONVERT(BIGINT,NULLIF(customer_id,N'')) AS parsed_customer_id,
 CAST(SWITCHOFFSET(TRY_CONVERT(DATETIMEOFFSET(0),NULLIF(registered_at,N''),127),'+00:00') AS DATETIME2(0)) AS registered_at_utc
FROM staging.customers;
-- JSONL: ingest one complete line into a single NVARCHAR(MAX) column before
-- OPENJSON. Do not split JSON on commas. Example inspection:
-- SELECT JSON_VALUE(payload,'$.table'), JSON_VALUE(payload,'$.source_version')
-- FROM bronze.cdc_lines;
