"""
SBDB Example 4: Dataset Tracker

This example demonstrates how to use the DatasetTracker to create a
tracking record from a list of ObjectSet JSON descriptor files.

The tracker reads the output configuration from each JSON file and
builds a summary CSV with dataset names, file paths, package versions,
and record counts.
"""

from sbdb import DatasetTracker


def main():
    """Demonstrate DatasetTracker functionality."""

    print("SBDB Example 4: Dataset Tracker")
    print("=" * 60)

    # Define the list of ObjectSet JSON descriptor files to track
    json_files = [
        "examples/example2_bolt.json"
    ]

    # Create the tracker
    print("\n1. Creating DatasetTracker...")
    tracker = DatasetTracker(
        json_files=json_files,
        record_file="examples/output_datasets/dataset_record.csv",
    )
    print(f"   Tracking {len(json_files)} JSON descriptor files")

    # Initialise the record
    print("\n2. Initialising dataset record...")
    record_path = tracker.initialise_record()

    # Display the record
    print(f"\n3. Dataset record saved to: {record_path}")
    df = tracker.get_record()

    print("\n   Record contents:")
    for _, row in df.iterrows():
        print(f"\n   Dataset: {row['dataset_name']}")
        print(f"     JSON descriptor:  {row['json_descriptor']}")
        print(f"     Reference class:  {row['reference_class']}")
        print(f"     Package version:  {row['reference_package_version']}")
        print(f"     SBDB version:     {row['sbdb_version']}")
        print(f"     Output folder:    {row['output_folder']}")
        print(f"     File types:       {row['filetypes']}")
        print(f"     Output files:     {row['output_files']}")
        print(f"     Record count:     {row['record_count']}")
        print(f"     Last generated:     {row['last_generated']}")
        print(f"     Notes:             {row['notes']}")




if __name__ == "__main__":
    main()
