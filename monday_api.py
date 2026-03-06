import os
import requests
from dotenv import load_dotenv
from logger import log_monday_call, log_rows, log_error, logger

load_dotenv()
API_KEY = os.getenv("MONDAY_API_KEY")

HEADERS = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
    "API-Version": "2023-10"
}


def fetch_board_items(board_id, query_id=None):

    try:

        if not API_KEY:
            raise Exception("MONDAY_API_KEY not loaded from .env")

        board_id = int(board_id)

        
        if query_id:
            log_monday_call(query_id, board_id)
        else:
            logger.info(f"MONDAY API CALLED | board_id={board_id}")

        query = f"""
        query {{
            boards(ids: {board_id}) {{
                items_page(limit: 500) {{
                    items {{
                        name
                        column_values {{
                            column {{
                                title
                            }}
                            text
                        }}
                    }}
                }}
            }}
        }}
        """

        response = requests.post(
            "https://api.monday.com/v2",
            headers=HEADERS,
            json={"query": query},
            timeout=30
        )

        # debug logging
        logger.debug(f"STATUS CODE: {response.status_code}")
        logger.debug(f"RAW RESPONSE: {response.text}")

        data = response.json()

        # Check API errors
        if "errors" in data:
            raise Exception(f"Monday API Error: {data['errors']}")

        if not data.get("data") or not data["data"]["boards"]:
            raise Exception("Board not found or empty response")

        items = data["data"]["boards"][0]["items_page"]["items"]

        formatted = []

        for item in items:

            row = {"Deal Name": item["name"]}

            for col in item["column_values"]:
                row[col["column"]["title"]] = col["text"]

            formatted.append(row)

        # log rows fetched
        if query_id:
            log_rows(query_id, board_id, len(formatted))
        else:
            logger.info(f"ROWS FETCHED | board={board_id} | rows={len(formatted)}")

        return formatted

    except Exception as e:

        if query_id:
            log_error(query_id, str(e))
        else:
            logger.error(str(e))

        return []