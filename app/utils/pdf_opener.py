import os
import subprocess
import sys
from pathlib import Path


def open_pdf(file_path: str) -> None:
	path = Path(file_path)
	if not path.exists():
		raise FileNotFoundError(f"PDF not found: {file_path}")
	if sys.platform.startswith("win"):
		os.startfile(str(path))  # type: ignore[attr-defined]
	elif sys.platform == "darwin":
		subprocess.run(["open", str(path)], check=False)
	else:
		subprocess.run(["xdg-open", str(path)], check=False) 