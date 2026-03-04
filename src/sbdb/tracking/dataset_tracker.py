"""
General Dataset Generation and Verification Tracking System

This module provides general utilities for tracking dataset generation, verification,
and database population activities with timestamps and package version information.
Can be extended for specific domain implementations.
"""

import os
import json
import csv
import pandas as pd
from datetime import datetime
from pathlib import Path
import importlib.util

# Constants
RECORD_FILE = "dataset_generation_record.csv"


def get_package_version(package_name):
    """Get version of an installed package."""
    try:
        import importlib.metadata
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return "Not installed"
    except Exception:
        return "Unknown"


def get_file_metadata(csv_path, json_path=None):
    """Get file metadata including record count and file sizes."""
    metadata = {
        'record_count': 0,
        'csv_size_mb': 0,
        'json_size_mb': 0,
        'csv_exists': False,
        'json_exists': False
    }
    
    # CSV metadata
    if csv_path and Path(csv_path).exists():
        metadata['csv_exists'] = True
        try:
            df = pd.read_csv(csv_path)
            metadata['record_count'] = len(df)
        except Exception as e:
            print(f"Error reading CSV {csv_path}: {e}")
        
        try:
            metadata['csv_size_mb'] = round(Path(csv_path).stat().st_size / (1024*1024), 2)
        except Exception:
            metadata['csv_size_mb'] = 0
    
    # JSON metadata
    if json_path and Path(json_path).exists():
        metadata['json_exists'] = True
        try:
            metadata['json_size_mb'] = round(Path(json_path).stat().st_size / (1024*1024), 2)
        except Exception:
            metadata['json_size_mb'] = 0
    
    return metadata


def categorise_collection(collection_name):
    """
    Default categorisation - should be overridden by domain-specific implementations.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        tuple: (category, dataset_type)
    """
    return 'general', 'dataset'


class DatasetTracker:
    """
    General dataset tracking class that can be extended for specific domains.
    """
    
    def __init__(self, base_dir=None, datasets_subdir="datasets", 
                 csv_subdir="collections_csv", json_subdir="collections_json",
                 record_filename="dataset_generation_record.csv"):
        """
        Initialise the dataset tracker.
        
        Args:
            base_dir: Base directory for the repository (defaults to parent of current file)
            datasets_subdir: Subdirectory containing datasets
            csv_subdir: Subdirectory containing CSV collections
            json_subdir: Subdirectory containing JSON collections  
            record_filename: Name of the tracking CSV file
        """
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.datasets_dir = self.base_dir / datasets_subdir
        self.csv_dir = self.datasets_dir / csv_subdir
        self.json_dir = self.datasets_dir / json_subdir
        self.record_file = record_filename
        self.record_path = self.base_dir / self.record_file
    
    def categorise_collection(self, collection_name):
        """
        Categorise a collection - should be overridden by subclasses.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            tuple: (category, dataset_type)
        """
        return categorise_collection(collection_name)
    
    def get_package_versions(self):
        """
        Get relevant package versions - should be overridden by subclasses.
        
        Returns:
            dict: Package versions
        """
        return {
            'main_package': 'Unknown',
            'framework_package': 'Unknown'
        }
    
    def initialise_record_file(self):
        """Create initial CSV record with all existing collections."""
        print("Initialising dataset generation record...")
        
        # Get all CSV collections
        csv_files = list(self.csv_dir.glob("*.csv")) if self.csv_dir.exists() else []
        
        records = []
        
        for csv_file in csv_files:
            collection_name = csv_file.stem
            
            # Find corresponding JSON file
            json_file = self.json_dir / f"{collection_name}.json"
            
            # Get metadata
            metadata = get_file_metadata(csv_file, json_file)
            
            # Categorise
            category, dataset_type = self.categorise_collection(collection_name)
            
            # Create record
            record = {
                'collection_name': collection_name,
                'category': category,
                'dataset_type': dataset_type,
                'last_generation_date': '',
                'dataset_verification_date': '',
                'database_population_date': '',
                'database_verification_date': '',
                'main_package_version': '',
                'framework_package_version': '',
                'record_count': metadata['record_count'],
                'csv_size_mb': metadata['csv_size_mb'],
                'json_size_mb': metadata['json_size_mb'],
                'csv_file_path': f"{self.datasets_dir.name}/{self.csv_dir.name}/{collection_name}.csv",
                'json_file_path': f"{self.datasets_dir.name}/{self.json_dir.name}/{collection_name}.json" if metadata['json_exists'] else '',
                'csv_exists': metadata['csv_exists'],
                'json_exists': metadata['json_exists'],
                'notes': f"Generated collection - {category}/{dataset_type}"
            }
            
            records.append(record)
        
        # Sort by category then by name
        records.sort(key=lambda x: (x['category'], x['collection_name']))
        
        # Write to CSV
        fieldnames = [
            'collection_name', 'category', 'dataset_type',
            'last_generation_date', 'dataset_verification_date', 
            'database_population_date', 'database_verification_date',
            'main_package_version', 'framework_package_version',
            'record_count', 'csv_size_mb', 'json_size_mb',
            'csv_file_path', 'json_file_path', 'csv_exists', 'json_exists',
            'notes'
        ]
        
        with open(self.record_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        
        print(f"✅ Created {self.record_file} with {len(records)} collections")
        return self.record_path
    
    def update_generation_record(self, collection_name, operation_type, notes=None):
        """
        Update the generation record with timestamp and package versions.
        
        Args:
            collection_name: Name of the collection
            operation_type: 'generation', 'dataset_verification', 'database_population', 'database_verification'
            notes: Optional additional notes
        """
        if not self.record_path.exists():
            print(f"Record file {self.record_file} not found. Creating new one...")
            self.initialise_record_file()
        
        # Read existing records
        df = pd.read_csv(self.record_path)
        
        # Find the collection
        mask = df['collection_name'] == collection_name
        if not mask.any():
            print(f"Warning: Collection {collection_name} not found in record. Adding new entry...")
            # Add new entry
            category, dataset_type = self.categorise_collection(collection_name)
            new_record = {
                'collection_name': collection_name,
                'category': category,
                'dataset_type': dataset_type,
                'last_generation_date': '',
                'dataset_verification_date': '',
                'database_population_date': '',
                'database_verification_date': '',
                'main_package_version': '',
                'framework_package_version': '',
                'record_count': 0,
                'csv_size_mb': 0,
                'json_size_mb': 0,
                'csv_file_path': f"{self.datasets_dir.name}/{self.csv_dir.name}/{collection_name}.csv",
                'json_file_path': f"{self.datasets_dir.name}/{self.json_dir.name}/{collection_name}.json",
                'csv_exists': False,
                'json_exists': False,
                'notes': f"Generated collection - {category}/{dataset_type}"
            }
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            mask = df['collection_name'] == collection_name
        
        # Update timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if operation_type == 'generation':
            df.loc[mask, 'last_generation_date'] = current_time
            # Also update package versions and file metadata
            package_versions = self.get_package_versions()
            df.loc[mask, 'main_package_version'] = package_versions.get('main_package', 'Unknown')
            df.loc[mask, 'framework_package_version'] = package_versions.get('framework_package', 'Unknown')
            
            # Update file metadata
            csv_path = self.csv_dir / f"{collection_name}.csv"
            json_path = self.json_dir / f"{collection_name}.json"
            metadata = get_file_metadata(csv_path, json_path)
            
            df.loc[mask, 'record_count'] = metadata['record_count']
            df.loc[mask, 'csv_size_mb'] = metadata['csv_size_mb']
            df.loc[mask, 'json_size_mb'] = metadata['json_size_mb']
            df.loc[mask, 'csv_exists'] = metadata['csv_exists']
            df.loc[mask, 'json_exists'] = metadata['json_exists']
            
        elif operation_type == 'dataset_verification':
            df.loc[mask, 'dataset_verification_date'] = current_time
        elif operation_type == 'database_population':
            df.loc[mask, 'database_population_date'] = current_time
        elif operation_type == 'database_verification':
            df.loc[mask, 'database_verification_date'] = current_time
        
        # Update notes if provided
        if notes:
            current_notes = df.loc[mask, 'notes'].iloc[0] if not pd.isna(df.loc[mask, 'notes'].iloc[0]) else ''
            df.loc[mask, 'notes'] = f"{current_notes}; {notes}" if current_notes else notes
        
        # Save updated records
        df.to_csv(self.record_path, index=False)
        
        print(f"✅ Updated {collection_name} - {operation_type} at {current_time}")
    
    def get_generation_status(self):
        """Get summary of generation status for all collections."""
        if not self.record_path.exists():
            print(f"Record file {self.record_file} not found.")
            return None
        
        df = pd.read_csv(self.record_path)
        
        # Summary statistics
        total_collections = len(df)
        generated = len(df[df['last_generation_date'] != ''])
        verified = len(df[df['dataset_verification_date'] != ''])
        populated = len(df[df['database_population_date'] != ''])
        db_verified = len(df[df['database_verification_date'] != ''])
        
        print(f"\n📊 Dataset Generation Status Summary")
        print(f"{'='*50}")
        print(f"Total Collections: {total_collections}")
        print(f"Generated: {generated} ({generated/total_collections*100:.1f}%)")
        print(f"Dataset Verified: {verified} ({verified/total_collections*100:.1f}%)")
        print(f"Database Populated: {populated} ({populated/total_collections*100:.1f}%)")
        print(f"Database Verified: {db_verified} ({db_verified/total_collections*100:.1f}%)")
        
        # Category breakdown
        print(f"\n📂 By Category:")
        category_counts = df['category'].value_counts()
        for category, count in category_counts.items():
            print(f"  {category}: {count} collections")
        
        return df


if __name__ == "__main__":
    # Basic functionality for testing
    import sys
    
    tracker = DatasetTracker()
    
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        tracker.initialise_record_file()
    else:
        tracker.get_generation_status()
