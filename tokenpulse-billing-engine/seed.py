"""
Database Seeding Script for TokenPulse.
"""
from app.database import init_db, seed_db

if __name__ == "__main__":
    print("[*] Initializing TokenPulse SQLite database schema...")
    init_db()
    print("[*] Seeding default test tenants and initial quotas...")
    seed_db()
    print("[✓] Seed complete. Ready to meter and bill.")
