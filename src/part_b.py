import duckdb
import matplotlib.pyplot as plt


# ============================================================
# HELPER FUNCTION - PRINT CLEAN BOX TABLE
# ============================================================

def print_box_table(headers, rows):

    rows = [
        [str(value) for value in row]
        for row in rows
    ]

    widths = []

    for i, header in enumerate(headers):

        max_width = len(header)

        for row in rows:
            max_width = max(max_width, len(row[i]))

        widths.append(max_width)

    top = "┌" + "┬".join(
        "─" * (w + 2)
        for w in widths
    ) + "┐"

    middle = "├" + "┼".join(
        "─" * (w + 2)
        for w in widths
    ) + "┤"

    bottom = "└" + "┴".join(
        "─" * (w + 2)
        for w in widths
    ) + "┘"

    print(top)

    print(
        "│ "
        + " │ ".join(
            f"{header:<{widths[i]}}"
            for i, header in enumerate(headers)
        )
        + " │"
    )

    print(middle)

    for row in rows:

        print(
            "│ "
            + " │ ".join(
                f"{row[i]:>{widths[i]}}"
                for i in range(len(headers))
            )
            + " │"
        )

    print(bottom)


# ============================================================
# PART B - ANALYTICS
# ============================================================


# ============================================================
# STEP 1 - LOAD DATA
# ============================================================

orders = duckdb.read_csv(
    "data/olist_orders_dataset.csv"
)

order_items = duckdb.read_csv(
    "data/olist_order_items_dataset.csv"
)

reviews = duckdb.read_csv(
    "data/olist_order_reviews_dataset.csv"
)

print("Data loaded successfully.")


# ============================================================
# STEP 2 - PREPARE ORDER-LEVEL DATA
# ============================================================


# ------------------------------------------------------------
# 2.1 Item summary
# ------------------------------------------------------------

item_summary = duckdb.sql("""
    SELECT
        order_id,
        COUNT(*) AS number_of_items,
        SUM(price + freight_value) AS order_value
    FROM order_items
    GROUP BY order_id
""")


# ------------------------------------------------------------
# 2.2 Review summary
# ------------------------------------------------------------

review_summary = duckdb.sql("""
    SELECT
        order_id,
        AVG(review_score) AS review_score
    FROM reviews
    GROUP BY order_id
""")


# ------------------------------------------------------------
# 2.3 Join order-level information
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

    LEFT JOIN item_summary i
        ON o.order_id = i.order_id

    LEFT JOIN review_summary r
        ON o.order_id = r.order_id
""")


# ------------------------------------------------------------
# 2.4 Calculate days late
# ------------------------------------------------------------

final_orders = duckdb.sql("""
    SELECT
        *,
        CASE
            WHEN delivered_date > estimated_date
            THEN DATE_DIFF(
                'day',
                estimated_date,
                delivered_date
            )
            ELSE 0
        END AS days_late

    FROM order_table

    WHERE order_status = 'delivered'
      AND delivered_date IS NOT NULL
""")


print(
    "\nDelivered order-level data prepared successfully."
)

print(
    "Number of delivered orders:",
    len(final_orders)
)


# ============================================================
# B1 - SHARE OF ORDERS DELIVERED LATE
# ============================================================

late_summary = duckdb.sql("""
    SELECT
        COUNT(*) AS total_orders,

        SUM(
            CASE
                WHEN days_late > 0 THEN 1
                ELSE 0
            END
        ) AS late_orders,

        ROUND(
            100.0 *
            SUM(
                CASE
                    WHEN days_late > 0 THEN 1
                    ELSE 0
                END
            ) / COUNT(*),
            2
        ) AS late_share_percentage

    FROM final_orders
""")

late_row = late_summary.fetchone()


print(
    "\n============================================================"
)

print(
    "B1 - SHARE OF ORDERS DELIVERED LATE"
)

print(
    "============================================================"
)


print_box_table(
    [
        "total_orders",
        "late_orders",
        "late_share_percentage"
    ],
    [[
        late_row[0],
        late_row[1],
        f"{late_row[2]:.2f}"
    ]]
)


# ============================================================
# B2 - LATE SHARE BY MONTH
# ============================================================

monthly_late_share = duckdb.sql("""
    SELECT

        DATE_TRUNC(
            'month',
            purchase_date
        ) AS month,

        COUNT(*) AS total_orders,

        SUM(
            CASE
                WHEN days_late > 0 THEN 1
                ELSE 0
            END
        ) AS late_orders,

        ROUND(
            100.0 *
            SUM(
                CASE
                    WHEN days_late > 0 THEN 1
                    ELSE 0
                END
            ) / COUNT(*),
            2
        ) AS late_share_percentage

    FROM final_orders

    GROUP BY DATE_TRUNC(
        'month',
        purchase_date
    )

    ORDER BY month
""")


print(
    "\n============================================================"
)

print(
    "B2 - LATE DELIVERY SHARE BY MONTH"
)

print(
    "============================================================"
)


monthly_rows = monthly_late_share.fetchall()

formatted_monthly_rows = []


for row in monthly_rows:

    formatted_monthly_rows.append([
        row[0].strftime("%Y-%m"),
        row[1],
        row[2],
        f"{row[3]:.2f}%"
    ])


print_box_table(
    [
        "month",
        "total_orders",
        "late_orders",
        "late_share_percentage"
    ],
    formatted_monthly_rows
)


# ============================================================
# B2 - CLEAN UI-FRIENDLY GRAPH
# ============================================================

months = []
late_share = []
total_orders = []


for row in monthly_rows:

    months.append(
        row[0].strftime("%b %Y")
    )

    late_share.append(
        float(row[3])
    )

    total_orders.append(
        int(row[1])
    )


# ------------------------------------------------------------
# Create figure
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(14, 7)
)


# ------------------------------------------------------------
# Main trend
# ------------------------------------------------------------

ax.plot(
    months,
    late_share,
    marker="o",
    markersize=6,
    linewidth=2.8
)


# ------------------------------------------------------------
# Light area below trend
# ------------------------------------------------------------

ax.fill_between(
    months,
    late_share,
    alpha=0.08
)


# ============================================================
# OVERALL LATE SHARE
# ============================================================

overall_late_share = float(
    late_row[2]
)


ax.axhline(
    overall_late_share,
    linestyle="--",
    linewidth=1.5,
    alpha=0.6
)


ax.text(
    len(months) - 1,
    overall_late_share + 1.0,
    f"Overall: {overall_late_share:.2f}%",
    ha="right",
    fontsize=9,
    fontweight="bold"
)


# ============================================================
# SEPTEMBER 2016
# ============================================================

# September 2016 has only one delivered order.
# Therefore 100% represents one order, not a large trend.

if (
    len(late_share) > 0
    and late_share[0] == 100
    and total_orders[0] == 1
):

    ax.annotate(
        "100% — 1 order",
        xy=(
            months[0],
            late_share[0]
        ),
        xytext=(35, -5),
        textcoords="offset points",
        ha="left",
        fontsize=9,
        fontweight="bold"
    )


# ============================================================
# HIGHLIGHT IMPORTANT SPIKES
# ============================================================

for i, value in enumerate(late_share):

    # Skip September 2016 single-order outlier
    if i == 0:
        continue

    if value >= 10:

        ax.scatter(
            months[i],
            value,
            s=100,
            zorder=5,
            edgecolor="white",
            linewidth=2
        )

        ax.annotate(
            f"{value:.2f}%",
            (
                months[i],
                value
            ),
            xytext=(0, 12),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            fontweight="bold"
        )


# ============================================================
# HIGHEST NORMAL-VOLUME MONTH
# ============================================================

if len(late_share) > 1:

    normal_values = late_share[1:]

    highest_index = (
        normal_values.index(
            max(normal_values)
        ) + 1
    )

    highest_month = months[highest_index]

    highest_value = late_share[highest_index]

    ax.annotate(
        "Peak",
        xy=(
            highest_month,
            highest_value
        ),
        xytext=(0, 28),
        textcoords="offset points",
        ha="center",
        fontsize=9,
        fontweight="bold"
    )


# ============================================================
# TITLE
# ============================================================

ax.set_title(
    "Late Delivery Share by Month",
    fontsize=19,
    fontweight="bold",
    loc="left",
    pad=25
)


# ============================================================
# SUBTITLE
# ============================================================

ax.text(
    0,
    1.02,
    "Share of delivered orders that arrived after the estimated delivery date",
    transform=ax.transAxes,
    fontsize=10,
    alpha=0.65
)


# ============================================================
# AXIS LABELS
# ============================================================

ax.set_xlabel(
    "Purchase Month",
    fontsize=10,
    labelpad=10
)

ax.set_ylabel(
    "Late Delivery Share (%)",
    fontsize=10,
    labelpad=10
)


# ============================================================
# X-AXIS
# ============================================================

plt.xticks(
    rotation=45,
    ha="right",
    fontsize=9
)


# ============================================================
# Y-AXIS
# ============================================================

ax.set_ylim(
    0,
    105
)

ax.set_yticks([
    0,
    20,
    40,
    60,
    80,
    100
])

ax.set_yticklabels([
    "0%",
    "20%",
    "40%",
    "60%",
    "80%",
    "100%"
])


# ============================================================
# GRID
# ============================================================

ax.grid(
    axis="y",
    linestyle="--",
    linewidth=0.8,
    alpha=0.25
)


# ============================================================
# REMOVE EXTRA BORDERS
# ============================================================

ax.spines["top"].set_visible(False)

ax.spines["right"].set_visible(False)

ax.spines["left"].set_alpha(0.2)

ax.spines["bottom"].set_alpha(0.2)


# ============================================================
# SAVE GRAPH
# ============================================================

plt.tight_layout()

plt.savefig(
    "outputs/part_b_late_share_by_month.png",
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

plt.show()


# ============================================================
# B3 - AVERAGE REVIEW SCORE: LATE VS ON-TIME
# ============================================================

review_comparison = duckdb.sql("""
    SELECT

        CASE
            WHEN days_late > 0
            THEN 'Late'
            ELSE 'On-Time'
        END AS delivery_status,

        ROUND(
            AVG(review_score),
            2
        ) AS average_review_score

    FROM final_orders

    WHERE review_score IS NOT NULL

    GROUP BY
        CASE
            WHEN days_late > 0
            THEN 'Late'
            ELSE 'On-Time'
        END

    ORDER BY delivery_status
""")


review_rows = review_comparison.fetchall()

formatted_review_rows = []


for row in review_rows:

    formatted_review_rows.append([
        row[0],
        f"{row[1]:.2f}"
    ])


print(
    "\n============================================================"
)

print(
    "B3 - AVERAGE REVIEW SCORE: LATE VS ON-TIME"
)

print(
    "============================================================"
)


print_box_table(
    [
        "delivery_status",
        "average_review_score"
    ],
    formatted_review_rows
)


# ============================================================
# B4 - ORDERS MORE THAN 7 DAYS LATE
# ============================================================

more_than_7_days = duckdb.sql("""
    SELECT

        COUNT(*) AS orders_over_7_days_late,

        ROUND(
            AVG(review_score),
            2
        ) AS average_review_score

    FROM final_orders

    WHERE days_late > 7
      AND review_score IS NOT NULL
""")


more_than_7_row = more_than_7_days.fetchone()


print(
    "\n============================================================"
)

print(
    "B4 - AVERAGE REVIEW SCORE FOR ORDERS MORE THAN 7 DAYS LATE"
)

print(
    "============================================================"
)


print_box_table(
    [
        "orders_over_7_days_late",
        "average_review_score"
    ],
    [[
        more_than_7_row[0],
        f"{more_than_7_row[1]:.2f}"
    ]]
)


# ============================================================
# COMPLETE
# ============================================================

print(
    "\nPart B completed successfully."
)