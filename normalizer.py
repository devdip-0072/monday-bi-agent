import re
from datetime import datetime, timedelta
from logger import logger


# =====================================
# COLUMN NAME NORMALIZER
# =====================================

def normalize_key(key):
    """
    Standardize column names.
    """

    if key is None:
        return None

    key = str(key).strip().lower()

    # remove special characters
    key = re.sub(r"[^\w\s]", "", key)

    # convert spaces to underscore
    key = re.sub(r"\s+", "_", key)

    return key


# =====================================
# NULL VALUE CHECK
# =====================================

def is_null(value):

    return value in [None, "", "N/A", "NA", "-", "--", "null"]


# =====================================
# SAFE FLOAT
# =====================================

def safe_float(value):

    if is_null(value):
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    raw_value = value

    value = str(value)
    value = value.replace(",", "")
    value = value.replace("₹", "")
    value = value.replace("$", "")

    try:
        return float(value)

    except Exception:

        logger.warning(f"Invalid numeric value detected: {raw_value}")

        return 0.0


# =====================================
# SAFE DATE
# =====================================

def safe_date(value):

    if is_null(value):
        return None

    # Excel serial date support
    if isinstance(value, (int, float)):
        try:
            return datetime(1899, 12, 30) + timedelta(days=float(value))
        except Exception:

            logger.warning(f"Invalid excel serial date: {value}")

            return None

    value = str(value).strip()

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d %b %Y",
        "%d %B %Y"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)

        except Exception:
            continue

    logger.warning(f"Unrecognized date format: {value}")

    return None


# =====================================
# SAFE TEXT
# =====================================

def safe_text(value):

    if is_null(value):
        return None

    text = str(value).strip()

    # remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text


# =====================================
# LOWERCASE NORMALIZATION
# =====================================

def safe_lower(value):

    text = safe_text(value)

    if text is None:
        return None

    return text.lower()


# =====================================
# GENERIC ROW NORMALIZER
# =====================================

def normalize_row(row, monetary_fields, date_fields, lowercase_fields):

    clean_row = {}

    try:

        for key, value in row.items():

            norm_key = normalize_key(key)

            if norm_key in monetary_fields:

                clean_row[norm_key] = safe_float(value)

            elif norm_key in date_fields:

                clean_row[norm_key] = safe_date(value)

            elif norm_key in lowercase_fields:

                clean_row[norm_key] = safe_lower(value)

            else:

                clean_row[norm_key] = safe_text(value)

    except Exception as e:

        logger.error(f"Row normalization failed: {row} | Error: {e}")

    return clean_row


# =====================================
# NORMALIZE DEALS BOARD
# =====================================

def normalize_deals(data):

    logger.info("Starting Deals normalization")

    monetary_fields = {
        "masked_deal_value"
    }

    date_fields = {
        "created_date",
        "tentative_close_date",
        "close_date_a"
    }

    lowercase_fields = {
        "sectorservice",
        "deal_status",
        "deal_stage"
    }

    normalized = []

    for row in data:

        normalized.append(
            normalize_row(row, monetary_fields, date_fields, lowercase_fields)
        )

    logger.info(f"Deals normalized successfully: {len(normalized)} rows")

    return normalized


# =====================================
# NORMALIZE WORK ORDERS
# =====================================

def normalize_workorders(data):

    logger.info("Starting Workorders normalization")

    monetary_fields = {

        "amount_in_rupees_excl_of_gst_masked",
        "amount_in_rupees_incl_of_gst_masked",

        "billed_value_in_rupees_excl_of_gst_masked",
        "billed_value_in_rupees_incl_of_gst_masked",

        "collected_amount_in_rupees_incl_of_gst_masked",

        "amount_to_be_billed_in_rs_exl_of_gst_masked",
        "amount_to_be_billed_in_rs_incl_of_gst_masked",

        "amount_receivable_masked"
    }

    date_fields = {

        "data_delivery_date",
        "date_of_poloi",

        "probable_start_date",
        "probable_end_date",

        "last_invoice_date",

        "collection_date",

        "actual_billing_month",
        "actual_collection_month"
    }

    lowercase_fields = {

        "execution_status",
        "billing_status",
        "sector",
        "type_of_work"
    }

    normalized = []

    for row in data:

        normalized.append(
            normalize_row(row, monetary_fields, date_fields, lowercase_fields)
        )

    logger.info(f"Workorders normalized successfully: {len(normalized)} rows")

    return normalized