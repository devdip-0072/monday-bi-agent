from collections import defaultdict
from logger import logger, log_metrics, log_error


def apply_filters(data, filters):
    """
    Apply dynamic filters to dataset.
    Supports:
    - exact match
    - range filters [start, end]
    """

    if not filters:
        logger.info("No filters applied")
        return data

    logger.info(f"Applying filters: {filters}")

    result = data

    for field, value in filters.items():

        if value is None:
            continue

        # RANGE FILTER
        if isinstance(value, list) and len(value) == 2:

            start, end = value

            result = [
                row for row in result
                if row.get(field) is not None
                and start <= row.get(field) <= end
            ]

        # EXACT MATCH
        else:

            target = str(value).lower()

            result = [
                row for row in result
                if row.get(field) is not None
                and str(row.get(field)).lower() == target
            ]

    logger.info(f"Rows after filtering: {len(result)}")

    return result

# METRIC ENGINE

def execute_metrics(data, metrics, group_by_cols=None):

    log_metrics(metrics)

    group_by_cols = group_by_cols or []

    grouped = defaultdict(list)

    for row in data:

        if group_by_cols:

            key = tuple(row.get(col) for col in group_by_cols)

            if len(key) == 1:
                key = key[0]

        else:
            key = "all"

        grouped[key].append(row)

    results = {}

    for key, rows in grouped.items():

        metric_result = {}

        for metric in metrics:

            m_type = metric.get("type")
            field = metric.get("field")

            # COUNT
            if m_type == "count":

                if field:
                    metric_result[f"count_{field}"] = sum(
                        1 for r in rows if r.get(field) is not None
                    )
                else:
                    metric_result["count"] = len(rows)

            # NUMERIC METRICS
            else:

                values = [
                    r.get(field)
                    for r in rows
                    if isinstance(r.get(field), (int, float))
                ]

                if not values:
                    metric_result[f"{m_type}_{field}"] = 0
                    continue

                if m_type == "sum":
                    metric_result[f"sum_{field}"] = sum(values)

                elif m_type == "average":
                    metric_result[f"avg_{field}"] = sum(values) / len(values)

                elif m_type == "min":
                    metric_result[f"min_{field}"] = min(values)

                elif m_type == "max":
                    metric_result[f"max_{field}"] = max(values)

        # Clean group key
        if isinstance(key, tuple):
            key = " | ".join(str(v) if v is not None else "N/A" for v in key)

        results[key] = metric_result

    logger.info(f"Metric groups computed: {len(results)}")

    return results



# DEDUPLICATION

def deduplicate_by_key(data, key):

    logger.info(f"Deduplicating by key: {key}")

    seen = set()
    result = []

    for row in data:

        val = row.get(key)

        if val and val not in seen:
            seen.add(val)
            result.append(row)

    logger.info(f"Rows after deduplication: {len(result)}")

    return result



# INNER JOIN ENGINE

def join_boards(data_map, join_key="deal_name"):

    boards = list(data_map.keys())

    logger.info(f"Joining boards: {boards}")

    # If only one board, no join needed
    if len(boards) == 1:
        logger.info("Single board detected — skipping join")
        return list(data_map.values())[0]

    base_board = boards[0]
    joined_data = data_map[base_board]

    for board in boards[1:]:

        other_data = data_map[board]

        lookup = defaultdict(list)

        for row in other_data:
            key = row.get(join_key)

            if key:
                lookup[key].append(row)

        merged_rows = []

        for row in joined_data:

            key = row.get(join_key)

            if key in lookup:

                for match in lookup[key]:

                    merged = {**row, **match}

                    merged_rows.append(merged)

        joined_data = merged_rows

        logger.info(f"Rows after joining with {board}: {len(joined_data)}")

    return joined_data

# MAIN ANALYTICS PIPELINE

def run_analytics(
    data_map,
    filters_map=None,
    metrics_map=None,
    group_by_map=None,
    join_key="deal_name"
):

    try:

        logger.info("Starting analytics pipeline")

        filters_map = filters_map or {}
        metrics_map = metrics_map or {}
        group_by_map = group_by_map or {}

        
        cleaned_map = {}

        for board, data in data_map.items():

            if board.lower().startswith("deal"):
                data = deduplicate_by_key(data, join_key)

            cleaned_map[board] = data

       
        joined_data = join_boards(cleaned_map, join_key)

        logger.info(f"Rows after join: {len(joined_data)}")

        
        combined_filters = {}

        for board_filters in filters_map.values():
            combined_filters.update(board_filters)

        filtered_data = apply_filters(joined_data, combined_filters)

        
        all_metrics = []

        for m in metrics_map.values():
            all_metrics.extend(m)

       
        group_cols = []

        for g in group_by_map.values():
            group_cols.extend(g)

        
        results = execute_metrics(filtered_data, all_metrics, group_cols)

        logger.info("Analytics pipeline completed")

        return {
            "total_rows": len(filtered_data),
            "results": results
        }

    except Exception as e:

        log_error(str(e))
        return {"error": str(e)}