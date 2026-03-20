"""
Dataset Generation Tracking System

This module provides utilities for tracking dataset generation from
ObjectSet JSON descriptor files. It reads the output configuration
from each JSON file to build a record of all datasets and their status.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

import sbdb


def get_package_version(package_name: str) -> str:
    """Get version of an installed package.

    Args:
        package_name: Name of the package to look up.

    Returns:
        Version string, or a status message if unavailable.
    """
    try:
        import importlib.metadata

        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return "Not installed"
    except Exception:
        return "Unknown"


def get_file_metadata(filepath: str) -> dict:
    """Get metadata for a single output file.

    Args:
        filepath: Path to the file.

    Returns:
        Dict with keys: exists, size_mb, record_count (csv only).
    """
    metadata = {
        "exists": False,
        "size_mb": 0.0,
        "record_count": None,
    }
    p = Path(filepath)
    if p.exists():
        metadata["exists"] = True
        metadata["size_mb"] = round(
            p.stat().st_size / (1024 * 1024), 4
        )
        if p.suffix == ".csv":
            try:
                df = pd.read_csv(p)
                metadata["record_count"] = len(df)
            except Exception:
                pass
    return metadata


class DatasetTracker:
    """Track datasets defined by ObjectSet JSON descriptor files.

    Args:
        json_files: List of paths to ObjectSet JSON descriptor files.
        record_file: Path for the output tracking CSV record.
    """

    FIELDNAMES = [
        "dataset_name",
        "json_descriptor",
        "reference_class",
        "reference_package_version",
        "sbdb_version",
        "output_folder",
        "filetypes",
        "output_files",
        "record_count",
        "last_generated",
        "notes",
    ]

    def __init__(
        self,
        json_files: list[str],
        record_file: str = "dataset_record.csv",
    ):
        self.json_files = json_files
        self.record_file = Path(record_file)

    @classmethod
    def from_record_file(cls, record_file: str) -> DatasetTracker:
        """Create a DatasetTracker from an existing record CSV file.

        Reads the ``json_descriptor`` column from the record to
        reconstruct the list of JSON files.

        Args:
            record_file: Path to an existing dataset record CSV file.

        Returns:
            A DatasetTracker instance with json_files and record_file
            populated from the existing record.

        Raises:
            FileNotFoundError: If the record file does not exist.
        """
        record_path = Path(record_file)
        if not record_path.exists():
            raise FileNotFoundError(
                f"Record file '{record_file}' not found."
            )
        df = pd.read_csv(
            record_path, dtype=str, keep_default_na=False
        )
        json_files = df["json_descriptor"].tolist()
        tracker = cls(
            json_files=json_files, record_file=record_file
        )
        return tracker

    @staticmethod
    def get_dataset_name(json_file: str) -> str:
        """Get the dataset name from an ObjectSet JSON descriptor file.

        Reads the ``output.filename`` field from the JSON file.

        Args:
            json_file: Path to the ObjectSet JSON descriptor file.

        Returns:
            The dataset name (output filename) from the JSON file.

        Raises:
            ValueError: If the JSON file has no output configuration.
        """
        with open(json_file) as f:
            data = json.load(f)
        output_config = data.get("output", None)
        if output_config is None:
            raise ValueError(
                f"JSON file '{json_file}' has no 'output' config"
            )
        return output_config.get("filename", "output")

    def initialise_record(self) -> Path:
        """Create the tracking record CSV from JSON descriptor files.

        Reads each JSON file, extracts output configuration, checks
        which output files exist on disk, and writes a summary CSV.

        Returns:
            Path to the created record file.
        """
        records = []
        current_sbdb_version = sbdb.__version__

        for json_path in self.json_files:
            try:
                with open(json_path) as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Warning: Could not read '{json_path}': {e}")
                continue

            reference_class = data.get("reference_class", "")
            output_config = data.get("output", None)

            if output_config is None:
                print(
                    f"Warning: '{json_path}' has no output config, "
                    "skipping."
                )
                continue

            # Extract output fields
            folder = output_config.get("folder", ".")
            filename = output_config.get("filename", "output")
            filetypes = output_config.get("filetypes", ["csv"])

            # Build output file paths
            output_files = [
                os.path.join(folder, f"{filename}.{ft}")
                for ft in filetypes
            ]

            # Get reference package version from top-level module name
            ref_package = reference_class.split(".")[0] if reference_class else ""
            ref_version = (
                get_package_version(ref_package) if ref_package else ""
            )

            # Get record count from first CSV output file (if exists)
            record_count = ""
            for fp in output_files:
                meta = get_file_metadata(fp)
                if meta["record_count"] is not None:
                    record_count = meta["record_count"]
                    break

            record = {
                "dataset_name": filename,
                "json_descriptor": json_path,
                "reference_class": reference_class,
                "reference_package_version": ref_version,
                "sbdb_version": current_sbdb_version,
                "output_folder": folder,
                "filetypes": ", ".join(filetypes),
                "output_files": ", ".join(output_files),
                "record_count": record_count,
                "last_generated": "",
                "notes": "",
            }
            records.append(record)

        # Write the record CSV
        with open(self.record_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=self.FIELDNAMES
            )
            writer.writeheader()
            writer.writerows(records)

        print(
            f"Created '{self.record_file}' with "
            f"{len(records)} dataset(s)"
        )
        return self.record_file

    def get_record(self) -> pd.DataFrame:
        """Read and return the tracking record as a DataFrame.

        Returns:
            DataFrame of the tracking record, or empty DataFrame
            if the record file does not exist.
        """
        if not self.record_file.exists():
            print(
                f"Record file '{self.record_file}' not found. "
                "Run initialise_record() first."
            )
            return pd.DataFrame(columns=self.FIELDNAMES)
        return pd.read_csv(self.record_file, dtype=str, keep_default_na=False)

    def print_record(self, dataset_name: str | None = None) -> None:
        """Print a formatted summary of one or all tracked datasets.

        Args:
            dataset_name: Name of a specific dataset to print.
                If None (default), prints all datasets.
        """
        df = self.get_record()
        if df.empty:
            return

        if dataset_name is not None:
            df = df[df["dataset_name"] == dataset_name]
            if df.empty:
                print(f"Dataset '{dataset_name}' not found in record.")
                return

        for _, row in df.iterrows():
            print(f"\n  Dataset: {row['dataset_name']}")
            print(f"    JSON descriptor:  {row['json_descriptor']}")
            print(f"    Reference class:  {row['reference_class']}")
            print(
                "    Package version:  "
                f"{row['reference_package_version']}"
            )
            print(f"    SBDB version:     {row['sbdb_version']}")
            print(f"    Output folder:    {row['output_folder']}")
            print(f"    File types:       {row['filetypes']}")
            print(f"    Output files:     {row['output_files']}")
            print(f"    Record count:     {row['record_count']}")
            print(f"    Last generated:   {row['last_generated']}")
            print(f"    Notes:            {row['notes']}")

    def update_record(
        self,
        dataset_name: str,
        notes: str | None = None,
    ) -> None:
        """Update a dataset's record after generation.

        Sets the last_generated timestamp, refreshes package versions,
        and updates the record count from the output CSV file.

        Args:
            dataset_name: Name of the dataset to update.
            notes: Optional notes to set on the record.
        """
        df = self.get_record()
        if df.empty:
            print("No record file found. Run initialise_record() first.")
            return

        mask = df["dataset_name"] == dataset_name
        if not mask.any():
            print(f"Dataset '{dataset_name}' not found in record.")
            return

        # Update timestamp
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.loc[mask, "last_generated"] = now

        # Update package versions
        df.loc[mask, "sbdb_version"] = sbdb.__version__
        ref_class = df.loc[mask, "reference_class"].iloc[0]
        if ref_class:
            ref_package = ref_class.split(".")[0]
            df.loc[mask, "reference_package_version"] = (
                get_package_version(ref_package)
            )

        # Update record count from output files
        output_files_str = df.loc[mask, "output_files"].iloc[0]
        if pd.notna(output_files_str):
            for fp in output_files_str.split(", "):
                meta = get_file_metadata(fp.strip())
                if meta["record_count"] is not None:
                    df.loc[mask, "record_count"] = str(
                        meta["record_count"]
                    )
                    break

        # Update notes if provided
        if notes is not None:
            df.loc[mask, "notes"] = notes

        # Save
        df.to_csv(self.record_file, index=False)
        print(
            f"Updated '{dataset_name}' — "
            f"last_generated: {now}"
        )
