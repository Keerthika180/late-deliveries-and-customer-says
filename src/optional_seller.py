import duckdb

result = duckdb.sql("""
WITH seller_orders AS (
    SELECT DISTINCT
        oi.seller_id,
        oi.order_id
    FROM read_csv_auto('data/olist_order_items_dataset.csv') oi
),

delivered_orders AS (
    SELECT
        order_id,
        order_delivered_customer_date,
        order_estimated_delivery_date
    FROM read_csv_auto('data/olist_orders_dataset.csv')
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
),

seller_delivery AS (
    SELECT
        so.seller_id,
        so.order_id,
        CASE
            WHEN d.order_delivered_customer_date >
                 d.order_estimated_delivery_date
            THEN 1
            ELSE 0
        END AS is_late
    FROM seller_orders so
    INNER JOIN delivered_orders d
        ON so.order_id = d.order_id
),

seller_summary AS (
    SELECT
        seller_id,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(is_late) AS late_orders
    FROM seller_delivery
    GROUP BY seller_id
)

SELECT
    seller_id,
    total_orders,
    late_orders,
    ROUND(100.0 * late_orders / total_orders, 2) AS late_share_percentage
FROM seller_summary
WHERE total_orders >= 50
ORDER BY late_share_percentage DESC
""")

# Save the result as a CSV file
result.write_csv("outputs/optional_seller_late_share.csv")

print("Seller late-share result saved successfully.")