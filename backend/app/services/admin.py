"""
Admin service for system administration
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

async def create_admin_user():
    """Create default admin user if not exists"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if admin user exists
            result = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                # Create admin user
                admin_user = User(
                    email=settings.ADMIN_EMAIL,
                    hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                    full_name="System Administrator",
                    is_active=True,
                    is_admin=True,
                    is_verified=True
                )
                
                db.add(admin_user)
                await db.commit()
                
                logger.info(f"Admin user created: {settings.ADMIN_EMAIL}")
            else:
                logger.info("Admin user already exists")
                
        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
            await db.rollback()
            raise

