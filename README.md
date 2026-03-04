# SBDB: Set-Based Database Framework

A framework for generalised set-based structural design data generation and verification.

## Overview

SBDB provides a systematic approach to generating and managing large datasets for structural design applications. The framework uses set-based design principles to create comprehensive design spaces through Cartesian products of design variables, enabling systematic exploration and optimisation of structural systems.

## Features

- **Set-Based Design Variable Management**: Generate comprehensive design spaces using Cartesian products
- **Object Set Generation**: Create large datasets of structural objects with error handling and progress tracking
- **Data Verification**: Compare generated data against external verification sources with detailed error analysis
- **Database Integration**: MongoDB utilities for storing and managing large structural datasets
- **Extensible Framework**: Domain-agnostic core with easy extension to different structural materials and systems

## Installation

### Development Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sbdb.git
cd sbdb

# Install in development mode
pip install -e .
```

### Dependencies

- Python ≥ 3.8
- pandas ≥ 1.3.0
- numpy ≥ 1.20.0
- pymongo ≥ 4.0.0
- ssh-pymongo ≥ 0.3.0
- python-dotenv ≥ 0.19.0

## Package Structure

```
sbdb/
├── src/sbdb/                          # Core SBDB framework
│   ├── __init__.py
│   ├── sets.py                        # Core set-based data structures
│   └── database/                      # Database utilities
│       ├── __init__.py
│       ├── connection.py              # MongoDB connection utilities
│       ├── population.py              # Database population functions
│       └── utils.py                   # General I/O utilities
├── examples/                          # Application examples
│   └── steel_structural_design/       # Steel structural design examples
│       ├── __init__.py
│       ├── steel_utils.py             # Steel-specific utilities
│       ├── generate_connections.py    # Connection generation example
│       ├── verify_steel_db.py         # Verification example
│       ├── populate_steel_db.py       # Database population example
│       └── data/                      # Steel design data
│           ├── input_data/            # Raw input data
│           ├── design_variable_sets/  # Design variable definitions
│           ├── collections_csv/       # Generated CSV collections
│           ├── collections_json/      # Generated JSON collections
│           ├── verification/          # Verification data sources
│           ├── verification_results/  # Verification results
│           └── verification_reports/  # Verification reports
├── pyproject.toml                     # Package configuration
├── README.md                          # This file
└── LICENSE                           # License file
```

## Quick Start

### Basic Usage

```python
from sbdb import DesignVariableSet, ObjectSet, VerifiedObjectLibrary

# 1. Define design variables
design_vars = {
    "length": [100, 200, 300],
    "width": [50, 75, 100],
    "material": ["steel", "aluminum"]
}

# 2. Create design variable set
dvs = DesignVariableSet(design_var_sets=design_vars)
print(f"Generated {len(dvs.param_list)} parameter combinations")

# 3. Generate object set (requires your structural class)
# os = ObjectSet(
#     reference_class=YourStructuralClass,
#     param_list=dvs.param_list
# )

# 4. Verify against external data (optional)
# vdf = VerifiedObjectLibrary(
#     object_library=os.object_library,
#     verification_library=verification_data,
#     lookup_index="name"
# )
```

### Database Operations

```python
from sbdb.database import connect_to_db, get_database, populate_db

# Connect to database
session, client = connect_to_db("localhost")
db = get_database(client, "your_database")

# Populate collections
population_list = [("collection_name", "json_filename")]
populate_db(db, population_list, "/path/to/json/files")
```

## Steel Structural Design Example

The `examples/steel_structural_design/` directory contains a comprehensive example demonstrating the framework's application to steel structural design:

### Running the Steel Examples

```python
# Generate steel connections
python -m examples.steel_structural_design.generate_connections

# Verify generated data
python -m examples.steel_structural_design.verify_steel_db

# Populate database
python -m examples.steel_structural_design.populate_steel_db
```

### Steel Example Features

- **Component Generation**: Bolts, welds, plates, and bolt groups
- **Member Generation**: Open sections, hollow sections, and tee sections
- **Connection Generation**: FEP and WSP connection types
- **Verification**: Comparison against ASI and Tekla verification data
- **Database Integration**: MongoDB population and management

## Core Classes

### DesignVariableSet

Manages design variable sets for combinatorial design space generation.

```python
# From dictionary
dvs = DesignVariableSet(design_var_sets={"var1": [1,2,3], "var2": ["a","b"]})

# From JSON file
dvs = DesignVariableSet.from_json("design_vars.json")

# Access parameter combinations
print(len(dvs.param_list))  # 6 combinations
```

### ObjectSet

Generates object sets from design variables using a reference class.

```python
os = ObjectSet(
    reference_class=MyStructuralClass,
    param_list=dvs.param_list,
    report_attrs=["attr1", "attr2", "attr3"]
)

# Access results
objects = os.object_set           # List of instantiated objects
dataframe = os.object_library     # Pandas DataFrame with attributes
```

### VerifiedObjectLibrary

Compares generated data against verification sources.

```python
vdf = VerifiedObjectLibrary(
    object_library=generated_df,
    verification_library=verification_df,
    lookup_index="name"
)

# Access verification results
errors = vdf.result_df      # Detailed error calculations
report = vdf.report_df      # Summary statistics
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this framework in your research, please cite:

```bibtex
@software{sbdb_framework,
  title={SBDB: Set-Based Database Framework for Structural Design},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/sbdb}
}
```

## Acknowledgments

- Steel structural design examples use the `steelas` package
- Verification data sourced from ASI and Tekla software
- Framework developed for academic research in structural optimisation
