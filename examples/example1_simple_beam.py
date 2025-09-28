"""
Basic SBDB Example - No External Dependencies Required

This example demonstrates the core SBDB functionality using a simple structural beam class.
No external packages (like steelas) are required to run this example.
"""

from sbdb import DesignVariableSet, ObjectSet


class SimpleBeam:
    """
    A simple structural beam class for demonstration purposes.
    
    This class calculates basic beam properties without requiring external dependencies.
    """
    
    def __init__(self, length: float, width: float, height: float, material: str = "steel"):
        self.length = length  # mm
        self.width = width    # mm  
        self.height = height  # mm
        self.material = material
        
        # Calculate derived properties
        self.area = self.width * self.height  # mm²
        self.volume = self.area * self.length  # mm³
        self.second_moment = (self.width * self.height**3) / 12  # mm⁴
        
        # Material properties (simplified)
        self.density = 7850 if material == "steel" else 2700  # kg/m³ (steel or aluminium)
        self.mass = (self.volume * self.density) / 1e9  # kg (convert mm³ to m³)
        
        # Create a unique name
        self.name = f"{material}_{int(length)}x{int(width)}x{int(height)}"


def main():
    """Demonstrate basic SBDB functionality with simple beam example."""
    
    print("SBDB Basic Example")
    print("=" * 50)
    
    # Step 1: Define design variables
    print("\n1. Defining design variables...")
    design_variables = {
        "length": [1000, 2000, 3000],      # mm
        "width": [100, 150, 200],          # mm
        "height": [200, 300, 400],         # mm  
        "material": ["steel", "aluminium"]
    }
    
    # Step 2: Create design variable set
    print("2. Creating design variable set...")
    dvs = DesignVariableSet(design_var_sets=design_variables)
    print(f"   Generated {len(dvs.param_list)} parameter combinations")
    
    # Display first few combinations
    print("   First 3 parameter combinations:")
    for i, params in enumerate(dvs.param_list[:3]):
        print(f"     {i+1}: {params}")
    
    # Step 3: Generate object set
    print("\n3. Generating object set...")
    report_attributes = [
        "name", "length", "width", "height", "material",
        "area", "volume", "second_moment", "mass"
    ]
    
    obj_set = ObjectSet(
        reference_class=SimpleBeam,
        param_list=dvs.param_list,
        report_attrs=report_attributes
    )
    
    print(f"   Successfully created {len(obj_set.object_set)} beam objects")
    
    # Step 4: Display results
    print("\n4. Object Library (first 10 rows):")
    print(obj_set.object_library.head(10))
    
    # Step 5: Basic analysis
    print("\n5. Basic Analysis:")
    df = obj_set.object_library
    
    # Group by material
    steel_beams = df[df['material'] == 'steel']
    alu_beams = df[df['material'] == 'aluminium']
    
    print(f"   Steel beams: {len(steel_beams)}")
    print(f"   Aluminium beams: {len(alu_beams)}")
    print(f"   Average steel beam mass: {steel_beams['mass'].mean():.2f} kg")
    print(f"   Average aluminium beam mass: {alu_beams['mass'].mean():.2f} kg")
    
    # Find lightest and heaviest beams
    lightest = df.loc[df['mass'].idxmin()]
    heaviest = df.loc[df['mass'].idxmax()]
    
    print(f"\n   Lightest beam: {lightest['name']} ({lightest['mass']:.2f} kg)")
    print(f"   Heaviest beam: {heaviest['name']} ({heaviest['mass']:.2f} kg)")
    
    # Step 6: Export results (optional)
    print("\n6. Exporting results...")
    df.to_csv("examples/example1_simple_beam.csv", index=False)
    print("   Results saved to 'examples/basic_beam_library.csv'")
    
    print("\nExample completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()
