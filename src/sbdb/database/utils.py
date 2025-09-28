"""
General database utilities for SBDB framework.

Provides utility functions for data import/export operations.
"""

import os
import pandas as pd


def export_collection(df: pd.DataFrame, name: str, csv_path: str, json_path: str) -> None:
    """
    Export a DataFrame to CSV and JSON collections.
    
    Args:
        df: DataFrame to export
        name: Base name for the collection files
        csv_path: Directory path for CSV export
        json_path: Directory path for JSON export
    """
    # Ensure directories exist
    os.makedirs(csv_path, exist_ok=True)
    os.makedirs(json_path, exist_ok=True)
    
    csv_filename = os.path.join(csv_path, f'{name}_collection.csv')
    json_filename = os.path.join(json_path, f'{name}_collection.json')
    
    df.to_csv(csv_filename, index=False)
    df.to_json(path_or_buf=json_filename, orient='records')
    print(f'{name} - collection export OK\n')


def import_csv_library(file_path: str, skiprows: int | list[int] | None = None) -> pd.DataFrame:
    """
    Import a CSV library file.

    Args:
        file_path: Path to the CSV file
        skiprows: Rows to skip when reading CSV (e.g., unit rows)
        
    Returns:
        DataFrame containing the CSV data
        
    Raises:
        FileNotFoundError: If the CSV file does not exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    return pd.read_csv(file_path, skiprows=skiprows)
