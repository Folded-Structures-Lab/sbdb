"""
MongoDB connection utilities for SBDB framework.

Provides functions to connect to various MongoDB instances including
localhost and remote servers via SSH tunneling.
"""

import os
from ssh_pymongo import MongoSession
from pymongo import MongoClient
from dotenv import load_dotenv


def connect_to_db(db_name: str) -> tuple[MongoSession, MongoClient]:
    """
    Switching method to connect to localhost or uqcloud.
    
    Args:
        db_name: Database connection type ("localhost" or "uqcloud")
        
    Returns:
        Tuple of (session, client) where session may be None for localhost
    """
    if db_name == "localhost":
        return connect_to_localhost()
    elif db_name == "uqcloud":
        return connect_to_uqcloud()
    else:
        raise ValueError(f"Unknown database connection type: {db_name}")


def connect_to_localhost() -> tuple[MongoSession, MongoClient]:
    """
    Connect to localhost mongodb server.
    
    Returns:
        Tuple of (None, MongoClient) - session is None for localhost connections
    """
    conn_str = "mongodb://localhost:27017"
    client = MongoClient(conn_str)
    session = None
    return session, client


def connect_to_uqcloud() -> tuple[MongoSession, MongoClient]:
    """
    Connect to uqcloud mongodb server (requires UQ VPN).
    
    Uses SSH tunneling to connect to remote MongoDB instance.
    Requires environment variables: MONGO_HOST, SSH_USERNAME, SSH_PW
    
    Returns:
        Tuple of (MongoSession, MongoClient)
    """
    load_dotenv()
    MONGO_HOST = os.getenv("MONGO_HOST")
    SSH_USERNAME = os.getenv("SSH_USERNAME")
    SSH_PW = os.getenv("SSH_PW")

    if not all([MONGO_HOST, SSH_USERNAME, SSH_PW]):
        raise ValueError("Missing required environment variables for uqcloud connection")

    session = MongoSession(
        MONGO_HOST,
        port=22,
        user=SSH_USERNAME,
        password=SSH_PW,
        uri="mongodb:127.0.0.1:27017",
    )
    client = session.connection
    return session, client
