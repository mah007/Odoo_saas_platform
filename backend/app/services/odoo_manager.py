"""
Odoo Instance Management Service
Handles Docker container creation and management for Odoo instances
"""
import docker
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
import secrets
import string

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.tenant import Tenant
from app.models.odoo_instance import OdooInstance, InstanceStatus

logger = logging.getLogger(__name__)

# Docker client
docker_client = docker.from_env()

def generate_password(length: int = 12) -> str:
    """Generate secure random password"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def get_next_available_port() -> int:
    """Get next available port for Odoo instance"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OdooInstance.port).order_by(OdooInstance.port.desc()).limit(1)
        )
        last_port = result.scalar_one_or_none()
        
        if last_port:
            return last_port + 1
        else:
            return settings.ODOO_BASE_PORT

async def create_odoo_instance(tenant_id: int):
    """Create new Odoo instance for tenant"""
    async with AsyncSessionLocal() as db:
        try:
            # Get tenant
            result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                logger.error(f"Tenant {tenant_id} not found")
                return
            
            # Get next available port
            port = await get_next_available_port()
            
            # Generate database name and password
            db_name = f"odoo_{tenant.subdomain}"
            admin_password = generate_password()
            container_name = f"odoo_{tenant.subdomain}_{tenant_id}"
            
            # Create Odoo instance record
            instance = OdooInstance(
                tenant_id=tenant_id,
                container_name=container_name,
                port=port,
                database_name=db_name,
                admin_password=admin_password,
                status=InstanceStatus.CREATING
            )
            
            db.add(instance)
            await db.commit()
            await db.refresh(instance)
            
            # Create Docker container
            try:
                container = docker_client.containers.run(
                    settings.ODOO_DOCKER_IMAGE,
                    name=container_name,
                    ports={f'8069/tcp': port},
                    environment={
                        'HOST': 'postgres',
                        'USER': 'odoo',
                        'PASSWORD': 'odoo',
                        'DB_NAME': db_name,
                        'ADMIN_PASSWD': admin_password
                    },
                    network=settings.DOCKER_NETWORK,
                    detach=True,
                    restart_policy={"Name": "unless-stopped"}
                )
                
                # Update instance with container ID
                instance.container_id = container.id
                instance.status = InstanceStatus.RUNNING
                
                # Update tenant
                tenant.odoo_port = port
                tenant.odoo_database = db_name
                tenant.odoo_admin_password = admin_password
                tenant.status = "active"
                
                await db.commit()
                
                logger.info(f"Odoo instance created for tenant {tenant.name}: {container_name}")
                
            except Exception as e:
                logger.error(f"Failed to create Docker container: {e}")
                instance.status = InstanceStatus.ERROR
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to create Odoo instance: {e}")
            await db.rollback()

async def start_instance(instance_id: int):
    """Start Odoo instance"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(OdooInstance).where(OdooInstance.id == instance_id))
            instance = result.scalar_one_or_none()
            
            if not instance:
                logger.error(f"Instance {instance_id} not found")
                return
            
            if instance.container_id:
                container = docker_client.containers.get(instance.container_id)
                container.start()
                
                instance.status = InstanceStatus.RUNNING
                await db.commit()
                
                logger.info(f"Started instance {instance.container_name}")
                
        except Exception as e:
            logger.error(f"Failed to start instance: {e}")

async def stop_instance(instance_id: int):
    """Stop Odoo instance"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(OdooInstance).where(OdooInstance.id == instance_id))
            instance = result.scalar_one_or_none()
            
            if not instance:
                logger.error(f"Instance {instance_id} not found")
                return
            
            if instance.container_id:
                container = docker_client.containers.get(instance.container_id)
                container.stop()
                
                instance.status = InstanceStatus.STOPPED
                await db.commit()
                
                logger.info(f"Stopped instance {instance.container_name}")
                
        except Exception as e:
            logger.error(f"Failed to stop instance: {e}")

async def restart_instance(instance_id: int):
    """Restart Odoo instance"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(OdooInstance).where(OdooInstance.id == instance_id))
            instance = result.scalar_one_or_none()
            
            if not instance:
                logger.error(f"Instance {instance_id} not found")
                return
            
            if instance.container_id:
                container = docker_client.containers.get(instance.container_id)
                container.restart()
                
                instance.status = InstanceStatus.RUNNING
                await db.commit()
                
                logger.info(f"Restarted instance {instance.container_name}")
                
        except Exception as e:
            logger.error(f"Failed to restart instance: {e}")

async def delete_instance(instance_id: int):
    """Delete Odoo instance"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(OdooInstance).where(OdooInstance.id == instance_id))
            instance = result.scalar_one_or_none()
            
            if not instance:
                logger.error(f"Instance {instance_id} not found")
                return
            
            if instance.container_id:
                try:
                    container = docker_client.containers.get(instance.container_id)
                    container.stop()
                    container.remove()
                except:
                    pass  # Container might not exist
            
            # Delete instance record
            await db.delete(instance)
            await db.commit()
            
            logger.info(f"Deleted instance {instance.container_name}")
            
        except Exception as e:
            logger.error(f"Failed to delete instance: {e}")

