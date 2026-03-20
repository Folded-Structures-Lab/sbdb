"""
SBDB Example 2: Australian Bolt Library Generation

This example demonstrates SBDB core functionality using the steelas package
to generate a comprehensive library of Australian standard bolts.

NOTE - requires steelas >=v0.2.0 python package to be installed
"""

from sbdb import ObjectSet


def main():
    """Generate Australian bolt library using SBDB framework."""

    print("SBDB Example 2: Australian Bolt Library Generation")
    print("=" * 60)

    # Generate object set from JSON descriptor file
    print("\n1. Generating object set from JSON descriptor...")
    obj_set, exported_files = ObjectSet.from_json("examples/example2_AUS_bolt.json")
    print(f"   Successfully created {len(obj_set.object_set)} bolt objects")
    if exported_files:
        for f in exported_files:
            print(f"   Exported to: {f}")

    # Display sample results
    df = obj_set.object_library
    print("\n2. Sample bolt library data (first 10 bolts):")
    print(df.head(10))


if __name__ == "__main__":
    main()
