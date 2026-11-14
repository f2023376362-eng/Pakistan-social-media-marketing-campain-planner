"""
Data Loader Module for YouTube Social Media Data Collection & Preprocessing.
Discovers and loads raw or processed CSV and Excel datasets.
Supports both Video Metadata and Comment Telemetry formats.
"""

import glob
import os
from pathlib import Path
from typing import Tuple, List, Optional
import pandas as pd


def discover_datasets(data_dir: str = "data") -> dict[str, List[Path]]:
    """
    Discovers all available CSV and Excel dataset files under raw, processed, and brand folders.
    Guarantees isolation from the archive directory.
    """
    base = Path(data_dir)
    results = {
        "raw_videos": sorted(base.glob("raw/videos/*.[c][s][v]")),
        "raw_comments": sorted(base.glob("raw/comments/*.[c][s][v]")),
        "processed_videos": sorted(base.glob("processed/videos/*.[c][s][v]")),
        "processed_comments": sorted(base.glob("processed/comments/*.[c][s][v]")),
        "brand_datasets": sorted(base.glob("brand/*.[c][s][v]")),
        "all_csvs": sorted(base.glob("**/*.csv")),
    }
    return results


def find_target_csv(
    data_dir: str = "data/raw/comments",
    fallback_dir: str = "data/raw",
) -> Path:
    """
    Searches for the most recent CSV file in the target or fallback directory.
    """
    target_path = Path(data_dir)
    matches = list(target_path.glob("*.csv")) if target_path.exists() else []

    if not matches and Path(fallback_dir).exists():
        matches = list(Path(fallback_dir).glob("**/*.csv"))

    # Also check data/brand
    brand_path = Path("data/brand")
    if not matches and brand_path.exists():
        matches = list(brand_path.glob("*.csv"))

    if not matches:
        raise FileNotFoundError(f"No CSV dataset files found in {data_dir}, {fallback_dir}, or data/brand")

    latest_file = max(matches, key=os.path.getmtime)
    return latest_file


def load_dataset(
    file_path: Optional[Path | str] = None,
    dataset_type: str = "comments",
    prefer_processed: bool = True,
) -> Tuple[Optional[pd.DataFrame], Optional[Path]]:
    """
    Loads comments or videos dataset into a pandas DataFrame.
    Prefers processed dataset if present, otherwise discovers raw or brand dataset.
    Returns: (df, resolved_file_path) or (None, None) if no data exists.
    """
    if file_path is None:
        if dataset_type == "videos":
            proc_files = list(Path("data/processed/videos").glob("*.csv")) if Path("data/processed/videos").exists() else []
            raw_files = list(Path("data/raw/videos").glob("*.csv")) if Path("data/raw/videos").exists() else []
            if prefer_processed and proc_files:
                file_path = max(proc_files, key=os.path.getmtime)
            elif raw_files:
                file_path = max(raw_files, key=os.path.getmtime)
            else:
                return None, None
        else:
            proc_files = list(Path("data/processed/comments").glob("*.csv")) if Path("data/processed/comments").exists() else []
            raw_files = list(Path("data/raw/comments").glob("*.csv")) if Path("data/raw/comments").exists() else []
            brand_files = list(Path("data/brand").glob("*.csv")) if Path("data/brand").exists() else []
            if prefer_processed and proc_files:
                file_path = max(proc_files, key=os.path.getmtime)
            elif raw_files:
                file_path = max(raw_files, key=os.path.getmtime)
            elif brand_files:
                file_path = max(brand_files, key=os.path.getmtime)
            else:
                return None, None
    else:
        file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(f"Target dataset file not found: {file_path}")

    # Load based on extension
    if file_path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path, encoding="utf-8-sig")

    return df, file_path
