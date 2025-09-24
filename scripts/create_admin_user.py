#!/usr/bin/env python3
"""
Script to create an admin user with hashed password for direct database insertion.
"""

import bcrypt
import getpass
import sys
from datetime import datetime

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def main():
    print("🔐 Admin User Creator for Youtharoot")
    print("=" * 40)
    
    # Get username
    username = input("Enter admin username: ").strip()
    if not username:
        print("❌ Username cannot be empty!")
        sys.exit(1)
    
    # Get password
    password = getpass.getpass("Enter admin password: ").strip()
    if not password:
        print("❌ Password cannot be empty!")
        sys.exit(1)
    
    # Confirm password
    password_confirm = getpass.getpass("Confirm admin password: ").strip()
    if password != password_confirm:
        print("❌ Passwords don't match!")
        sys.exit(1)
    
    # Hash the password
    print("\n🔄 Hashing password...")
    password_hash = hash_password(password)
    
    # Generate SQL statements
    current_time = datetime.utcnow().isoformat()
    
    print("\n✅ Admin user created successfully!")
    print("\n" + "=" * 60)
    print("SQL STATEMENTS TO INSERT ADMIN USER:")
    print("=" * 60)
    
    # For PostgreSQL
    print("\n-- PostgreSQL (for Railway/production):")
    postgresql_sql = f"""INSERT INTO users (username, password_hash, role, created_at, updated_at) 
VALUES ('{username}', '{password_hash}', 'admin', '{current_time}', '{current_time}');"""
    print(postgresql_sql)
    
    # For in-memory (development)
    print("\n-- For in-memory database (development), add to app/repositories/memory.py:")
    memory_code = f"""User(
    id=1,  # or next available ID
    username="{username}",
    password_hash="{password_hash}",
    role="admin",
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)"""
    print(memory_code)
    
    print("\n" + "=" * 60)
    print("SAVE THIS INFORMATION SECURELY!")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Password Hash: {password_hash}")
    print("=" * 60)

if __name__ == "__main__":
    main()