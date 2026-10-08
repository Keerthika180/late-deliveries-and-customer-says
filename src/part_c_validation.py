import duckdb
import csv


# ==========================================
# LOAD ORIGINAL REVIEWS
# ==========================================

reviews = duckdb.read_csv(
    "data/olist_order_reviews_dataset.csv"
)


# ==========================================
# LOAD GROQ CLASSIFICATIONS
# ==========================================

results = duckdb.read_csv(
    "outputs/part_c_results.csv"
)


# ==========================================
# JOIN REVIEWS WITH GROQ RESULTS
# ==========================================

validation_data = duckdb.sql("""
    SELECT
        r.review_id,
        r.order_id,
        r.review_comment_message,
        g.category AS groq_category,
        g.summary AS groq_summary

    FROM reviews r

    INNER JOIN results g
        ON r.review_id = g.review_id

    LIMIT 30
""")


# ==========================================
# GET ROWS
# ==========================================

rows = validation_data.fetchall()


# ==========================================
# SAVE VALIDATION FILE
# ==========================================

with open(
    "part_c_validation_30.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "review_id",
        "order_id",
        "review_comment_message",
        "groq_category",
        "groq_summary",
        "manual_category",
        "correct"
    ])

    for row in rows:

        writer.writerow([
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            "",
            ""
        ])


# ==========================================
# FINAL CHECK
# ==========================================

print()
print("=" * 60)
print("       PART C - MANUAL VALIDATION")
print("=" * 60)

print()
print("Number of reviews:", len(rows))

print()
print("File created:")
print("part_c_validation_30.csv")

print()
print("Columns:")
print("review_id")
print("order_id")
print("review_comment_message")
print("groq_category")
print("groq_summary")
print("manual_category")
print("correct")

print()
print("=" * 60)