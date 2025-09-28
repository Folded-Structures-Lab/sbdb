"""
SBDB Example 2: Australian Bolt Library Generation

This example demonstrates SBDB core functionality using the steelas package
to generate a comprehensive library of Australian standard bolts.

NOTE - requires steelas v0.2.0 python package to be installed
"""

from steelas.component.bolt import Bolt
from sbdb import ObjectSet, DesignVariableSet


def main():
    """Generate Australian bolt library using SBDB framework."""
    
    print("SBDB Example 2: Australian Bolt Library Generation")
    print("=" * 60)
    
    # Step 1: Load design variables from JSON file
    print("\n1. Loading design variables from JSON file...")
    input_file = "examples/example2_AUS_bolt.json"
    
    try:
        des_vars = DesignVariableSet.from_json(input_file)
        print(f"   ✓ Successfully loaded design variables from '{input_file}'")
        print(f"   ✓ Generated {len(des_vars.param_list)} parameter combinations")
        
        # Display the design variable structure
        print(f"   ✓ Design variable categories: {list(des_vars.design_var_sets.keys())}")
        for var_name, var_values in des_vars.design_var_sets.items():
            print(f"     - {var_name}: {len(var_values)} options")
        
    except FileNotFoundError:
        print(f"   ✗ Error: Could not find '{input_file}'. Please ensure the file exists.")
        return
    except Exception as e:
        print(f"   ✗ Error loading design variables: {e}")
        return
    
    # Step 2: Display sample parameter combinations
    print("\n2. Sample parameter combinations (first 5):")
    for i, params in enumerate(des_vars.param_list[:5]):
        print(f"   {i+1}: {params}")
    if len(des_vars.param_list) > 5:
        print(f"   ... and {len(des_vars.param_list) - 5} more combinations")
    
    # Step 3: Define component class and reporting attributes
    print("\n3. Setting up object generation parameters...")
    component_class = Bolt
    report_attributes = [
        "name",
        "bolt_des",
        "bolt_cat", 
        "threads_included",
        "d_f",
        "d_h",
        "a_e_min",
        "s_p_min",
        "phiV_f",
        "phiN_tf",
    ]
    print(f"   ✓ Reference class: {component_class.__name__}")
    print(f"   ✓ Reporting {len(report_attributes)} attributes per bolt")
    print(f"   ✓ Attributes: {', '.join(report_attributes)}")
    
    # Step 4: Generate object set
    print("\n4. Generating object set using SBDB ObjectSet class...")
    print("   This process instantiates each bolt and calculates properties...")
    
    object_set = ObjectSet(
        reference_class=component_class,
        param_list=des_vars.param_list,
        report_attrs=report_attributes,
    )
    
    print(f"   ✓ Successfully created {len(object_set.object_set)} bolt objects")
    
    # Check for any skipped objects
    if hasattr(object_set, 'skipped_indices') and object_set.skipped_indices:
        print(f"   ⚠ Skipped {len(object_set.skipped_indices)} parameter combinations due to errors")
    
    # Step 5: Analyse the generated object library
    print("\n5. Analysing generated bolt library:")
    df = object_set.object_library
    print(f"   ✓ Generated library with {len(df)} bolts")
    print(f"   ✓ Library contains {len(df.columns)} attributes per bolt")
    
    # Basic statistics
    if 'bolt_cat' in df.columns:
        categories = df['bolt_cat'].value_counts()
        print(f"   ✓ Bolt categories:")
        for cat, count in categories.items():
            print(f"     - {cat}: {count} bolts")
    
    if 'd_f' in df.columns:
        diameters = df['d_f'].unique()
        print(f"   ✓ Bolt diameters: {sorted(diameters)} mm")
    
    # Step 6: Display sample results
    print("\n6. Sample bolt library data (first 5 bolts):")
    print(df.head())
    
    # Step 7: Export results
    print("\n7. Exporting results...")
    output_file = "examples/example2_AUS_bolt_library.csv"
    df.to_csv(output_file, index=False)
    print(f"   ✓ Library exported to '{output_file}'")
    
    # Summary
    print(f"\n" + "=" * 60)
    print("SBDB Generation Summary:")
    print(f"   • Input combinations: {len(des_vars.param_list)}")
    print(f"   • Successfully generated: {len(df)} bolts")
    print(f"   • Attributes per bolt: {len(report_attributes)}")
    print(f"   • Output file: {output_file}")
    print("Generation completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
