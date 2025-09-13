"""
User management service
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.user import User
from app.models.tenant import Tenant
from app.core.security import get_password_hash, verify_password
from app.schemas.auth import UserCreate, UserResponse
from app.schemas.admin import UserManagementResponse, UserUpdateRequest

class UserService:
    """Service for user management operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        result = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")
        
        # Create new user
        user = User(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            company=user_data.company,
            phone=user_data.phone
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def update_user(self, user_id: int, update_data: dict) -> Optional[User]:
        """Update user information"""
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            return await self.get_user_by_id(user_id)
        
        # Hash password if provided
        if 'password' in update_data:
            update_data['hashed_password'] = get_password_hash(update_data.pop('password'))
        
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        
        return await self.get_user_by_id(user_id)
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        result = await self.db.execute(
            delete(User).where(User.id == user_id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await self.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()
        
        return user
    
    async def get_users_list(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None
    ) -> List[UserManagementResponse]:
        """Get paginated list of users for admin management"""
        query = select(
            User,
            func.count(Tenant.id).label('tenant_count')
        ).outerjoin(Tenant).group_by(User.id)
        
        # Apply filters
        if search:
            query = query.where(
                User.email.ilike(f"%{search}%") |
                User.full_name.ilike(f"%{search}%") |
                User.company.ilike(f"%{search}%")
            )
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        if is_admin is not None:
            query = query.where(User.is_admin == is_admin)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        users_data = result.all()
        
        # Convert to response format
        users_list = []
        for user, tenant_count in users_data:
            # Get instance count for this user
            instance_count_query = select(func.count()).select_from(
                select(Tenant.id).where(Tenant.owner_id == user.id).subquery()
            )
            instance_result = await self.db.execute(instance_count_query)
            instance_count = instance_result.scalar() or 0
            
            users_list.append(UserManagementResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                company=user.company,
                is_active=user.is_active,
                is_verified=user.is_verified,
                is_admin=user.is_admin,
                tenant_count=tenant_count or 0,
                instance_count=instance_count,
                last_login=user.last_login,
                created_at=user.created_at
            ))
        
        return users_list
    
    async def update_user_admin(self, user_id: int, update_data: UserUpdateRequest) -> Optional[User]:
        """Update user by admin"""
        update_dict = update_data.dict(exclude_unset=True)
        return await self.update_user(user_id, update_dict)
    
    async def verify_user_email(self, user_id: int) -> bool:
        """Mark user email as verified"""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_verified=True, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        return True
    
    async def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password"""
        user = await self.get_user_by_id(user_id)
        if not user or not verify_password(current_password, user.hashed_password):
            return False
        
        await self.update_user(user_id, {'password': new_password})
        return True
    
    async def reset_password(self, email: str, new_password: str) -> bool:
        """Reset user password (admin function)"""
        user = await self.get_user_by_email(email)
        if not user:
            return False
        
        await self.update_user(user.id, {'password': new_password})
        return True

