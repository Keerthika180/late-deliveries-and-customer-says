import duckdb
import csv
import matplotlib.pyplot as plt


# =========================================================
# 1. Connect to DuckDB
# =========================================================

con = duckdb.connect()


# =========================================================
# 2. Join classified reviews with orders
# =========================================================

query = """
SELECT
    r.review_id,
    r.order_id,
    c.category,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date

FROM read_csv_auto('outputs/part_c_results.csv') c

JOIN read_csv_auto('data/olist_order_reviews_dataset.csv') r
    ON c.review_id = r.review_id

LEFT JOIN read_csv_auto('data/olist_orders_dataset.csv') o
    ON r.order_id = o.order_id
"""

rows = con.execute(query).fetchall()

columns = [
    desc[0]
    for desc in con.description
]


# =========================================================
# 3. Convert to dictionaries
# =========================================================

records = [
    dict(zip(columns, row))
    for row in rows
]


# =========================================================
# 4. Required themes
# =========================================================

themes = [
    "late or not received",
    "wrong or missing item",
    "product quality",
    "good experience",
    "other"
]


# =========================================================
# 5. Normalize LLM category names
# =========================================================

def normalize_category(category):

    if category is None:
        return "other"

    category = category.strip().lower()

    if category in [
        "late or not received",
        "late/not received"
    ]:
        return "late or not received"

    if category in [
        "wrong or missing item",
        "wrong/missing item"
    ]:
        return "wrong or missing item"

    if category == "product quality":
        return "product quality"

    if category == "good experience":
        return "good experience"

    return "other"


# =========================================================
# 6. Determine Late / On-Time / Unknown
# =========================================================

timing_records = []

for row in records:

    delivered = row["order_delivered_customer_date"]
    estimated = row["order_estimated_delivery_date"]

    if delivered is None or estimated is None:

        timing = "Unknown"

    elif delivered > estimated:

        timing = "Late"

    else:

        timing = "On-Time"

    timing_records.append({
        "review_id": row["review_id"],
        "category": normalize_category(row["category"]),
        "timing": timing
    })


# =========================================================
# 7. Count themes
# =========================================================

counts = {
    "Late": {
        theme: 0
        for theme in themes
    },

    "On-Time": {
        theme: 0
        for theme in themes
    }
}


timing_counts = {
    "Late": 0,
    "On-Time": 0,
    "Unknown": 0
}


for row in timing_records:

    timing = row["timing"]
    category = row["category"]

    timing_counts[timing] += 1

    if timing in ["Late", "On-Time"]:
        counts[timing][category] += 1


# =========================================================
# 8. Calculate percentages
# =========================================================

late_percentages = {}
ontime_percentages = {}


for theme in themes:

    late_count = counts["Late"][theme]
    ontime_count = counts["On-Time"][theme]

    late_percentages[theme] = (
        late_count / timing_counts["Late"] * 100
        if timing_counts["Late"] > 0
        else 0
    )

    ontime_percentages[theme] = (
        ontime_count / timing_counts["On-Time"] * 100
        if timing_counts["On-Time"] > 0
        else 0
    )


# =========================================================
# 9. Print theme mix
# =========================================================

print()
print("=" * 70)
print("THEME MIX: LATE VS ON-TIME")
print("=" * 70)

print(
    f"{'Theme':35s}"
    f"{'Late':>15s}"
    f"{'On-Time':>15s}"
)

print("-" * 70)

for theme in themes:

    print(
        f"{theme:35s}"
        f"{late_percentages[theme]:>14.2f}%"
        f"{ontime_percentages[theme]:>14.2f}%"
    )


# =========================================================
# 10. Print review counts
# =========================================================

print()
print("=" * 40)
print("REVIEW COUNTS")
print("=" * 40)

print(
    f"{'Timing':20s}"
    f"{'Reviews':>10s}"
)

print("-" * 40)

for timing in ["Late", "On-Time", "Unknown"]:

    print(
        f"{timing:20s}"
        f"{timing_counts[timing]:>10d}"
    )

print("-" * 40)


# =========================================================
# 11. Save theme mix CSV
# =========================================================

with open(
    "outputs/part_c_theme_mix_late_vs_ontime.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "theme",
        "late_percentage",
        "on_time_percentage"
    ])

    for theme in themes:

        writer.writerow([
            theme,
            round(late_percentages[theme], 2),
            round(ontime_percentages[theme], 2)
        ])


print()
print("Saved: part_c_theme_mix_late_vs_ontime.csv")


# =========================================================
# 12. Create clean presentation chart
# =========================================================

late_values = [
    late_percentages[theme]
    for theme in themes
]

ontime_values = [
    ontime_percentages[theme]
    for theme in themes
]


# Same theme = same color in both bars
theme_colors = [
    "#4C78A8",  # Late / not received
    "#F58518",  # Wrong / missing item
    "#54A24B",  # Product quality
    "#E45756",  # Good experience
    "#B279A2"   # Other
]


fig, ax = plt.subplots(
    figsize=(11, 7)
)


# ---------------------------------------------------------
# Draw stacked bars
# ---------------------------------------------------------

bottom_late = 0
bottom_ontime = 0


for i, theme in enumerate(themes):

    ax.bar(
        "Late",
        late_values[i],
        bottom=bottom_late,
        color=theme_colors[i],
        width=0.55,
        label=theme
    )

    ax.bar(
        "On-Time",
        ontime_values[i],
        bottom=bottom_ontime,
        color=theme_colors[i],
        width=0.55
    )

    # Add percentage labels only when large enough
    if late_values[i] >= 5:

        ax.text(
            0,
            bottom_late + late_values[i] / 2,
            f"{late_values[i]:.1f}%",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold"
        )

    if ontime_values[i] >= 5:

        ax.text(
            1,
            bottom_ontime + ontime_values[i] / 2,
            f"{ontime_values[i]:.1f}%",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold"
        )

    bottom_late += late_values[i]
    bottom_ontime += ontime_values[i]


# =========================================================
# 13. Chart formatting
# =========================================================

ax.set_title(
    "Review Theme Mix: Late vs On-Time Orders",
    fontsize=18,
    fontweight="bold",
    pad=18
)

ax.set_ylabel(
    "Share of Reviews (%)",
    fontsize=11
)

ax.set_xlabel(
    "Delivery Timing",
    fontsize=11
)


ax.set_ylim(0, 100)

ax.set_xticks([0, 1])

ax.set_xticklabels(
    ["Late", "On-Time"],
    fontsize=11,
    fontweight="bold"
)


# Clean horizontal grid
ax.yaxis.grid(
    True,
    linestyle="--",
    alpha=0.25
)

ax.set_axisbelow(True)


# Remove unnecessary borders
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)


# Legend
ax.legend(
    title="Review Theme",
    loc="upper center",
    bbox_to_anchor=(0.5, -0.10),
    ncol=2,
    frameon=False,
    fontsize=10,
    title_fontsize=10
)


# Add sample-size information
ax.text(
    0,
    -0.16,
    f"n = {timing_counts['Late']} reviews",
    transform=ax.transAxes,
    ha="center",
    fontsize=10
)

ax.text(
    1,
    -0.16,
    f"n = {timing_counts['On-Time']} reviews",
    transform=ax.transAxes,
    ha="center",
    fontsize=10
)


plt.tight_layout()


# =========================================================
# 14. Save high-quality chart
# =========================================================

plt.savefig(
    "outputs/part_c_theme_mix_late_vs_ontime.png",
    dpi=300,
    bbox_inches="tight"
)


plt.show()


print(
    "Saved: part_c_theme_mix_late_vs_ontime.png"
)