"""
SBDB Example 3: Australian Bolt Group Library Generation

This example demonstrates nested object set generation, where a design variable
(bolt) is itself an ObjectSet generated from a nested descriptor in the JSON file.

NOTE - requires steelas >=v0.2.0 python package to be installed
"""

from sbdb import ObjectSet


def main():
    """Generate Australian bolt group library using SBDB framework."""

    print("SBDB Example 3: Australian Bolt Group Library Generation")
    print("=" * 60)

    # Generate object set from JSON descriptor file
    # The "bolt" design variable is a nested ObjectSet that gets resolved
    # automatically from its nested descriptor in the JSON file.
    print("\n1. Generating bolt group object set from JSON descriptor...")
    obj_set, exported_files = ObjectSet.from_json(
        "examples/example3_bolt_group.json"
    )
    print(f"   Successfully created {len(obj_set.object_set)} bolt group objects")
    if exported_files:
        for f in exported_files:
            print(f"   Exported to: {f}")

    # Display sample results
    df = obj_set.object_library
    print(
        f"\n2. Library contains {len(df)} bolt groups"
        f" with {len(df.columns)} attributes"
    )
    print("\n3. Sample bolt group library data (first 10 rows):")
    print(df.head(10))


if __name__ == "__main__":
    main()
