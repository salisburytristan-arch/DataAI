#!/usr/bin/env python3
"""
ArcticCodex seed script - creates initial admin user and org for first-time setup.

Usage:
    python seed.py
    
Sets up:
    - Organization: "default"
    - Admin user: (prompt for email/password)
    - Initial audit trail entry
"""

import os
import sys
import getpass
from uuid import uuid4
from datetime import datetime

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'core', 'src'))

from models import Organization, User, UserRole, AuditEvent, EventType
from db import get_db, init_database
import bcrypt

def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def main():
    """Run seeding script."""
    print("=" * 60)
    print("ArcticCodex First-Time Setup")
    print("=" * 60)
    
    try:
        # Initialize database
        print("\n[1/4] Initializing database connection...")
        db = get_db()
        print("✓ Connected to Supabase")
        
        # Check if org already exists
        print("\n[2/4] Checking for existing organization...")
        with db.get_session() as session:
            existing_org = session.query(Organization).filter_by(name='default').first()
            if existing_org:
                print("✗ Organization already exists!")
                print(f"  ID: {existing_org.id}")
                print(f"  Name: {existing_org.display_name}")
                return
        
        # Create organization
        print("\n[3/4] Creating organization...")
        org = Organization(
            id=str(uuid4()),
            name='default',
            display_name='My Organization',
            settings={},
            is_active=True
        )
        
        # Get admin credentials
        print("\nAdmin User Setup:")
        email = input("  Email: ").strip()
        
        # Validate email
        with db.get_session() as session:
            existing_user = session.query(User).filter_by(email=email).first()
            if existing_user:
                print(f"✗ Email already registered!")
                return
        
        password = getpass.getpass("  Password (min 8 chars): ")
        if len(password) < 8:
            print("✗ Password must be at least 8 characters!")
            return
        
        password_confirm = getpass.getpass("  Confirm password: ")
        if password != password_confirm:
            print("✗ Passwords don't match!")
            return
        
        full_name = input("  Full Name: ").strip()
        
        # Create user
        user = User(
            id=str(uuid4()),
            org_id=org.id,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True
        )
        
        # Save to database
        print("\n[4/4] Saving to database...")
        with db.get_session() as session:
            session.add(org)
            session.flush()  # Flush to get org.id
            
            session.add(user)
            session.flush()
            
            # Create audit event
            audit_event = AuditEvent(
                id=str(uuid4()),
                org_id=org.id,
                event_type=EventType.AUTH,
                timestamp=datetime.utcnow(),
                actor=email,
                payload={
                    'action': 'initial_setup',
                    'message': 'Organization and admin user created'
                },
                event_hash='0' * 64,  # Genesis event
                prev_hash='0' * 64
            )
            session.add(audit_event)
            session.commit()
        
        print("\n" + "=" * 60)
        print("✓ Setup Complete!")
        print("=" * 60)
        print(f"\nOrganization:")
        print(f"  Name: {org.display_name}")
        print(f"  ID: {org.id}")
        print(f"\nAdmin User:")
        print(f"  Email: {email}")
        print(f"  Name: {full_name}")
        print(f"\nNext steps:")
        print(f"  1. Start ArcticCodex: python -m uvicorn packages.core.src.app:app --reload")
        print(f"  2. Open: http://localhost:8000")
        print(f"  3. Login with your admin credentials")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
