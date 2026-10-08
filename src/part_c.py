import duckdb
import os
import json
import time
import csv

from dotenv import load_dotenv
from groq import Groq


# ==========================================
# PART C - SELECT 200 REVIEWS
# ==========================================

reviews = duckdb.read_csv(
    "data/olist_order_reviews_dataset.csv"
)

sample_reviews = duckdb.sql("""
    SELECT
        review_id,
        order_id,
        review_score,
        review_comment_message
    FROM reviews
    WHERE review_comment_message IS NOT NULL
      AND TRIM(review_comment_message) <> ''
    LIMIT 200
""")

print("\nSelected Reviews:")
print("Number of reviews:", len(sample_reviews))


# ==========================================
# GROQ API SETUP
# ==========================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("\nGroq API key was not found.")
    exit()

print("\nGroq API key loaded successfully.")

client = Groq(api_key=api_key)


# ==========================================
# CONVERT REVIEWS TO LIST
# ==========================================

reviews_list = sample_reviews.fetchall()


# ==========================================
# PROCESS REVIEWS IN BATCHES
# ==========================================

all_results = []
raw_outputs = []

# Process 5 reviews at a time
batch_size = 5

for start in range(0, len(reviews_list), batch_size):

    batch = reviews_list[start:start + batch_size]

    print(
        f"\nProcessing reviews "
        f"{start + 1} to {start + len(batch)}..."
    )

    # --------------------------------------
    # Prepare reviews for the prompt
    # --------------------------------------

    review_text = ""

    for i, review in enumerate(batch, start=1):

        review_text += f"""
Review {i}
Review ID: {review[0]}
Review: {review[3]}
"""


    # --------------------------------------
    # Prompt
    # --------------------------------------

    prompt = f"""
Classify each customer review into exactly ONE
of these five categories:

1. late/not received
2. wrong/missing item
3. product quality
4. good experience
5. other

For every review, also provide a one-line
English summary.

Important rules:

- Use exactly ONE category per review.
- Do not create new categories.
- The category must be the exact category name.
- Do NOT return category numbers.
- Keep the summary short.
- The summary must be in English.
- Return ONLY valid JSON.
- Do not use markdown.

The category must be exactly one of:

late/not received
wrong/missing item
product quality
good experience
other

Return exactly this JSON format:

[
  {{
    "review_id": "review id",
    "category": "exact category name",
    "summary": "one-line English summary"
  }}
]

Reviews:

{review_text}
"""


    # ======================================
    # SEND REQUEST TO GROQ
    # ======================================

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        raw_response = response.choices[0].message.content


        # ----------------------------------
        # Save raw response
        # ----------------------------------

        raw_outputs.append({
            "batch_start": start + 1,
            "batch_end": start + len(batch),
            "raw_output": raw_response
        })


        # ----------------------------------
        # Convert response to JSON
        # ----------------------------------

        results = json.loads(raw_response)

        all_results.extend(results)

        print(
            f"Completed batch "
            f"{start + 1} to {start + len(batch)}"
        )


    except Exception as e:

        print(
            f"Error processing batch "
            f"{start + 1} to {start + len(batch)}:"
        )

        print(e)


    # Small pause between API requests
    time.sleep(1)


# ==========================================
# SAVE CLASSIFIED RESULTS
# ==========================================

with open(
    "part_c_results.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "review_id",
            "category",
            "summary"
        ]
    )

    writer.writeheader()
    writer.writerows(all_results)


# ==========================================
# SAVE RAW GROQ OUTPUTS
# ==========================================

with open(
    "part_c_raw_outputs.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        raw_outputs,
        file,
        ensure_ascii=False,
        indent=2
    )


# ==========================================
# FINAL CHECK
# ==========================================

print("\n==========================================")
print("Classification completed.")
print("==========================================")

print(
    "Number of classified reviews:",
    len(all_results)
)

print("\nCategory counts:")

if all_results:

    category_counts = {}

    for result in all_results:

        category = result["category"]

        category_counts[category] = (
            category_counts.get(category, 0) + 1
        )

    for category, count in category_counts.items():

        print(
            f"{category}: {count}"
        )

else:

    print("No reviews were classified.")


print("\nFiles created:")
print("1. part_c_results.csv")
print("2. part_c_raw_outputs.json")