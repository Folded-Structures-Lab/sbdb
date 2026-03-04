#!/usr/bin/env python3
"""
Test script for core SBDB framework functionality.

This script tests the basic imports and functionality of the refactored SBDB package
to ensure the core framework is working correctly.
"""

def test_core_imports():
    """Test that all core SBDB components can be imported."""
    print("Testing core SBDB imports...")
    
    try:
        from sbdb import DesignVariableSet, ObjectSet, VerifiedObjectLibrary
        print("✅ Core classes imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import core classes: {e}")
        return False
    
    try:
        from sbdb.database import connect_to_db, get_database, populate_db
        print("✅ Database utilities imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import database utilities: {e}")
        return False
    
    return True


def test_design_variable_set():
    """Test DesignVariableSet functionality."""
    print("\nTesting DesignVariableSet...")
    
    try:
        from sbdb import DesignVariableSet
        
        # Test basic functionality
        design_vars = {
            "length": [100, 200, 300],
            "width": [50, 75],
            "material": ["steel", "aluminum"]
        }
        
        dvs = DesignVariableSet(design_var_sets=design_vars)
        expected_combinations = 3 * 2 * 2  # 12 combinations
        
        if len(dvs.param_list) == expected_combinations:
            print(f"✅ Generated {len(dvs.param_list)} parameter combinations (expected {expected_combinations})")
        else:
            print(f"❌ Expected {expected_combinations} combinations, got {len(dvs.param_list)}")
            return False
            
        # Test value function
        val_fn = dvs.create_value_function()
        if isinstance(val_fn, dict) and len(val_fn) == 3:
            print("✅ Value function created successfully")
        else:
            print("❌ Value function creation failed")
            return False
            
    except Exception as e:
        print(f"❌ DesignVariableSet test failed: {e}")
        return False
    
    return True


def test_database_imports():
    """Test database utility imports."""
    print("\nTesting database utilities...")
    
    try:
        from sbdb.database.connection import connect_to_localhost
        from sbdb.database.utils import export_collection
        from sbdb.database.population import get_database
        print("✅ Database utility functions imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import database utilities: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 50)
    print("SBDB Core Framework Test")
    print("=" * 50)
    
    tests = [
        test_core_imports,
        test_design_variable_set,
        test_database_imports
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! SBDB core framework is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
