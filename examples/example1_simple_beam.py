"""
Basic SBDB Example - No External Dependencies Required

This example demonstrates the core SBDB functionality using a simple beam class.
No external packages are required to run this example.

"""

from sbdb import ObjectSet


class SimpleBeam:
    """
    A simple structural beam class for demonstration purposes.

    This class calculates basic beam properties without requiring external dependencies.
    """

    def __init__(
        self, length: float, width: float, height: float, material: str = "steel"
    ):
        self.length = length  # mm
        self.width = width  # mm
        self.height = height  # mm
        self.material = material

        # Calculate derived properties
        self.area = self.width * self.height  # mm²
        self.volume = self.area * self.length  # mm³
        self.second_moment = (self.width * self.height**3) / 12  # mm⁴

        # Material properties (simplified)
        self.density = (
            7850 if material == "steel" else 2700
        )  # kg/m³ (steel or aluminium)
        self.mass = (self.volume * self.density) / 1e9  # kg (convert mm³ to m³)

        # Create a unique name
        self.name = f"{material}_{int(length)}x{int(width)}x{int(height)}"


def main():
    """Demonstrate basic SBDB functionality with simple beam example."""

    print("SBDB Basic Example")
    print("=" * 50)

    # Generate object set from JSON descriptor file
    print("\n1. Generating object set from JSON descriptor...")
    obj_set, exported_file = ObjectSet.from_json("examples/example1_simple_beam.json")
    print(f"   Successfully created {len(obj_set.object_set)} beam objects")
    if exported_file:
        print(f"   Exported to: {exported_file}")

    # Display results
    print("\n2. Object Library:")
    df = obj_set.object_library
    print(df)


if __name__ == "__main__":
    main()
