"""
Data Analyst Agent - Data analysis and insight generation agent.

Inherits from BaseAgent and specializes in:
- Reading and parsing CSV/JSON files
- Computing descriptive statistics
- Filtering and querying data
- Generating insights and visualizations (Python code)
- Creating analysis summaries

System prompt focuses on analytical thinking, data-driven insights,
and actionable recommendations.
"""

import logging
from typing import Optional

from core.agents.base_agent import BaseAgent
from core.providers.base_provider import BaseProvider
from core.tools.data_tools import (
    read_csv_file,
    describe_data,
    filter_data,
    calculate_stats,
)
from core.tools.python_executor import execute_python_code

logger = logging.getLogger(__name__)


# System prompt for data analyst agent
DATA_ANALYST_SYSTEM_PROMPT = (
    "Kamu adalah J.A.R.V.I.S Data Analyst Agent - agen analisis data yang "
    "mengubah raw data menjadi insight yang actionable.\n\n"
    "Misi Utama:\n"
    "- Membaca dan memahami struktur data (CSV/JSON)\n"
    "- Menghitung statistik: mean, median, std, distribusi, korelasi\n"
    "- Mengidentifikasi pattern, trend, dan anomali dalam data\n"
    "- Generate kode Python untuk visualisasi (matplotlib/seaborn)\n"
    "- Menyajikan insight yang mudah dipahami non-teknis\n\n"
    "Personality:\n"
    "- Analitis: Selalu backup conclusion dengan data\n"
    "- Teliti: Periksa data quality sebelum analisis\n"
    "- Praktis: Berikan rekomendasi yang actionable\n"
    "- Jelas: Jelaskan statistik dalam bahasa yang mudah dipahami\n\n"
    "Workflow:\n"
    "1. Baca file data untuk memahami struktur dan isinya\n"
    "2. Gunakan describe_data untuk overview statistik\n"
    "3. Gunakan filter_data untuk mengeksplorasi subset\n"
    "4. Gunakan calculate_stats untuk analisis mendalam per kolom\n"
    "5. Jika diminta visualisasi, generate kode Python (matplotlib)\n"
    "6. Rangkum findings dalam format:\n"
    "   - Key Insights (poin-poin utama)\n"
    "   - Data Summary (statistik penting)\n"
    "   - Recommendations (saran berdasarkan data)\n\n"
    "Tips:\n"
    "- Selalu cek missing values dan data types terlebih dahulu\n"
    "- Gunakan Bahasa Indonesia untuk penjelasan, English untuk code\n"
    "- Jika data terlalu besar, fokus pada sample/aggregate"
)


class DataAnalystAgent(BaseAgent):
    """Data analysis agent with statistical and visualization capabilities.

    Specializes in:
    - Reading and parsing CSV/JSON data files
    - Computing descriptive statistics and aggregations
    - Filtering and querying datasets
    - Generating Python visualization code (matplotlib)
    - Providing data-driven insights and recommendations
    """

    def __init__(
        self,
        provider: BaseProvider,
        model: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 5,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> None:
        """Initialize the Data Analyst Agent.

        Args:
            provider: LLM provider for inference.
            model: Model name to use.
            system_prompt: Optional custom system prompt.
            max_retries: Maximum self-healing retry attempts.
            temperature: Lower temperature for precise analysis.
            max_tokens: Higher limit for detailed reports.
        """
        super().__init__(
            name="data_analyst",
            provider=provider,
            model=model,
            system_prompt=system_prompt or DATA_ANALYST_SYSTEM_PROMPT,
            max_retries=max_retries,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self._register_data_tools()

    def _register_data_tools(self) -> None:
        """Register data analysis tools."""
        # Tool: read_csv_file
        self.register_tool(
            name="read_csv_file",
            func=read_csv_file,
            description=(
                "Read a CSV file and return its contents including headers, "
                "preview rows (first 10), row/column counts, and data types."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the CSV file to read",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                    },
                },
                "required": ["file_path"],
            },
        )

        # Tool: describe_data
        self.register_tool(
            name="describe_data",
            func=describe_data,
            description=(
                "Generate descriptive statistics for a CSV file. Provides "
                "count, mean, std, min, max, quartiles for numeric columns."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the CSV file to describe",
                    },
                },
                "required": ["file_path"],
            },
        )

        # Tool: filter_data
        self.register_tool(
            name="filter_data",
            func=filter_data,
            description=(
                "Filter CSV data by a condition. Supported operators: "
                "==, !=, >, <, >=, <=, contains, startswith, endswith."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the CSV file",
                    },
                    "column": {
                        "type": "string",
                        "description": "Column name to filter on",
                    },
                    "operator": {
                        "type": "string",
                        "description": "Comparison operator (==, !=, >, <, >=, <=, contains, startswith, endswith)",
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to compare against",
                    },
                },
                "required": ["file_path", "column", "operator", "value"],
            },
        )

        # Tool: calculate_stats
        self.register_tool(
            name="calculate_stats",
            func=calculate_stats,
            description=(
                "Calculate detailed statistics for a numeric column: "
                "count, mean, median, std, min, max, sum, quartiles (Q25, Q50, Q75)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the CSV file",
                    },
                    "column": {
                        "type": "string",
                        "description": "Name of the numeric column to analyze",
                    },
                },
                "required": ["file_path", "column"],
            },
        )

        # Tool: execute_python_code
        self.register_tool(
            name="execute_python_code",
            func=execute_python_code,
            description=(
                "Execute Python code for data visualization or custom analysis. "
                "Use matplotlib/seaborn for charts. Returns stdout, stderr, exit code."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code string to execute (e.g., matplotlib visualization)",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds (default: 30)",
                    },
                },
                "required": ["code"],
            },
        )

        logger.info("DataAnalystAgent: Registered %d tools", len(self._tools))

    def get_agent_type(self) -> str:
        """Get the agent type identifier.

        Returns:
            'data_analyst' - identifies this as a data analysis agent.
        """
        return "data_analyst"
