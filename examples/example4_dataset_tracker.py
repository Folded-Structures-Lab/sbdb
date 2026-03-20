"""
SBDB Example 4: Dataset Tracker

This example demonstrates how to use the DatasetTracker to create a
tracking record from a list of ObjectSet JSON descriptor files, and
then update the record after generating a dataset.
"""

from sbdb import DatasetTracker, ObjectSet


def main():
    """Demonstrate DatasetTracker functionality."""

    print("SBDB Example 4: Dataset Tracker")
    print("=" * 60)

    # Define the list of ObjectSet JSON descriptor files to track
    json_files = [
        "examples/example2_bolt.json",
        "examples/example3_bolt_group.json",
    ]

    # Step 1: Create the tracker and initialise the record
    print("\n1. Creating DatasetTracker and initialising record...")
    tracker = DatasetTracker(
        json_files=json_files,
        record_file="examples/output_datasets/dataset_record.csv",
    )
    tracker.initialise_record()

    # Step 2: Print the record before generation
    print("\n2. Record before generation:")
    tracker.print_record()

    # Step 3: Generate the example2_bolt dataset
    print("\n3. Generating example2_bolt dataset...")
    obj_set_filename = "examples/example2_bolt.json"
    obj_set, exported_files = ObjectSet.from_json(obj_set_filename)
    print(f"   Created {len(obj_set.object_set)} objects")
    for f in exported_files:
        print(f"   Exported to: {f}")

    # Step 4: Update the tracker record after generation
    print("\n4. Updating tracker record...")
    dataset_name = tracker.get_dataset_name(obj_set_filename)
    tracker.update_record(
        dataset_name=dataset_name,
        notes="Generated via example4",
    )

    # Step 5: Print the updated record
    print("\n5. Record after generation:")
    tracker.print_record("example2_bolt_library")

    # Bonus Step: Create the tracking record from file
    print("\nBonus Step: Create the tracking record from file...")
    imported_tracker = DatasetTracker.from_record_file(
        "examples/output_datasets/dataset_record.csv"
    )
    imported_tracker.print_record()


if __name__ == "__main__":
    main()
