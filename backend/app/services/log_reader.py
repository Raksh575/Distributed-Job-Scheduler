import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

class LogReaderService:
    """
    LogReaderService parses, filters, and paginates JSON-structured application logs.
    Reads logs in reverse (latest first) and generates downloadable file streams.
    """

    def __init__(self, log_filename: str = "app_structured.log"):
        self.log_filename = log_filename

    def read_logs(
        self,
        category: Optional[str] = None,
        level: Optional[str] = None,
        search_query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Read and filter structured logs from file, returning matching logs and total count."""
        if not os.path.exists(self.log_filename):
            return [], 0

        filtered_logs = []
        
        # Read the file and parse lines in reverse order (newest first)
        with open(self.log_filename, "r", encoding="utf8") as f:
            lines = f.readlines()
            
        for line in reversed(lines):
            line_str = line.strip()
            if not line_str:
                continue
                
            try:
                log_entry = json.loads(line_str)
                
                # Filter 1: Log Level
                if level and log_entry.get("level", "").upper() != level.upper():
                    continue
                    
                # Filter 2: Category
                if category and log_entry.get("category", "").lower() != category.lower():
                    continue
                    
                # Filter 3: Search Query
                if search_query:
                    q = search_query.lower()
                    msg = log_entry.get("message", "").lower()
                    logger_name = log_entry.get("logger", "").lower()
                    if q not in msg and q not in logger_name:
                        continue
                        
                # Filter 4: Date Range
                if start_date or end_date:
                    ts_str = log_entry.get("timestamp", "")
                    # standard timestamp format: %Y-%m-%dT%H:%M:%SZ
                    try:
                        # Strip trailing 'Z' if present for parser
                        cleaned_ts = ts_str.replace("Z", "+00:00")
                        entry_date = datetime.fromisoformat(cleaned_ts)
                        if start_date and entry_date < start_date:
                            continue
                        if end_date and entry_date > end_date:
                            continue
                    except ValueError:
                        pass # Ignore dates if they fail to parse

                filtered_logs.append(log_entry)
                
            except json.JSONDecodeError:
                continue # Skip malformed log lines
                
        total_count = len(filtered_logs)
        paginated_logs = filtered_logs[skip : skip + limit]
        
        return paginated_logs, total_count

    def generate_download_stream(
        self,
        category: Optional[str] = None,
        level: Optional[str] = None,
        search_query: Optional[str] = None
    ):
        """Generator yielding matching plain log lines for file downloads."""
        if not os.path.exists(self.log_filename):
            return

        with open(self.log_filename, "r", encoding="utf8") as f:
            lines = f.readlines()

        for line in reversed(lines):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                log_entry = json.loads(line_str)
                if level and log_entry.get("level", "").upper() != level.upper():
                    continue
                if category and log_entry.get("category", "").lower() != category.lower():
                    continue
                if search_query:
                    q = search_query.lower()
                    msg = log_entry.get("message", "").lower()
                    logger_name = log_entry.get("logger", "").lower()
                    if q not in msg and q not in logger_name:
                        continue
                
                # Format to standard readable log format
                formatted = f"{log_entry.get('timestamp')} [{log_entry.get('level')}] {log_entry.get('logger')} - {log_entry.get('message')}\n"
                yield formatted
            except json.JSONDecodeError:
                yield f"MALFORMED_LINE: {line_str}\n"
