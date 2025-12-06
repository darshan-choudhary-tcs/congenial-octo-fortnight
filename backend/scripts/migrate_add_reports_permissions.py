"""
Migration script to add reports permissions to database
"""
from sqlalchemy import create_engine, text
from loguru import logger
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings

def migrate():
    """Add reports permissions to permissions table"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        try:
            logger.info("Adding reports permissions...")

            # Check if permissions exist
            result = conn.execute(text("SELECT name FROM permissions WHERE name LIKE 'reports:%'"))
            existing_perms = [row[0] for row in result]

            # Permissions to add
            new_permissions = [
                {
                    "name": "reports:generate",
                    "description": "Generate energy reports",
                    "resource": "reports",
                    "action": "generate"
                },
                {
                    "name": "reports:view",
                    "description": "View reports",
                    "resource": "reports",
                    "action": "view"
                },
                {
                    "name": "reports:configure",
                    "description": "Configure report settings",
                    "resource": "reports",
                    "action": "configure"
                }
            ]

            # Add new permissions
            for perm in new_permissions:
                if perm["name"] not in existing_perms:
                    conn.execute(
                        text("""
                            INSERT INTO permissions (name, description, resource, action)
                            VALUES (:name, :description, :resource, :action)
                        """),
                        perm
                    )
                    logger.info(f"✓ Added permission: {perm['name']}")
                else:
                    logger.info(f"⊘ Permission already exists: {perm['name']}")

            # Get permission IDs
            result = conn.execute(text("SELECT id, name FROM permissions WHERE name LIKE 'reports:%'"))
            perm_ids = {row[1]: row[0] for row in result}

            # Get role IDs
            result = conn.execute(text("SELECT id, name FROM roles WHERE name IN ('admin', 'authenticated_user')"))
            role_ids = {row[1]: row[0] for row in result}

            # Add permissions to roles
            logger.info("Adding reports permissions to roles...")

            for role_name in ['admin', 'authenticated_user']:
                if role_name not in role_ids:
                    logger.warning(f"Role {role_name} not found, skipping...")
                    continue

                role_id = role_ids[role_name]

                for perm_name, perm_id in perm_ids.items():
                    # Check if already assigned
                    result = conn.execute(
                        text("SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :perm_id"),
                        {"role_id": role_id, "perm_id": perm_id}
                    )

                    if not result.fetchone():
                        conn.execute(
                            text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :perm_id)"),
                            {"role_id": role_id, "perm_id": perm_id}
                        )
                        logger.info(f"✓ Added {perm_name} to {role_name}")
                    else:
                        logger.info(f"⊘ {perm_name} already assigned to {role_name}")

            conn.commit()
            logger.info("✅ Migration completed successfully!")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    migrate()
