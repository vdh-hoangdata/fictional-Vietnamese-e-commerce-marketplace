# Import into SQL Server

The supplied scripts target SQL Server 2017+ and have not been executed against
a server in this workspace. SQLite validation verifies the data contract, not
T-SQL execution. No server instance or credentials are assumed.

Run `sql/01_create_database.sql`, select VietCommerce, then run
`02_create_tables.sql` and `04_staging_tables.sql`. DDL creates BIGINT business
keys and VND amounts, INT quantities, BIT flags, NVARCHAR strings, DATE local
reporting dates and DATETIME2(0) UTC event instants. There are no identity business
keys. `03_constraints_indexes.sql` adds FKs and reporting indexes after loading
typed tables. These scripts initialize a fresh database and are not migrations.

For exercises, import each raw CSV part into the matching `staging` table. Use
the Import Flat File/Import and Export Wizard with UTF-8 code page 65001, comma
delimiter, double-quote qualifier, first-row column names and **text columns**.
Inspect preview and explicit column mappings: automatic numeric inference is
unsafe with malformed values. Omit staging_row_id and loaded_at from the mapping
so their defaults apply. Stage duplicates and nullable fields without business
constraints. `05_load_guidance.sql` shows an alternative BULK INSERT into a
temporary text table and safe conversion examples; edit the server-visible path.
The database service account, not the Python user, needs file access.

Import every bounded-size part; each has its own header. Never load raw sources
directly into constrained dbo tables. JSONL web events and CDC should be landed
as one JSON string per line with a script or your ingestion tool, then parsed
with OPENJSON. The Import Wizard's delimited parser is not a JSONL parser. Nested
properties and product attributes are NVARCHAR(MAX) JSON text in the typed model.

Students implement version-based deduplication, quarantine and conversion from
staging to their own Silver layer. Use TRY_CONVERT(BIGINT, ...) and explicit
ISO-8601 date handling. Convert a Z timestamp to datetimeoffset first, then to
UTC datetime2; do not implicitly apply the local server timezone. Use NULLIF for
empty strings, and distinguish malformed required numerics from valid zero.
`DATETIME2` has no timezone metadata; UTC is a documented storage contract.

For an instructor reference load, canonical CSVs are already typed by contract;
load parents before children (warehouses, sellers, categories roots/leaves,
products, campaigns, coupons, customers, addresses, orders, items, prices,
histories, payments, shipments, shipment_items, events, returns, refunds, support,
reviews, inventory and spend). FKs can be added after all tables load, resolving
taxonomy self-references and refund/return dependencies without disabling checks.
Reconcile imported counts with the file manifest before running
`03_constraints_indexes.sql` and `06_data_quality_checks.sql`.

For Vietnam reporting, SQL Server's Windows timezone name is
`SE Asia Standard Time`: `(ordered_at AT TIME ZONE 'UTC') AT TIME ZONE
'SE Asia Standard Time'`. Local midnight boundaries differ from UTC dates.
Marketing spend is already a local date and must not receive a second shift.
