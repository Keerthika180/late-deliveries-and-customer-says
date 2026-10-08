import duckdb

# ============================================================
# PART A: DATA ENGINEERING
# ============================================================

# ------------------------------------------------------------
# Step A1: Load the three source files
# ------------------------------------------------------------

orders = duckdb.read_csv("data/olist_orders_dataset.csv")
order_items = duckdb.read_csv("data/olist_order_items_dataset.csv")
reviews = duckdb.read_csv("data/olist_order_reviews_dataset.csv")

# Check that the files loaded successfully
print("Orders:", len(orders))
print("Order Items:", len(order_items))
print("Reviews:", len(reviews))


# ------------------------------------------------------------
# Step A2: Display the columns in each dataset
# ------------------------------------------------------------

print("\nOrders columns:")
print(orders.columns)

print("\nOrder Items columns:")
print(order_items.columns)

print("\nReviews columns:")
print(reviews.columns)


# ------------------------------------------------------------
# Step A3: Summarize order items
#
# One order can have multiple item rows.
# We aggregate by order_id so that we get ONE row per order.
# ------------------------------------------------------------

item_summary = duckdb.sql("""
    SELECT
        order_id,
        COUNT(*) AS number_of_items,
        SUM(price + freight_value) AS order_value
    FROM order_items
    GROUP BY order_id
""")

print("\nItem Summary:")
print(item_summary.limit(5))


# ------------------------------------------------------------
# Step A4: Check for multiple reviews per order
#
# Some orders have more than one review record.
# We identify them before creating the review summary.
# ------------------------------------------------------------

review_counts = duckdb.sql("""
    SELECT
        order_id,
        COUNT(*) AS review_count
    FROM reviews
    GROUP BY order_id
    HAVING COUNT(*) > 1
""")

print("\nOrders with multiple reviews:")
print("Count:", len(review_counts))


# ------------------------------------------------------------
# Step A5: Create one review score per order
#
# If an order has multiple reviews, AVG() gives one
# review score per order.
# ------------------------------------------------------------

review_summary = duckdb.sql("""
    SELECT
        order_id,
        AVG(review_score) AS review_score
    FROM reviews
    GROUP BY order_id
""")

print("\nReview Summary:")
print(review_summary.limit(5))


# ------------------------------------------------------------
# Step A6: Join orders, item summary, and review summary
#
# Items and reviews were already aggregated by order_id.
# Therefore, joining them will not multiply order rows.
# ------------------------------------------------------------

order_table = duckdb.sql("""
    SELECT
        o.order_id,
        o.order_status,
        o.order_purchase_timestamp AS purchase_date,
        o.order_estimated_delivery_date AS estimated_date,
        o.order_delivered_customer_date AS delivered_date,
        i.number_of_items,
        i.order_value,
        r.review_score
    FROM orders o
    INNER JOIN item_summary i
        ON o.order_id = i.order_id
    LEFT JOIN review_summary r
        ON o.order_id = r.order_id
""")

print("\nOrder Table:")
print(order_table.limit(5))


# ------------------------------------------------------------
# Step A7: Create the final table
#
# Keep only delivered orders.
# Calculate days_late:
#   - If delivered after estimated date -> number of days late
#   - Otherwise -> 0
# ------------------------------------------------------------

final_orders = duckdb.sql("""
    SELECT
        order_id,
        purchase_date,
        estimated_date,
        delivered_date,
        number_of_items,
        order_value,
        review_score,
        CASE
            WHEN delivered_date > estimated_date
            THEN DATE_DIFF('day', estimated_date, delivered_date)
            ELSE 0
        END AS days_late
    FROM order_table
    WHERE order_status = 'delivered'
      AND delivered_date IS NOT NULL
""")

print("\nFinal Orders:")
print(final_orders.limit(5))

print("\nTotal delivered orders in final table:")
print(len(final_orders))


# ============================================================
# REQUIRED CHECK 1
# Order ID must be unique in the final table
# ============================================================

duplicate_orders = duckdb.sql("""
    SELECT
        order_id,
        COUNT(*) AS count
    FROM final_orders
    GROUP BY order_id
    HAVING COUNT(*) > 1
""")

print("\nDuplicate order IDs:")
print("Count:", len(duplicate_orders))


# ============================================================
# REQUIRED CHECK 2
# Delivered date must be after purchase date
# ============================================================

invalid_dates = duckdb.sql("""
    SELECT
        order_id,
        purchase_date,
        delivered_date
    FROM final_orders
    WHERE delivered_date <= purchase_date
""")

print("\nInvalid delivery dates:")
print("Count:", len(invalid_dates))


# ============================================================
# REQUIRED CHECK 3
# Order value must equal the sum of its items
#
# IMPORTANT:
# Recalculate directly from the ORIGINAL order_items table.
# This makes the validation independent of item_summary.
# ============================================================

value_check = duckdb.sql("""
    SELECT
        f.order_id,
        f.order_value AS final_order_value,
        SUM(i.price + i.freight_value) AS item_sum
    FROM final_orders f
    JOIN order_items i
        ON f.order_id = i.order_id
    GROUP BY
        f.order_id,
        f.order_value
    HAVING ABS(
        f.order_value - SUM(i.price + i.freight_value)
    ) > 0.01
""")

print("\nOrder value mismatches:")
print("Count:", len(value_check))


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n========================================")
print("PART A DATA QUALITY CHECK SUMMARY")
print("========================================")

print("Duplicate order IDs:", len(duplicate_orders))
print("Invalid delivery dates:", len(invalid_dates))
print("Order value mismatches:", len(value_check))

if (
    len(duplicate_orders) == 0
    and len(invalid_dates) == 0
    and len(value_check) == 0
):
    print("\nAll 3 required checks passed!")
else:
    print("\nOne or more checks failed. Please review the results.")