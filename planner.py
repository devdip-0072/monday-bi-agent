import os
import json
import yaml
import re
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

from logger import log_gemini_call, log_plan, log_error

load_dotenv()

# =========================
# API KEY HANDLING
# =========================

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        raise ValueError("GEMINI_API_KEY not found in env or Streamlit secrets")

client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# =========================
# LOAD SCHEMA
# =========================

with open("schema.yml", "r") as f:
    schemas = yaml.safe_load(f)

# =========================
# NORMALIZATION
# =========================

def normalize_key(key):
    key = str(key).lower().strip()
    key = re.sub(r"[^\w\s]", "", key)
    key = key.replace(" ", "_")
    return key

# =========================
# BUILD SCHEMA MAP
# =========================

schema_map = {}

for board, cols in schemas.items():
    schema_map[board] = {}

    for col in cols.keys():
        schema_map[board][normalize_key(col)] = col

# =========================
# BUILD SCHEMA TEXT FOR LLM
# =========================

schema_text = ""

for board, cols in schemas.items():

    schema_text += f"{board}:\n"

    for col in cols.keys():
        schema_text += f"- {col}\n"

# =========================
# SAFE JSON PARSER
# =========================

def safe_parse_json(text):

    # remove markdown
    text = re.sub(r"```json|```", "", text).strip()

    # extract JSON block
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:
        text = match.group()

    text = text.replace("'", '"')
    text = re.sub(r",(\s*[\]}])", r"\1", text)

    try:
        return json.loads(text)
    except Exception:
        return {
            "boards": [],
            "metrics": [],
            "filters": [],
            "group_by": []
        }

# =========================
# COLUMN VALIDATION
# =========================

def validate_column(board, column):

    if not column:
        return None

    norm = normalize_key(column)

    if board not in schema_map:
        return None

    # exact match
    if norm in schema_map[board]:
        return norm

    # fuzzy match
    for key in schema_map[board]:
        if norm in key or key in norm:
            return key

    return None

# =========================
# FIX PLAN
# =========================

def fix_plan(plan):

    fixed_metrics = []

    for metric in plan.get("metrics", []):

        board = metric.get("board")
        column = metric.get("column")

        valid = validate_column(board, column)

        if valid:
            metric["column"] = valid
            fixed_metrics.append(metric)

    plan["metrics"] = fixed_metrics

    fixed_filters = []

    for f in plan.get("filters", []):

        board = f.get("board")
        column = f.get("column")

        valid = validate_column(board, column)

        if valid:
            f["column"] = valid
            fixed_filters.append(f)

    plan["filters"] = fixed_filters

    fixed_group = []

    for item in plan.get("group_by", []):

        board = item.get("board")
        column = item.get("column")

        valid = validate_column(board, column)

        if valid:
            fixed_group.append({
                "board": board,
                "column": valid
            })

    plan["group_by"] = fixed_group

    return plan

# =========================
# PLAN VALIDATION
# =========================

def validate_plan(plan):

    if not isinstance(plan.get("boards"), list):
        plan["boards"] = []

    if not isinstance(plan.get("metrics"), list):
        plan["metrics"] = []

    if not isinstance(plan.get("filters"), list):
        plan["filters"] = []

    if not isinstance(plan.get("group_by"), list):
        plan["group_by"] = []

    return plan

# =========================
# MAIN PLANNER
# =========================

def create_plan_llm(user_question):

    try:

        log_gemini_call(user_question)

        prompt = f"""
You are an expert Business Intelligence planning agent.

Convert the user question into a structured analytics plan.

=====================
AVAILABLE SCHEMA
=====================

{schema_text}

=====================
USER QUESTION
=====================

{user_question}

=====================
OUTPUT FORMAT
=====================

Return JSON ONLY.

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

    plan = validate_plan(plan)

    plan = fix_plan(plan)

    log_plan(plan)

    return plan