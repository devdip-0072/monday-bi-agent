import os
import json
import yaml
import re
from openai import OpenAI
from dotenv import load_dotenv

# Logger
from logger import log_gemini_call, log_plan, log_error

load_dotenv()

# =================================
# Gemini Client
# =================================

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# =================================
# Load Schema
# =================================

with open("schema.yml", "r") as f:
    schemas = yaml.safe_load(f)


# =================================
# Column Normalization
# =================================

def normalize_key(key):
    key = str(key).lower().strip()
    key = re.sub(r"[^\w\s]", "", key)
    key = key.replace(" ", "_")
    return key


# =================================
# Build Normalized Schema Map
# =================================

schema_map = {}

for board, cols in schemas.items():

    schema_map[board] = {}

    for col in cols.keys():
        schema_map[board][normalize_key(col)] = col


# =================================
# Safe JSON Parse
# =================================

def safe_parse_json(text):

    text = re.sub(r"```json|```", "", text).strip()
    text = text.replace("'", '"')
    text = re.sub(r",(\s*[\]}])", r"\1", text)

    try:
        return json.loads(text)
    except:
        return {
            "boards": [],
            "metrics": [],
            "filters": [],
            "group_by": []
        }


# =================================
# Validate Columns Against Schema
# =================================

def validate_column(board, column):

    norm = normalize_key(column)

    if board not in schema_map:
        return None

    if norm in schema_map[board]:
        return norm

    return None


# =================================
# Fix Plan Columns
# =================================

def fix_plan(plan):

    # Fix metrics
    for metric in plan.get("metrics", []):

        board = metric.get("board")
        column = metric.get("column")

        valid = validate_column(board, column)

        if valid:
            metric["column"] = valid
        else:
            metric["column"] = None


    # Fix filters
    for f in plan.get("filters", []):

        board = f.get("board")
        column = f.get("column")

        valid = validate_column(board, column)

        if valid:
            f["column"] = valid
        else:
            f["column"] = None


    # Fix group_by
    fixed_group = []

    for col in plan.get("group_by", []):

        norm = normalize_key(col)

        for board in schema_map:

            if norm in schema_map[board]:
                fixed_group.append(norm)
                break

    plan["group_by"] = fixed_group

    return plan


# =================================
# Generate LLM Plan
# =================================

def create_plan_llm(user_question):

    try:

        log_gemini_call(user_question)

        schema_text = ""

        for board, cols in schemas.items():

            schema_text += f"{board}:\n"

            for col in cols.keys():
                schema_text += f"- {col}\n"


        prompt = f"""
You are an expert Business Intelligence planning agent.

Your job is to convert a user question into a structured analytics plan.

You MUST strictly use the schema provided below. 
DO NOT invent columns, boards, or metrics that are not present in the schema.

=====================
AVAILABLE SCHEMA
=====================

{schema_text}

=====================
USER QUESTION
=====================

{user_question}

=====================
TASK
=====================

Analyze the user question and generate a JSON analytics plan that includes:

1. Which board(s) must be used
2. Which metric(s) should be calculated
3. Which filters should be applied
4. Which columns should be used for grouping

=====================
OUTPUT FORMAT
=====================

Return JSON ONLY. No explanation.

{{
"boards": ["board_name"],

"metrics": [
  {{
    "board": "board_name",
    "type": "sum | count | average | min | max",
    "column": "column_name"
  }}
],

"filters": [
  {{
    "board": "board_name",
    "column": "column_name",
    "value": "value"
  }}
],

"group_by": [
  {{
    "board": "board_name",
    "column": "column_name"
  }}
]
}}

=====================
PLANNING RULES
=====================

1. **Schema Grounding**
- Only use boards and columns present in the schema.
- If the user mentions a concept similar to a column name, map it to the closest column.

2. **Metric Selection**
- Use SUM for revenue, value, billing, amount, collected amount, etc.
- Use COUNT when user asks for number of deals, projects, work orders.
- Use AVERAGE for average metrics.
- MIN/MAX only for date or range queries.

3. **Column Type Awareness**
- Numeric columns → allowed for sum, average, min, max.
- Categorical columns → allowed for group_by.
- Date columns → allowed for filters and grouping.

4. **Filters**
Extract filters from the user question such as:

Examples:
"completed work orders" → filter Execution Status = Completed  
"open deals" → filter Deal Status = Open  
"this month" → filter using relevant date column  
"sector telecom" → filter Sector = Telecom

5. **Grouping**
Use group_by when user asks:
- "by sector"
- "by owner"
- "per customer"
- "per month"
- "per stage"

6. **Board Selection**

Use:
Deal_funnel → pipeline / deals / deal value / stages  
Work_order_Tracker → billing / collection / work orders / execution

7. **Multiple Boards**
If the question requires both deals and work orders, include both boards.

8. **Ambiguity Handling**
If metric is implied but not stated:
- revenue / billing → SUM
- number of deals → COUNT

9. **Never invent columns**

Bad:
"revenue_amount"

Good:
"Collected Amount in Rupees (Incl of GST.) (Masked)"

=====================
EXAMPLES
=====================

Example 1:

User Question:
Total collected amount for completed work orders

Output:

{{
"boards": ["Work_order_Tracker"],
"metrics": [
  {{
    "board": "Work_order_Tracker",
    "type": "sum",
    "column": "Collected Amount in Rupees (Incl of GST.) (Masked)"
  }}
],
"filters": [
  {{
    "board": "Work_order_Tracker",
    "column": "Execution Status",
    "value": "Completed"
  }}
],
"group_by": []
}}

Example 2:

User Question:
Total deal value by sector

Output:

{{
"boards": ["Deal_funnel"],
"metrics": [
  {{
    "board": "Deal_funnel",
    "type": "sum",
    "column": "Masked Deal value"
  }}
],
"filters": [],
"group_by": [
  {{
    "board": "Deal_funnel",
    "column": "Sector/service"
  }}
]
}}

Remember:
Return JSON ONLY.
Do not explain anything.
"""


        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        text = response.choices[0].message.content

        plan = safe_parse_json(text)

    except Exception as e:

        log_error(str(e))

        plan = {}


    # Ensure keys exist
    plan.setdefault("boards", [])
    plan.setdefault("metrics", [])
    plan.setdefault("filters", [])
    plan.setdefault("group_by", [])


    # Fix invalid columns
    plan = fix_plan(plan)


    # Log planner output
    log_plan(plan)

    return plan

