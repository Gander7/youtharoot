#!/usr/bin/env python3
"""
Generate a secure SECRET_KEY for the Youth Attendance API.

Usage:
    python generate_secret_key.py

This script generates a cryptographically secure random key suitable for
use as a SECRET_KEY in JWT token signing for production deployments.
"""

import secrets
import sys

def generate_secret_key(length=32):
    """Generate a secure random key encoded as URL-safe base64."""
    return secrets.token_urlsafe(length)

def main():
    print("🔐 Youth Attendance API - SECRET_KEY Generator")
    print("=" * 50)
    
    # Generate a secure key
    secret_key = generate_secret_key()
    
    print(f"Generated SECRET_KEY:")
    print(f"{secret_key}")
    print()
    print("📋 Copy and paste this key into your environment variables:")
    print(f"SECRET_KEY={secret_key}")
    print()
    print("💡 Usage Instructions:")
    print("  • For Railway: Add this as an environment variable in your service")
    print("  • For local .env: Add this line to your .env file")
    print("  • Keep this key secure and never commit it to version control")
    print()
    print("🔄 Run this script again to generate a new key if needed.")

if __name__ == "__main__":
    main()