import json
import os

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=ENV_FILE, override=True)


# ============================================================
# GROQ API KEY
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# AI QUESTION UNDERSTANDING
# ============================================================

def understand_question(
    question,
    columns,
    numeric_columns,
    categorical_columns
):

    # --------------------------------------------------------
    # Detect likely date columns from column names
    # --------------------------------------------------------

    date_keywords = [
        "date",
        "time",
        "year",
        "month",
        "day",
        "timestamp"
    ]

    date_columns = []

    for col in columns:

        col_lower = col.lower()

        if any(
            keyword in col_lower
            for keyword in date_keywords
        ):
            date_columns.append(col)


    system_prompt = f"""
You are an expert AI Data Analyst.

Your job is to convert a user's natural-language
question into a structured JSON analysis plan.

AVAILABLE COLUMNS:
{columns}

NUMERIC COLUMNS:
{numeric_columns}

CATEGORICAL COLUMNS:
{categorical_columns}

LIKELY DATE/TIME COLUMNS:
{date_columns}


============================================================
SUPPORTED OPERATIONS
============================================================

1. total
2. average
3. minimum
4. maximum
5. count
6. unique_count
7. group_by
8. top_n
9. bottom_n
10. correlation
11. date_trend


============================================================
GENERAL RULES
============================================================

1. Never invent column names.

2. Use ONLY columns from AVAILABLE COLUMNS.

3. Return a plan that can be executed by Pandas.

4. For normal grouping, use group_by.

5. For questions involving time trends, months,
   years, quarters, weeks or dates, use date_trend.

6. If a question says "over time", "trend",
   "by month", "monthly", "by year", "yearly",
   "by quarter", "quarterly", "by week",
   "weekly", or "by date", use date_trend.

7. Choose the correct numeric measure.

8. Choose the most appropriate date column.

9. Never invent a date column.

10. Return ONLY the JSON object.


============================================================
TOTAL
============================================================

Question:

"What is the total sales?"

Return:

{{
    "operation": "total",
    "column": "Sales",
    "group_by": null,
    "aggregation": null,
    "n": null,
    "date_column": null,
    "granularity": null
}}


============================================================
AVERAGE
============================================================

Question:

"What is the average sales?"

Return:

{{
    "operation": "average",
    "column": "Sales",
    "group_by": null,
    "aggregation": null,
    "n": null,
    "date_column": null,
    "granularity": null
}}


============================================================
MINIMUM
============================================================

Question:

"What is the minimum profit?"

Return:

{{
    "operation": "minimum",
    "column": "Profit",
    "group_by": null,
    "aggregation": null,
    "n": null,
    "date_column": null,
    "granularity": null
}}


============================================================
MAXIMUM
============================================================

Question:

"What is the maximum profit?"

Return:

{{
    "operation": "maximum",
    "column": "Profit",
    "group_by": null,
    "aggregation": null,
    "n": null,
    "date_column": null,
    "granularity": null
}}


============================================================
COUNT
============================================================

Question:

"How many orders are there?"

Return:

{{
    "operation": "count",
    "column": "Order_ID",
    "group_by": null,
    "aggregation": null,
    "n": null,
    "date_column": null,
    "granularity": null
}}


============================================================
UNIQUE COUNT
============================================================

Question:

"How many unique customers are there?"

Return:

{{
    "operation": "unique_count",
    "column": "Customer",
    "group_by": null,
    "aggregation": null,
    "n": null,
    "date_column": null,
    "granularity": null
}}


============================================================
GROUP BY
============================================================

Question:

"What are the total sales by country?"

Return:

{{
    "operation": "group_by",
    "column": "Sales",
    "group_by": "Country",
    "aggregation": "sum",
    "n": null,
    "date_column": null,
    "granularity": null
}}


============================================================
AVERAGE GROUP BY
============================================================

Question:

"What is the average sales by category?"

Return:

{{
    "operation": "group_by",
    "column": "Sales",
    "group_by": "Category",
    "aggregation": "mean",
    "n": null,
    "date_column": null,
    "granularity": null
}}


============================================================
TOP N
============================================================

Question:

"What are the top 5 products by sales?"

Return:

{{
    "operation": "top_n",
    "column": "Sales",
    "group_by": "Product",
    "aggregation": null,
    "n": 5,
    "date_column": null,
    "granularity": null
}}


============================================================
BOTTOM N
============================================================

Question:

"What are the bottom 5 products by sales?"

Return:

{{
    "operation": "bottom_n",
    "column": "Sales",
    "group_by": "Product",
    "aggregation": null,
    "n": 5,
    "date_column": null,
    "granularity": null
}}


============================================================
CORRELATION
============================================================

Question:

"What is the relationship between sales and profit?"

Return:

{{
    "operation": "correlation",
    "column": "Sales",
    "group_by": "Profit",
    "aggregation": null,
    "n": null,
    "date_column": null,
    "granularity": null
}}


============================================================
DATE TREND
============================================================

Question:

"Show sales trend over time."

Return:

{{
    "operation": "date_trend",
    "column": "Sales",
    "group_by": null,
    "aggregation": "sum",
    "n": null,
    "date_column": "Order_Date",
    "granularity": "month"
}}


============================================================
DATE TREND BY MONTH
============================================================

Question:

"What were the total sales each month?"

Return:

{{
    "operation": "date_trend",
    "column": "Sales",
    "group_by": null,
    "aggregation": "sum",
    "n": null,
    "date_column": "Order_Date",
    "granularity": "month"
}}


============================================================
DATE TREND BY YEAR
============================================================

Question:

"Show profit by year."

Return:

{{
    "operation": "date_trend",
    "column": "Profit",
    "group_by": null,
    "aggregation": "sum",
    "n": null,
    "date_column": "Order_Date",
    "granularity": "year"
}}


============================================================
DATE TREND BY QUARTER
============================================================

Question:

"Show sales by quarter."

Return:

{{
    "operation": "date_trend",
    "column": "Sales",
    "group_by": null,
    "aggregation": "sum",
    "n": null,
    "date_column": "Order_Date",
    "granularity": "quarter"
}}


============================================================
DATE TREND BY WEEK
============================================================

Question:

"Show weekly sales."

Return:

{{
    "operation": "date_trend",
    "column": "Sales",
    "group_by": null,
    "aggregation": "sum",
    "n": null,
    "date_column": "Order_Date",
    "granularity": "week"
}}


============================================================
DATE TREND BY DATE
============================================================

Question:

"Show sales by date."

Return:

{{
    "operation": "date_trend",
    "column": "Sales",
    "group_by": null,
    "aggregation": "sum",
    "n": null,
    "date_column": "Order_Date",
    "granularity": "day"
}}


============================================================
AVERAGE BY MONTH
============================================================

Question:

"What is the average sales by month?"

Return:

{{
    "operation": "date_trend",
    "column": "Sales",
    "group_by": null,
    "aggregation": "mean",
    "n": null,
    "date_column": "Order_Date",
    "granularity": "month"
}}


============================================================
HIGHEST MONTH
============================================================

Question:

"Which month had the highest sales?"

Return:

{{
    "operation": "date_trend",
    "column": "Sales",
    "group_by": null,
    "aggregation": "sum",
    "n": null,
    "date_column": "Order_Date",
    "granularity": "month"
}}


============================================================
LOWEST MONTH
============================================================

Question:

"Which month had the lowest profit?"

Return:

{{
    "operation": "date_trend",
    "column": "Profit",
    "group_by": null,
    "aggregation": "sum",
    "n": null,
    "date_column": "Order_Date",
    "granularity": "month"
}}


============================================================
IMPORTANT
============================================================

For date questions:

"by date"
= granularity "day"

"daily"
= granularity "day"

"by week"
= granularity "week"

"weekly"
= granularity "week"

"by month"
= granularity "month"

"monthly"
= granularity "month"

"by quarter"
= granularity "quarter"

"quarterly"
= granularity "quarter"

"by year"
= granularity "year"

"yearly"
= granularity "year"

"over time"
= choose the most appropriate time granularity,
usually "month" when the dataset contains enough dates.


Return ONLY valid JSON.
"""


    # ========================================================
    # GROQ REQUEST
    # ========================================================

    response = client.chat.completions.create(

        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": question
            }
        ],

        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "data_analysis_plan",
                "strict": True,
                "schema": {
                    "type": "object",

                    "properties": {

                        "operation": {
                            "type": "string",
                            "enum": [
                                "total",
                                "average",
                                "minimum",
                                "maximum",
                                "count",
                                "unique_count",
                                "group_by",
                                "top_n",
                                "bottom_n",
                                "correlation",
                                "date_trend"
                            ]
                        },

                        "column": {
                            "type": [
                                "string",
                                "null"
                            ]
                        },

                        "group_by": {
                            "type": [
                                "string",
                                "null"
                            ]
                        },

                        "aggregation": {
                            "type": [
                                "string",
                                "null"
                            ],
                            "enum": [
                                "sum",
                                "mean",
                                "min",
                                "max",
                                "count",
                                None
                            ]
                        },

                        "n": {
                            "type": [
                                "integer",
                                "null"
                            ]
                        },

                        "date_column": {
                            "type": [
                                "string",
                                "null"
                            ]
                        },

                        "granularity": {
                            "type": [
                                "string",
                                "null"
                            ],
                            "enum": [
                                "day",
                                "week",
                                "month",
                                "quarter",
                                "year",
                                None
                            ]
                        }
                    },

                    "required": [
                        "operation",
                        "column",
                        "group_by",
                        "aggregation",
                        "n",
                        "date_column",
                        "granularity"
                    ],

                    "additionalProperties": False
                }
            }
        },

        temperature=0
    )


    content = response.choices[0].message.content

    result = json.loads(content)

    return result


# ============================================================
# AI BUSINESS INSIGHT
# ============================================================

def generate_insight(
    question,
    analysis_result
):

    prompt = f"""
You are a professional business data analyst.

USER QUESTION:
{question}

DATA ANALYSIS RESULT:
{analysis_result}

Generate a concise business insight.

IMPORTANT RULES:

1. Only make claims supported by the provided data.

2. Do not invent causes.

3. Do not assume customer behavior.

4. Do not assume market conditions.

5. Do not invent information that is not present
   in the analysis result.

6. Mention highest and lowest values when applicable.

7. Mention important differences when supported
   by the data.

8. Recommendations must clearly be recommendations.

9. Keep the response between 3 and 5 sentences.

10. Return plain text only.

11. Do not use markdown headings.

12. Do not use bullet points.
"""


    response = client.chat.completions.create(

        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "system",
                "content": prompt
            }
        ],

        temperature=0.2
    )


    return response.choices[0].message.content