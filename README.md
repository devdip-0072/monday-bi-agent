Monday.com Business Intelligence Agent

An AI-powered Business Intelligence Agent that answers founder-level business questions by querying live data from monday.com boards.

The system allows users to ask natural language questions about business metrics such as revenue, pipeline performance, billing, and collections.

Instead of manually exporting data and performing spreadsheet analysis, executives can get instant insights through conversation.

Problem

Founders frequently ask questions such as:

How much revenue have we collected from completed projects?

What does our pipeline look like for the energy sector this quarter?

Which sectors generate the highest revenue?

Answering these questions typically requires:

Exporting data from monday.com boards

Cleaning messy datasets

Writing queries or performing manual analysis

Preparing ad-hoc reports

This process is slow and inefficient.

The goal of this project is to build an AI agent that automatically performs this analysis in real time.

Solution Overview

The Monday BI Agent converts natural language questions into structured analytics queries that are executed on live monday.com data.

The system performs the following steps:

Understand the user question using an LLM.

Convert the question into a structured analytics plan.

Fetch live data from monday.com boards.

Normalize messy business data.

Execute analytics operations.

Return the result to the user.

This architecture combines LLM reasoning with deterministic analytics execution to ensure both flexibility and accuracy.
System architecture
User Question
      │
      ▼
LLM Planner Agent
      │
      ▼
Schema Validation
      │
      ▼
Monday.com API Fetcher
      │
      ▼
Data Normalization
      │
      ▼
Analytics Engine
      │
      ▼
Business Insight

The LLM is responsible only for query planning, while all analytics computations are performed by deterministic code.

This prevents hallucinated results and ensures reliable financial calculations.

Example Query

User Question:

Total collected amount for completed work orders

Planner Output:

{
 "boards": ["Work_order_Tracker"],
 "metrics": [
   {
     "board": "Work_order_Tracker",
     "type": "sum",
     "column": "Collected Amount in Rupees (Incl of GST.) (Masked)"
   }
 ],
 "filters": [
   {
     "board": "Work_order_Tracker",
     "column": "Execution Status",
     "value": "Completed"
   }
 ],
 "group_by": []
}

The analytics engine then executes this plan on live board data.

Data Sources

The system integrates with two monday.com boards.

Work Order Tracker

Tracks project execution and financial lifecycle.

Contains fields such as:

Execution status

Billing value

Collected revenue

Invoice details

Collection status

This board is used for revenue and operational analytics.

Deal Funnel

Tracks the sales pipeline.

Contains fields such as:

Deal stage

Deal value

Closure probability

Sector

This board is used for pipeline and sales analytics.

Key Features
Natural Language Querying

Users can ask business questions in plain English.

Examples:

Total collected revenue

Pipeline value by sector

Outstanding receivables

Number of completed projects

Live monday.com Integration

Every query fetches live data using the monday.com API.

No caching or preloading is used, ensuring results reflect the latest board state.

Data Normalization

Real-world datasets often contain inconsistencies such as:

missing values

mixed date formats

numbers stored as text.

The system automatically cleans and standardizes data before analysis.

Schema-Grounded LLM Planning

The LLM is provided with a schema definition that lists all available boards and columns.

This prevents the model from hallucinating fields and improves planning accuracy.

Deterministic Analytics Engine

All calculations are executed by a Python analytics engine rather than the LLM.

Supported operations include:

SUM

COUNT

AVERAGE

MIN

MAX

GROUP BY

FILTER

This ensures accurate and reproducible results.

Agent Action Logging

The system logs:

LLM prompts

generated analytics plans

errors.

This provides full traceability and simplifies debugging.

Project Structure
monday-bi-agent
│
├── app.py
├── planner.py
├── analytics_engine.py
├── normalizer.py
├── monday_api.py
├── logger.py
│
├── schema.yml  
│
└── logs

Each component handles a specific part of the analytics pipeline.

Technology Stack
Component	Technology
Backend	Python
Interface	Streamlit
LLM	Gemini 2.5 Flash
Data Processing	Pandas
API Integration	monday.com API
Prompt Configuration	YAML
Running the Project
Install dependencies
pip install -r requirements.txt
Set environment variables

Create a .env file.

GEMINI_API_KEY=your_api_key
DEALS_BOARD_ID=your_board_id
WORK_ORDERS_BOARD_ID=your_board_id
MONDAY_API_KEY=your_monday_key
Run the application
streamlit run app.py

The application will start a local interface where users can ask questions.

Example Queries

Revenue Analysis

Total collected amount for completed work orders

Pipeline Analysis

Pipeline value by sector

Operational Analysis

Number of completed work orders

Financial Analysis

Total outstanding receivables
Limitations

Current prototype limitations include:

limited join logic between boards

no long-term conversation memory

limited advanced analytics capabilities.

Future Improvements

Potential enhancements:

multi-agent architecture

semantic column matching using embeddings

automated insight generation

advanced BI visualizations

conversational memory for follow-up queries.

Conclusion

The Monday BI Agent demonstrates how combining LLM-based query planning with deterministic analytics execution can create a powerful natural language business intelligence system.

This architecture enables business users to obtain real-time insights from complex datasets without manual analysis workflows.

