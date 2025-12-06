"""
Script to add reports permissions to the database
"""
from sqlalchemy import create_engine, text
from loguru import logger
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings

def add_reports_permissions():
    """Add reports permissions to database"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        try:
            logger.info("Adding reports permissions...")

            # Check if permissions already exist
            result = conn.execute(text("SELECT name FROM permissions WHERE name LIKE 'reports:%'"))
            existing = [row[0] for row in result]

            permissions_to_add = [
                ('reports:view', 'View energy reports'),
                ('reports:generate', 'Generate energy reports'),
                ('reports:configure', 'Configure report parameters')
            ]

            for perm_name, perm_desc in permissions_to_add:
                if perm_name not in existing:
                    conn.execute(
                        text("INSERT INTO permissions (name, description) VALUES (:name, :description)"),
                        {"name": perm_name, "description": perm_desc}
                    )
                    logger.info(f"✓ Added permission: {perm_name}")
                else:
                    logger.info(f"⊘ Permission already exists: {perm_name}")

            # Get admin role ID
            admin_role = conn.execute(text("SELECT id FROM roles WHERE name = 'admin'")).fetchone()
            if admin_role:
                admin_role_id = admin_role[0]

                # Get permission IDs
                result = conn.execute(text("SELECT id, name FROM permissions WHERE name LIKE 'reports:%'"))
                permission_ids = {row[1]: row[0] for row in result}

                # Add permissions to admin role
                logger.info("Adding reports permissions to admin role...")
                for perm_name in permission_ids:
                    # Check if already assigned
                    exists = conn.execute(
                        text("SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :perm_id"),
                        {"role_id": admin_role_id, "perm_id": permission_ids[perm_name]}
                    ).fetchone()

                    if not exists:
                        conn.execute(
                            text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :perm_id)"),
                            {"role_id": admin_role_id, "perm_id": permission_ids[perm_name]}
                        )
                        logger.info(f"✓ Assigned {perm_name} to admin role")
                    else:
                        logger.info(f"⊘ {perm_name} already assigned to admin role")

            conn.commit()
            logger.info("✅ Reports permissions added successfully!")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Failed to add permissions: {e}")
            raise

if __name__ == "__main__":
    add_reports_permissions()
