import logging
import os
from datetime import datetime

# ==========================
# CREATE LOG DIRECTORY
# ==========================

LOG_DIR = "logs"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file = os.path.join(
    LOG_DIR,
    f"agent_log_{datetime.now().strftime('%Y-%m-%d')}.log"
)

# ==========================
# LOGGER CONFIG
# ==========================

logger = logging.getLogger("BI_AGENT")

if not logger.handlers:   # prevents duplicate logs

    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()

    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# ==========================
# LOG HELPERS
# ==========================

def log_query(query):
    logger.info(f"USER QUERY: {query}")


def log_gemini_call(prompt):
    logger.info("GEMINI API CALLED")
    logger.debug(f"PROMPT: {prompt}")


def log_monday_call(board_id):
    logger.info(f"MONDAY API CALLED | board_id={board_id}")


def log_rows(board, count):
    logger.info(f"ROWS FETCHED | board={board} | rows={count}")


def log_plan(plan):
    logger.info(f"PLANNER OUTPUT: {plan}")


def log_metrics(metrics):
    logger.info(f"METRICS EXECUTED: {metrics}")


def log_error(error):
    logger.error(f"ERROR: {error}")