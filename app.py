import streamlit as st
import os
from dotenv import load_dotenv

from planner import create_plan_llm
from monday_api import fetch_board_items
from normalizer import normalize_deals, normalize_workorders
from analytics_engine import run_analytics

load_dotenv()

DEALS_BOARD_ID = os.getenv("DEALS_BOARD_ID")
WORK_ORDERS_BOARD_ID = os.getenv("WORK_ORDERS_BOARD_ID")

st.title("📊 Monday BI Agent")


question = st.text_input("Ask your business question:")

if st.button("Run") and question.strip():

    st.subheader("🧠 LLM Plan")

   
    # 2. GENERATE PLAN FROM LLM
    plan = create_plan_llm(question)
    st.json(plan)

    boards = plan.get("boards", [])
    if not boards:
        st.warning("No boards detected in the plan. Refine your question.")
        st.stop()


    # 3. FETCH DATA FOR ALL BOARDS
   
    data_map = {}
    for board in boards:
        board_lower = board.lower()
        if board_lower in ["deals", "deal_funnel"]:
            if not DEALS_BOARD_ID:
                st.error("DEALS_BOARD_ID not set in .env")
                continue
            raw = fetch_board_items(DEALS_BOARD_ID)
            data_map[board] = normalize_deals(raw)

        elif board_lower in ["work orders", "work_order_tracker"]:
            if not WORK_ORDERS_BOARD_ID:
                st.error("WORK_ORDERS_BOARD_ID not set in .env")
                continue
            raw = fetch_board_items(WORK_ORDERS_BOARD_ID)
            data_map[board] = normalize_workorders(raw)

        else:
            st.warning(f"Unknown board: {board}")

    if not data_map:
        st.warning("No board data fetched.")
        st.stop()

    st.write("### Raw Records per Board")
    for board, rows in data_map.items():
        st.write(f"{board}: {len(rows)} rows")
    # 4. EXTRACT FILTERS, METRICS, GROUP_BY

    filters_map = {}
    metrics_map = {}
    group_by_map = {}

    for f in plan.get("filters", []):
        board = f.get("board")
        column = f.get("column")
        value = f.get("value")
        if board and column:
            filters_map.setdefault(board, {})[column] = value

    for m in plan.get("metrics", []):
        board = m.get("board")
        metric_type = m.get("type")
        field = m.get("column")
        if board and metric_type and field:
            metrics_map.setdefault(board, []).append({"type": metric_type, "field": field})

    for board in plan.get("boards", []):
        gb_cols = plan.get("group_by", [])
        if gb_cols:
            group_by_map[board] = gb_cols

 
    # 5. RUN ANALYTICS PIPELINE

    results = run_analytics(
        data_map,
        filters_map=filters_map,
        metrics_map=metrics_map,
        group_by_map=group_by_map
    )

    st.subheader("📈 Results")
    st.json(results)


    # 6. BUSINESS SUMMARY
   
    st.subheader("📝 Business Summary")
    st.write(f"**Question:** {question}")

    if results["results"]:
        st.write("**Summary by group:**")
        for group, metrics in results["results"].items():
            st.write(f"- {group}: {metrics}")
    else:
        st.write("No results found after applying filters.")