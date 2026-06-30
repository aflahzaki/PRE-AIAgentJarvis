"""
Data Tools - CSV/JSON data manipulation for J.A.R.V.I.S agents.

Provides data reading, description, filtering, and statistics calculation
using pandas (with fallback to the built-in csv module when pandas is
unavailable). All functions return structured dict results with
success/error status.

Security: All file operations are restricted to the workspace directory
(configurable via JARVIS_WORKSPACE env var, defaults to current working dir).
This prevents the LLM from reading/writing arbitrary system files.

Dependencies:
    - pandas: Install with `pip install pandas` (optional, with csv fallback)
"""

import csv
import logging
import os
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Workspace root for path restriction.
# All file operations are confined to this directory.
_WORKSPACE_ROOT = os.path.abspath(
    os.getenv("JARVIS_WORKSPACE", os.getcwd())
)

# Graceful import of pandas
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning(
        "pandas not installed. Data tools will use basic csv module fallback. "
        "Install with: pip install pandas"
    )


def _validate_file_path(file_path: str) -> Dict[str, Any]:
    """Validate that a file path exists, is accessible, and is within workspace.

    Resolves the path to absolute and checks it is under the workspace root.
    This prevents path traversal attacks (e.g., '../../etc/passwd').

    Args:
        file_path: Path to validate.

    Returns:
        Dict with 'valid' bool and optional 'error' string.
    """
    if not file_path or not file_path.strip():
        return {"valid": False, "error": "File path cannot be empty."}

    abs_path = os.path.abspath(file_path)

    # Ensure the resolved path is within the workspace root
    if not abs_path.startswith(_WORKSPACE_ROOT + os.sep) and abs_path != _WORKSPACE_ROOT:
        return {
            "valid": False,
            "error": "Access denied: path '{}' is outside the allowed workspace.".format(
                file_path
            ),
        }

    if not os.path.exists(abs_path):
        return {
            "valid": False,
            "error": "File not found: {}".format(file_path),
        }

    if not os.path.isfile(abs_path):
        return {
            "valid": False,
            "error": "Path is not a file: {}".format(file_path),
        }

    return {"valid": True, "path": abs_path}


def _read_csv_fallback(file_path: str) -> Dict[str, Any]:
    """Read a CSV file using the built-in csv module (fallback).

    Args:
        file_path: Path to the CSV file.

    Returns:
        Dict with headers, rows, and row count.
    """
    try:
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            rows = list(reader)

        return {
            "success": True,
            "headers": list(headers),
            "rows": rows,
            "row_count": len(rows),
            "column_count": len(headers),
        }
    except Exception as e:
        return {"success": False, "error": "CSV read error: {}".format(str(e))}


def read_csv_file(
    file_path: str, encoding: str = "utf-8"
) -> Dict[str, Any]:
    """Read a CSV file and return its contents.

    Args:
        file_path: Path to the CSV file.
        encoding: File encoding (default: utf-8).

    Returns:
        Dict with 'success', file info (headers, rows, shape) or 'error'.
    """
    validation = _validate_file_path(file_path)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}

    abs_path = validation["path"]

    if PANDAS_AVAILABLE:
        try:
            df = pd.read_csv(abs_path, encoding=encoding)
            # Convert first few rows to display
            preview_rows = df.head(10).to_dict(orient="records")

            return {
                "success": True,
                "path": abs_path,
                "headers": list(df.columns),
                "rows": preview_rows,
                "row_count": len(df),
                "column_count": len(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            }
        except Exception as e:
            logger.error("pandas read_csv error: %s", str(e))
            return {
                "success": False,
                "error": "Error reading CSV: {}".format(str(e)),
            }
    else:
        # Fallback to csv module
        return _read_csv_fallback(abs_path)


def describe_data(file_path: str) -> Dict[str, Any]:
    """Generate descriptive statistics for a CSV file.

    Provides count, mean, std, min, max, and quartiles for numeric columns.
    Falls back to basic statistics when pandas is unavailable.

    Args:
        file_path: Path to the CSV file to describe.

    Returns:
        Dict with 'success' and 'description' (formatted stats) or 'error'.
    """
    validation = _validate_file_path(file_path)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}

    abs_path = validation["path"]

    if PANDAS_AVAILABLE:
        try:
            df = pd.read_csv(abs_path)
            description = df.describe(include="all").to_string()
            info_lines = []
            info_lines.append("Shape: {} rows x {} columns".format(*df.shape))
            info_lines.append("Columns: {}".format(", ".join(df.columns)))
            info_lines.append(
                "Dtypes: {}".format(
                    ", ".join(
                        "{}: {}".format(c, t) for c, t in df.dtypes.items()
                    )
                )
            )
            info_lines.append(
                "Missing values: {}".format(
                    ", ".join(
                        "{}: {}".format(c, v)
                        for c, v in df.isnull().sum().items()
                        if v > 0
                    )
                    or "None"
                )
            )
            info_lines.append("")
            info_lines.append("Statistical Summary:")
            info_lines.append(description)

            return {
                "success": True,
                "description": "\n".join(info_lines),
                "shape": {"rows": df.shape[0], "columns": df.shape[1]},
                "columns": list(df.columns),
            }
        except Exception as e:
            logger.error("describe_data error: %s", str(e))
            return {
                "success": False,
                "error": "Error describing data: {}".format(str(e)),
            }
    else:
        # Fallback: basic stats using csv module
        try:
            result = _read_csv_fallback(abs_path)
            if not result["success"]:
                return result

            headers = result["headers"]
            rows = result["rows"]
            info_lines = []
            info_lines.append(
                "Shape: {} rows x {} columns".format(
                    result["row_count"], result["column_count"]
                )
            )
            info_lines.append("Columns: {}".format(", ".join(headers)))

            # Try basic numeric stats for each column
            for col in headers:
                values = []
                for row in rows:
                    try:
                        values.append(float(row[col]))
                    except (ValueError, TypeError):
                        continue

                if values:
                    info_lines.append(
                        "\n{}: count={}, min={:.2f}, max={:.2f}, "
                        "mean={:.2f}".format(
                            col,
                            len(values),
                            min(values),
                            max(values),
                            sum(values) / len(values),
                        )
                    )

            return {
                "success": True,
                "description": "\n".join(info_lines),
                "shape": {
                    "rows": result["row_count"],
                    "columns": result["column_count"],
                },
                "columns": headers,
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Error describing data: {}".format(str(e)),
            }


def filter_data(
    file_path: str, column: str, operator: str, value: Any
) -> Dict[str, Any]:
    """Filter CSV data by a condition on a specific column.

    Supported operators: ==, !=, >, <, >=, <=, contains, startswith, endswith.

    Args:
        file_path: Path to the CSV file.
        column: Column name to filter on.
        operator: Comparison operator.
        value: Value to compare against.

    Returns:
        Dict with 'success' and filtered 'rows' or 'error'.
    """
    validation = _validate_file_path(file_path)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}

    abs_path = validation["path"]

    valid_operators = ["==", "!=", ">", "<", ">=", "<=", "contains", "startswith", "endswith"]
    if operator not in valid_operators:
        return {
            "success": False,
            "error": "Invalid operator '{}'. Valid operators: {}".format(
                operator, ", ".join(valid_operators)
            ),
        }

    if PANDAS_AVAILABLE:
        try:
            df = pd.read_csv(abs_path)

            if column not in df.columns:
                return {
                    "success": False,
                    "error": "Column '{}' not found. Available: {}".format(
                        column, ", ".join(df.columns)
                    ),
                }

            if operator == "==":
                mask = df[column] == value
            elif operator == "!=":
                mask = df[column] != value
            elif operator == ">":
                mask = df[column] > float(value)
            elif operator == "<":
                mask = df[column] < float(value)
            elif operator == ">=":
                mask = df[column] >= float(value)
            elif operator == "<=":
                mask = df[column] <= float(value)
            elif operator == "contains":
                mask = df[column].astype(str).str.contains(
                    str(value), case=False, na=False
                )
            elif operator == "startswith":
                mask = df[column].astype(str).str.startswith(str(value), na=False)
            elif operator == "endswith":
                mask = df[column].astype(str).str.endswith(str(value), na=False)
            else:
                mask = df[column] == value

            filtered = df[mask]
            rows = filtered.head(100).to_dict(orient="records")

            return {
                "success": True,
                "rows": rows,
                "count": len(filtered),
                "filter": "{} {} {}".format(column, operator, value),
            }
        except Exception as e:
            logger.error("filter_data error: %s", str(e))
            return {
                "success": False,
                "error": "Error filtering data: {}".format(str(e)),
            }
    else:
        # Fallback: csv module filtering
        try:
            result = _read_csv_fallback(abs_path)
            if not result["success"]:
                return result

            if column not in result["headers"]:
                return {
                    "success": False,
                    "error": "Column '{}' not found. Available: {}".format(
                        column, ", ".join(result["headers"])
                    ),
                }

            filtered_rows = []
            for row in result["rows"]:
                row_val = row.get(column, "")
                try:
                    if operator in (">", "<", ">=", "<="):
                        row_num = float(row_val)
                        cmp_val = float(value)
                        if operator == ">" and row_num > cmp_val:
                            filtered_rows.append(row)
                        elif operator == "<" and row_num < cmp_val:
                            filtered_rows.append(row)
                        elif operator == ">=" and row_num >= cmp_val:
                            filtered_rows.append(row)
                        elif operator == "<=" and row_num <= cmp_val:
                            filtered_rows.append(row)
                    elif operator == "==":
                        if str(row_val) == str(value):
                            filtered_rows.append(row)
                    elif operator == "!=":
                        if str(row_val) != str(value):
                            filtered_rows.append(row)
                    elif operator == "contains":
                        if str(value).lower() in str(row_val).lower():
                            filtered_rows.append(row)
                    elif operator == "startswith":
                        if str(row_val).startswith(str(value)):
                            filtered_rows.append(row)
                    elif operator == "endswith":
                        if str(row_val).endswith(str(value)):
                            filtered_rows.append(row)
                except (ValueError, TypeError):
                    continue

            return {
                "success": True,
                "rows": filtered_rows[:100],
                "count": len(filtered_rows),
                "filter": "{} {} {}".format(column, operator, value),
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Error filtering data: {}".format(str(e)),
            }


def calculate_stats(
    file_path: str, column: str
) -> Dict[str, Any]:
    """Calculate statistical measures for a numeric column.

    Computes count, mean, median, std, min, max, sum, and quartiles.

    Args:
        file_path: Path to the CSV file.
        column: Name of the numeric column to analyze.

    Returns:
        Dict with 'success' and 'stats' dict or 'error'.
    """
    validation = _validate_file_path(file_path)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}

    abs_path = validation["path"]

    if PANDAS_AVAILABLE:
        try:
            df = pd.read_csv(abs_path)

            if column not in df.columns:
                return {
                    "success": False,
                    "error": "Column '{}' not found. Available: {}".format(
                        column, ", ".join(df.columns)
                    ),
                }

            col_data = pd.to_numeric(df[column], errors="coerce").dropna()

            if len(col_data) == 0:
                return {
                    "success": False,
                    "error": "Column '{}' has no numeric values.".format(
                        column
                    ),
                }

            stats = {
                "column": column,
                "count": int(col_data.count()),
                "mean": float(col_data.mean()),
                "median": float(col_data.median()),
                "std": float(col_data.std()),
                "min": float(col_data.min()),
                "max": float(col_data.max()),
                "sum": float(col_data.sum()),
                "q25": float(col_data.quantile(0.25)),
                "q50": float(col_data.quantile(0.50)),
                "q75": float(col_data.quantile(0.75)),
            }

            return {"success": True, "stats": stats}

        except Exception as e:
            logger.error("calculate_stats error: %s", str(e))
            return {
                "success": False,
                "error": "Error calculating stats: {}".format(str(e)),
            }
    else:
        # Fallback: basic stats using csv module
        try:
            result = _read_csv_fallback(abs_path)
            if not result["success"]:
                return result

            if column not in result["headers"]:
                return {
                    "success": False,
                    "error": "Column '{}' not found. Available: {}".format(
                        column, ", ".join(result["headers"])
                    ),
                }

            values = []
            for row in result["rows"]:
                try:
                    values.append(float(row[column]))
                except (ValueError, TypeError):
                    continue

            if not values:
                return {
                    "success": False,
                    "error": "Column '{}' has no numeric values.".format(
                        column
                    ),
                }

            values.sort()
            n = len(values)
            mean_val = sum(values) / n
            variance = sum((x - mean_val) ** 2 for x in values) / max(n - 1, 1)
            std_val = variance ** 0.5

            # Simple quartile calculation
            def percentile(sorted_vals: List[float], p: float) -> float:
                idx = (len(sorted_vals) - 1) * p
                lower = int(idx)
                upper = lower + 1
                if upper >= len(sorted_vals):
                    return sorted_vals[-1]
                weight = idx - lower
                return sorted_vals[lower] * (1 - weight) + sorted_vals[upper] * weight

            stats = {
                "column": column,
                "count": n,
                "mean": mean_val,
                "median": percentile(values, 0.5),
                "std": std_val,
                "min": values[0],
                "max": values[-1],
                "sum": sum(values),
                "q25": percentile(values, 0.25),
                "q50": percentile(values, 0.50),
                "q75": percentile(values, 0.75),
            }

            return {"success": True, "stats": stats}

        except Exception as e:
            return {
                "success": False,
                "error": "Error calculating stats: {}".format(str(e)),
            }
