"""
Migration script to move profile data from primary database to company-specific databases.

This script:
1. Reads all profiles from the primary database (data_store.db)
2. For each profile, identifies the user's company database
3. Creates the profile record in the company database
4. Optionally removes the profile from the primary database (with backup)

Usage:
    python migrate_profiles_to_company_db.py [--remove-from-primary] [--dry-run]
"""

import sys
import os
from pathlib import Path
import argparse
import shutil
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

from app.config import settings
from app.database.models import Profile, User

def get_primary_session():
    """Get session for primary database"""
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def get_company_session(company_db_name: str):
    """Get session for company database"""
    data_dir = Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent
    db_path = str(data_dir / company_db_name)

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Company database not found: {db_path}")

    db_url = f"sqlite:///{db_path}"
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def backup_primary_db():
    """Create backup of primary database before migration"""
    primary_db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    backup_path = f"{primary_db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    logger.info(f"Creating backup: {backup_path}")
    shutil.copy2(primary_db_path, backup_path)
    return backup_path

def migrate_profiles(dry_run=False, remove_from_primary=False):
    """
    Migrate profile data from primary database to company databases

    Args:
        dry_run: If True, only show what would be migrated without making changes
        remove_from_primary: If True, remove profiles from primary DB after migration
    """
    logger.info("Starting profile migration...")

    if not dry_run and remove_from_primary:
        backup_path = backup_primary_db()
        logger.info(f"✓ Backup created: {backup_path}")

    primary_db = get_primary_session()

    try:
        # Get all profiles from primary database
        profiles = primary_db.query(Profile).all()
        logger.info(f"Found {len(profiles)} profiles in primary database")

        if len(profiles) == 0:
            logger.info("No profiles to migrate")
            return

        migrated_count = 0
        skipped_count = 0
        error_count = 0

        for profile in profiles:
            try:
                # Get user to find their company database
                user = primary_db.query(User).filter(User.id == profile.user_id).first()

                if not user:
                    logger.warning(f"Profile {profile.id}: User {profile.user_id} not found - SKIPPING")
                    skipped_count += 1
                    continue

                if not user.company_database_name:
                    logger.warning(f"Profile {profile.id}: User {user.username} has no company database - SKIPPING")
                    skipped_count += 1
                    continue

                logger.info(f"Processing profile {profile.id} for user {user.username} (company DB: {user.company_database_name})")

                if dry_run:
                    logger.info(f"  [DRY RUN] Would migrate profile {profile.id} to {user.company_database_name}")
                    migrated_count += 1
                    continue

                # Get company database session
                company_db = get_company_session(user.company_database_name)

                try:
                    # Find the user in the company database (should be user_id=1 for admin)
                    company_user = company_db.query(User).filter(User.username == user.username).first()

                    if not company_user:
                        logger.warning(f"Profile {profile.id}: User {user.username} not found in company database - SKIPPING")
                        skipped_count += 1
                        continue

                    # Check if profile already exists in company database
                    existing_profile = company_db.query(Profile).filter(Profile.user_id == company_user.id).first()

                    if existing_profile:
                        logger.warning(f"Profile {profile.id}: Profile already exists in company database for user {company_user.username} - SKIPPING")
                        skipped_count += 1
                        continue

                    # Create profile in company database
                    new_profile = Profile(
                        user_id=company_user.id,
                        industry=profile.industry,
                        location=profile.location,
                        sustainability_target_kp1=profile.sustainability_target_kp1,
                        sustainability_target_kp2=profile.sustainability_target_kp2,
                        budget=profile.budget,
                        historical_data_path=profile.historical_data_path,
                        created_at=profile.created_at,
                        updated_at=profile.updated_at
                    )

                    company_db.add(new_profile)
                    company_db.commit()

                    logger.info(f"  ✓ Migrated profile {profile.id} to company database (new ID: {new_profile.id})")
                    migrated_count += 1

                    # Remove from primary database if requested
                    if remove_from_primary:
                        primary_db.delete(profile)
                        primary_db.commit()
                        logger.info(f"  ✓ Removed profile {profile.id} from primary database")

                except Exception as e:
                    company_db.rollback()
                    logger.error(f"  ✗ Error migrating profile {profile.id}: {e}")
                    error_count += 1
                finally:
                    company_db.close()

            except Exception as e:
                logger.error(f"✗ Error processing profile {profile.id}: {e}")
                error_count += 1

        # Summary
        logger.info("\n" + "="*60)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total profiles found:    {len(profiles)}")
        logger.info(f"Successfully migrated:   {migrated_count}")
        logger.info(f"Skipped:                 {skipped_count}")
        logger.info(f"Errors:                  {error_count}")
        logger.info("="*60)

        if dry_run:
            logger.info("\n[DRY RUN MODE] No changes were made to the databases")
        elif remove_from_primary:
            logger.info(f"\n✓ Profiles removed from primary database")
            logger.info(f"✓ Backup available at: {backup_path}")

    finally:
        primary_db.close()

def main():
    parser = argparse.ArgumentParser(
        description="Migrate profile data from primary database to company-specific databases"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes"
    )
    parser.add_argument(
        "--remove-from-primary",
        action="store_true",
        help="Remove profiles from primary database after migration (creates backup first)"
    )

    args = parser.parse_args()

    logger.info("Profile Migration Script")
    logger.info("="*60)

    if args.dry_run:
        logger.info("Running in DRY RUN mode - no changes will be made")

    if args.remove_from_primary and not args.dry_run:
        logger.warning("WARNING: Profiles will be REMOVED from primary database after migration")
        logger.warning("A backup will be created automatically")
        response = input("\nContinue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Migration cancelled")
            return

    try:
        migrate_profiles(dry_run=args.dry_run, remove_from_primary=args.remove_from_primary)
        logger.info("\n✓ Migration completed successfully")
    except Exception as e:
        logger.error(f"\n✗ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
