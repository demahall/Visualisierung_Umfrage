from datetime import datetime
import traceback
from typing import List, Any
from pathlib import Path
import pandas as pd

class TinyLogger:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.fp = open(self.log_path, "w", encoding="utf-8")

        self.write(f"Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.write(f"Log file: {self.log_path.resolve()}")
        self.write("-" * 90)

    def write(self, msg: str):
        print(msg)
        self.fp.write(msg + "\n")
        self.fp.flush()

    def write_traceback(self):
        self.fp.write(traceback.format_exc() + "\n")
        self.fp.flush()

    def close(self):
        self.write("-" * 90)
        self.write(f"Run finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.fp.close()
