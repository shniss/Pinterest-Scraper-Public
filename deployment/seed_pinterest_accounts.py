#!/usr/bin/env python3
"""
Seed Pinterest accounts into MongoDB

This script reads Pinterest account data from a JSON file and inserts them into MongoDB.
It supports environment variable passwords (e.g., "env:PIN_PASSWORD_1") and is idempotent.
"""

import os
import json
import sys
from typing import Dict, Any, List
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_mongodb_connection() -> MongoClient:
    """Create MongoDB connection from environment variables."""
    mongodb_uri = os.getenv('MONGO_URI')
    if not mongodb_uri:
        logger.error("MONGODB_URI environment variable not set")
        sys.exit(1)
    
    try:
        client = MongoClient(mongodb_uri)
        # Test connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)

def resolve_password(password: str) -> str:
    """Resolve password that may reference environment variables."""
    if password.startswith('env:'):
        env_var = password[4:]  # Remove 'env:' prefix
        resolved = os.getenv(env_var)
        if not resolved:
            logger.error(f"Environment variable {env_var} not found")
            sys.exit(1)
        return resolved
    return password

def load_accounts_data() -> List[Dict[str, Any]]:
    """Load Pinterest accounts from JSON file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, 'pinterest_accounts.sample.json')
    
    try:
        with open(json_path, 'r') as f:
            accounts = json.load(f)
        logger.info(f"Loaded {len(accounts)} accounts from {json_path}")
        return accounts
    except FileNotFoundError:
        logger.error(f"Accounts file not found: {json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in accounts file: {e}")
        sys.exit(1)

def check_existing_accounts(db, accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check which accounts already exist and return only new ones."""
    collection = db.pinterest_agent.pinterest_accounts
    new_accounts = []
    
    for account in accounts:
        # Check if account with same email already exists
        existing = collection.find_one({"email": account["email"]})
        if existing:
            logger.info(f"Account {account['email']} already exists, skipping")
        else:
            new_accounts.append(account)
    
    return new_accounts

def insert_accounts(db, accounts: List[Dict[str, Any]]) -> None:
    """Insert accounts into MongoDB."""
    if not accounts:
        logger.info("No new accounts to insert")
        return
    
    collection = db.pinterest_agent.pinterest_accounts
    
    # Create unique index on email if it doesn't exist
    try:
        collection.create_index("email", unique=True)
        logger.info("Created unique index on email field")
    except Exception as e:
        logger.warning(f"Index creation failed (may already exist): {e}")
    
    inserted_count = 0
    for account in accounts:
        try:
            # Resolve password if it references environment variable
            if "password" in account:
                account["password"] = resolve_password(account["password"])
            
            # Add timestamps
            from datetime import datetime
            account["created_at"] = datetime.utcnow()
            account["updated_at"] = datetime.utcnow()
            
            # Insert account
            result = collection.insert_one(account)
            logger.info(f"Inserted account {account['email']} with ID: {result.inserted_id}")
            inserted_count += 1
            
        except DuplicateKeyError:
            logger.warning(f"Account {account['email']} already exists (duplicate key)")
        except Exception as e:
            logger.error(f"Failed to insert account {account['email']}: {e}")
    
    logger.info(f"Successfully inserted {inserted_count} new accounts")

def main():
    """Main function to seed Pinterest accounts."""
    logger.info("Starting Pinterest accounts seeding...")
    
    # Connect to MongoDB
    client = get_mongodb_connection()
    db = client.pinterest_agent  # Explicitly use pinterest_agent database
    logger.info(f"Using database: {db}")
    
    try:
        # Load accounts data
        accounts = load_accounts_data()
        
        # Check for existing accounts
        new_accounts = check_existing_accounts(db, accounts)
        
        # Insert new accounts
        insert_accounts(db, new_accounts)
        
        logger.info("Pinterest accounts seeding completed successfully!")
        
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main() 