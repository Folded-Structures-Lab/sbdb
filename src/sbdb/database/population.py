"""
Database population utilities for SBDB framework.

Provides functions for managing MongoDB collections, including creation,
population, and deletion operations with user confirmation.
"""

import json
from typing import List, Tuple
from pymongo import MongoClient
from pymongo.database import Database

PopulationList = List[Tuple[str, str]]


def get_database(client: MongoClient, db_name: str) -> Database:
    """
    Retrieve a database.

    Checks if the specified database exists.
    If the database does not exist, it will be created when data is first inserted.
    
    Args:
        client: MongoDB client instance
        db_name: Name of the database to retrieve
        
    Returns:
        Database instance
    """
    db_list = client.list_database_names()
    db_status = "exists" if db_name in db_list else "created"
    print(f"{db_name} {db_status}.")
    db = client[db_name]
    return db


def drop_all_collections_USE_WITH_CAUTION(db: Database) -> None:
    """
    Drop all collections in the specified database.

    Lists all collections in the database and prompts the user to confirm drop them or not.
    This operation is irreversible and should be used with caution.
    
    Args:
        db: Database instance
    """
    col_list = db.list_collection_names()
    print("db collections:")
    print(col_list)

    user_input = input(f"delete all collections (yes/no)?")

    if user_input.lower() == "yes":
        user_input2 = input(f"are you sure (yes/no)?")
        if user_input2.lower() == "yes":
            for coll_name in col_list:
                coll = db[coll_name]
                coll.drop()
                print(f"{coll_name} dropped.")


def drop_new_collections(db: Database, population_list: PopulationList) -> None:
    """
    Checks and optionally drops existing collections in a database based on a given list of new collection names, with user confirmation.

    Args:
        db: Database instance
        population_list: A list of tuples (collection_name, filename) to be checked against the database.

    The function prompts the user to confirm the deletion of each existing collection found in the list of new collection names.
    """
    new_colls = unique_collection_names(population_list)
    col_list = db.list_collection_names()

    for coll_name in new_colls:
        if coll_name in col_list:
            # check whether to overwrite (wipe out) collection if it already exists
            get_input = True

            while get_input:
                user_input = input(
                    f"{coll_name} collection exists - delete and replace this collection (yes/no)?\n"
                )

                if user_input.lower() == "yes":
                    get_input = False
                    coll = db[coll_name]
                    coll.drop()
                    print(f"{coll_name} dropped.")
                elif user_input.lower() == "no":  # NOTE: if no, data will be added into existing collection when populate_db is called
                    print("process stopped")
                    break
                else:
                    print("Type yes/no")


def unique_collection_names(population_list: PopulationList) -> List[str]:
    """
    Extract unique collection names from population list.
    
    Args:
        population_list: List of (collection_name, filename) tuples
        
    Returns:
        List of unique collection names
    """
    new_colls = list(set(coll_name for coll_name, _ in population_list))
    return new_colls


def populate_db(db: Database, population_list: PopulationList, json_path: str) -> None:
    """
    Populate selected collections in the database with data from JSON files.
    
    Args:
        db: Database instance
        population_list: List of (collection_name, filename) tuples
        json_path: Path to directory containing JSON files
    """
    new_colls = unique_collection_names(population_list)  # all collections that to be populated
    col_list = db.list_collection_names()  # existing collections

    for coll_name in new_colls:
        if coll_name not in col_list:
            print(f"{coll_name} created.")

    user_input = input(f"populate ALL collections in the Database? only populate newly added collection types if no. (yes/no)")

    for coll_name, fname in population_list:
        if user_input == "yes" or (user_input == "no" and coll_name not in col_list):
            # NOTE: if yes - all collections will be populated, this may cause data duplication.
            # NOTE: if no - only populate when a collection types does not exist/have been deleted, cannot add new data to existing collections.
            file_path = f"{json_path}/{fname}.json"
            coll = db[coll_name]

            try:
                with open(file_path) as f:
                    file_data = json.load(f)

                x = coll.insert_many(file_data)
                num_inserted = len(x.inserted_ids)
                print(f"{fname} added to {coll_name} with {num_inserted} records created.")
            except FileNotFoundError:
                print(f"Warning: File {file_path} not found, skipping {fname}")
            except Exception as e:
                print(f"Error processing {fname}: {e}")
