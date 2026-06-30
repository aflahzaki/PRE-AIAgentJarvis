"""
Tools - Autonomous capabilities for J.A.R.V.I.S agents.

Available tools:
- file_tools: File read/write/list/edit operations
- python_executor: Safe Python script execution with timeout
- web_search: DuckDuckGo web and news search
- data_tools: CSV/JSON data manipulation with pandas
- scheduler_tools: Task CRUD via database
- knowledge_tools: Knowledge base CRUD via database
- writing_tools: Email, proposal, caption templates and formatting
"""

from core.tools.file_tools import read_file, write_file, list_files, edit_file
from core.tools.python_executor import execute_python, execute_python_code

__all__ = [
    "read_file",
    "write_file",
    "list_files",
    "edit_file",
    "execute_python",
    "execute_python_code",
]

# Conditional imports for new tools - wrapped in try/except to avoid crashes
# if dependencies are missing. Each module handles its own graceful degradation.

try:
    from core.tools.web_search import search_web, search_news, get_page_summary
    __all__.extend(["search_web", "search_news", "get_page_summary"])
except ImportError:
    pass

try:
    from core.tools.data_tools import (
        read_csv_file, describe_data, filter_data, calculate_stats
    )
    __all__.extend(["read_csv_file", "describe_data", "filter_data", "calculate_stats"])
except ImportError:
    pass

try:
    from core.tools.scheduler_tools import (
        add_task, list_tasks, update_task, complete_task,
        get_overdue_tasks, get_today_tasks
    )
    __all__.extend([
        "add_task", "list_tasks", "update_task", "complete_task",
        "get_overdue_tasks", "get_today_tasks",
    ])
except ImportError:
    pass

try:
    from core.tools.knowledge_tools import (
        add_knowledge, search_knowledge, get_knowledge_by_category,
        delete_knowledge
    )
    __all__.extend([
        "add_knowledge", "search_knowledge", "get_knowledge_by_category",
        "delete_knowledge",
    ])
except ImportError:
    pass

try:
    from core.tools.writing_tools import (
        email_template, proposal_template, caption_template,
        format_academic, format_casual
    )
    __all__.extend([
        "email_template", "proposal_template", "caption_template",
        "format_academic", "format_casual",
    ])
except ImportError:
    pass
