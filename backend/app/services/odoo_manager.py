"""
Odoo Instance Management Service
Handles Docker container creation and management for Odoo instances
"""
import docker
import asyncio
import logging
import os
import json
import time
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, Dict, Any, List
import secrets
import string

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.tenant import Tenant
from app.models.odoo_instance import OdooInstance, InstanceStatus

logger = logging.getLogger(__name__)

# Docker client - initialize conditionally
docker_client = None
try:
    docker_client = docker.from_env()
    logger.info("Docker client initialized successfully")
except Exception as e:
    logger.warning(f"Docker client initialization failed: {e}")
    logger.warning("Odoo instance management will be limited without Docker")

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
            return 8070  # Start from 8070 (8069 is default Odoo port)

class OdooInstanceManager:
    """Manager for Odoo instance operations"""
    
    def __init__(self):
        self.docker_client = docker_client
    
    async def create_instance(
        self, 
        tenant_id: int, 
        instance_name: str,
        odoo_version: str = "17.0",
        admin_password: Optional[str] = None,
        database_name: Optional[str] = None,
        modules: Optional[List[str]] = None
    ) -> Optional[OdooInstance]:
        """Create a new Odoo instance"""
        if not self.docker_client:
            logger.error("Docker client not available")
            return None
        
        async with AsyncSessionLocal() as db:
            try:
                # Get tenant
                tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
                tenant = tenant_result.scalar_one_or_none()
                
                if not tenant:
                    logger.error(f"Tenant {tenant_id} not found")
                    return None
                
                # Generate instance details
                container_name = f"odoo-{tenant_id}-{instance_name.lower().replace(' ', '-')}"
                port = await get_next_available_port()
                admin_pwd = admin_password or generate_password()
                db_name = database_name or f"odoo_{tenant_id}_{int(time.time())}"
                
                # Create instance record
                instance = OdooInstance(
                    tenant_id=tenant_id,
                    container_name=container_name,
                    odoo_version=odoo_version,
                    port=port,
                    database_name=db_name,
                    admin_password=admin_pwd,
                    status=InstanceStatus.CREATING
                )
                
                db.add(instance)
                await db.commit()
                await db.refresh(instance)
                
                # Create Docker container
                container_id = await self._create_docker_container(
                    instance_id=instance.id,
                    container_name=container_name,
                    odoo_version=odoo_version,
                    port=port,
                    database_name=db_name,
                    admin_password=admin_pwd,
                    modules=modules or []
                )
                
                if container_id:
                    # Update instance with container ID
                    await db.execute(
                        update(OdooInstance)
                        .where(OdooInstance.id == instance.id)
                        .values(
                            container_id=container_id,
                            status=InstanceStatus.RUNNING,
                            started_at=datetime.utcnow()
                        )
                    )
                    await db.commit()
                    
                    logger.info(f"Odoo instance created successfully: {container_name}")
                    return instance
                else:
                    # Failed to create container, update status
                    await db.execute(
                        update(OdooInstance)
                        .where(OdooInstance.id == instance.id)
                        .values(status=InstanceStatus.ERROR)
                    )
                    await db.commit()
                    
                    logger.error(f"Failed to create Docker container for instance {instance.id}")
                    return None
                
            except Exception as e:
                logger.error(f"Error creating Odoo instance: {e}")
                await db.rollback()
                return None
    
    async def _create_docker_container(
        self,
        instance_id: int,
        container_name: str,
        odoo_version: str,
        port: int,
        database_name: str,
        admin_password: str,
        modules: List[str]
    ) -> Optional[str]:
        """Create Docker container for Odoo instance"""
        try:
            # Environment variables for Odoo
            environment = {
                'POSTGRES_DB': database_name,
                'POSTGRES_USER': 'odoo',
                'POSTGRES_PASSWORD': generate_password(),
                'POSTGRES_HOST': 'postgres',
                'POSTGRES_PORT': '5432',
                'ODOO_ADMIN_PASSWD': admin_password,
                'ODOO_DB_NAME': database_name,
                'ODOO_DB_USER': 'odoo',
                'ODOO_DB_PASSWORD': generate_password(),
            }
            
            # Volume mounts
            volumes = {
                f"odoo-{instance_id}-data": {'bind': '/var/lib/odoo', 'mode': 'rw'},
                f"odoo-{instance_id}-addons": {'bind': '/mnt/extra-addons', 'mode': 'rw'},
                f"odoo-{instance_id}-config": {'bind': '/etc/odoo', 'mode': 'rw'},
            }
            
            # Port mapping
            ports = {
                '8069/tcp': port,
                '8072/tcp': port + 1000  # For longpolling
            }
            
            # Create and start container
            container = self.docker_client.containers.run(
                image=f"odoo:{odoo_version}",
                name=container_name,
                environment=environment,
                volumes=volumes,
                ports=ports,
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                labels={
                    "odoo.instance.id": str(instance_id),
                    "odoo.tenant.id": str(instance_id),
                    "odoo.version": odoo_version,
                    "managed.by": "odoo-saas-platform"
                }
            )
            
            logger.info(f"Docker container created: {container.id}")
            return container.id
            
        except Exception as e:
            logger.error(f"Error creating Docker container: {e}")
            return None
    
    async def start_instance(self, instance_id: int) -> bool:
        """Start Odoo instance"""
        if not self.docker_client:
            return False
        
        async with AsyncSessionLocal() as db:
            try:
                # Get instance
                result = await db.execute(select(OdooInstance).where(OdooInstance.id == instance_id))
                instance = result.scalar_one_or_none()
                
                if not instance or not instance.container_id:
                    return False
                
                # Start container
                container = self.docker_client.containers.get(instance.container_id)
                container.start()
                
                # Update instance status
                await db.execute(
                    update(OdooInstance)
                    .where(OdooInstance.id == instance_id)
                    .values(
                        status=InstanceStatus.RUNNING,
                        started_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                logger.info(f"Instance {instance_id} started successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error starting instance {instance_id}: {e}")
                return False
    
    async def stop_instance(self, instance_id: int) -> bool:
        """Stop Odoo instance"""
        if not self.docker_client:
            return False
        
        async with AsyncSessionLocal() as db:
            try:
                # Get instance
                result = await db.execute(select(OdooInstance).where(OdooInstance.id == instance_id))
                instance = result.scalar_one_or_none()
                
                if not instance or not instance.container_id:
                    return False
                
                # Stop container
                container = self.docker_client.containers.get(instance.container_id)
                container.stop()
                
                # Update instance status
                await db.execute(
                    update(OdooInstance)
                    .where(OdooInstance.id == instance_id)
                    .values(
                        status=InstanceStatus.STOPPED,
                        stopped_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                logger.info(f"Instance {instance_id} stopped successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error stopping instance {instance_id}: {e}")
                return False
    
    async def restart_instance(self, instance_id: int) -> bool:
        """Restart Odoo instance"""
        if not self.docker_client:
            return False
        
        async with AsyncSessionLocal() as db:
            try:
                # Get instance
                result = await db.execute(select(OdooInstance).where(OdooInstance.id == instance_id))
                instance = result.scalar_one_or_none()
                
                if not instance or not instance.container_id:
                    return False
                
                # Restart container
                container = self.docker_client.containers.get(instance.container_id)
                container.restart()
                
                # Update instance status
                await db.execute(
                    update(OdooInstance)
                    .where(OdooInstance.id == instance_id)
                    .values(
                        status=InstanceStatus.RUNNING,
                        started_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                logger.info(f"Instance {instance_id} restarted successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error restarting instance {instance_id}: {e}")
                return False
    
    async def delete_instance(self, instance_id: int) -> bool:
        """Delete Odoo instance and its container"""
        if not self.docker_client:
            return False
        
        async with AsyncSessionLocal() as db:
            try:
                # Get instance
                result = await db.execute(select(OdooInstance).where(OdooInstance.id == instance_id))
                instance = result.scalar_one_or_none()
                
                if not instance:
                    return False
                
                # Stop and remove container if exists
                if instance.container_id:
                    try:
                        container = self.docker_client.containers.get(instance.container_id)
                        container.stop()
                        container.remove()
                        
                        # Remove volumes
                        try:
                            volume_names = [
                                f"odoo-{instance_id}-data",
                                f"odoo-{instance_id}-addons",
                                f"odoo-{instance_id}-config"
                            ]
                            for volume_name in volume_names:
                                try:
                                    volume = self.docker_client.volumes.get(volume_name)
                                    volume.remove()
                                except:
                                    pass
                        except Exception as e:
                            logger.warning(f"Error removing volumes for instance {instance_id}: {e}")
                        
                    except Exception as e:
                        logger.warning(f"Error removing container for instance {instance_id}: {e}")
                
                # Delete instance record
                await db.delete(instance)
                await db.commit()
                
                logger.info(f"Instance {instance_id} deleted successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error deleting instance {instance_id}: {e}")
                return False
    
    async def get_instance_stats(self, instance_id: int) -> Optional[Dict[str, Any]]:
        """Get instance statistics"""
        if not self.docker_client:
            return None
        
        async with AsyncSessionLocal() as db:
            try:
                # Get instance
                result = await db.execute(select(OdooInstance).where(OdooInstance.id == instance_id))
                instance = result.scalar_one_or_none()
                
                if not instance or not instance.container_id:
                    return None
                
                # Get container stats
                container = self.docker_client.containers.get(instance.container_id)
                stats = container.stats(stream=False)
                
                # Calculate CPU usage
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                cpu_usage = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
                
                # Calculate memory usage
                memory_usage = stats['memory_stats']['usage']
                memory_limit = stats['memory_stats']['limit']
                memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0.0
                
                # Network stats
                network_rx = sum(net['rx_bytes'] for net in stats['networks'].values())
                network_tx = sum(net['tx_bytes'] for net in stats['networks'].values())
                
                return {
                    'cpu_usage': round(cpu_usage, 2),
                    'memory_usage': round(memory_percent, 2),
                    'memory_bytes': memory_usage,
                    'network_rx': network_rx,
                    'network_tx': network_tx,
                    'status': container.status,
                    'uptime': (datetime.utcnow() - instance.started_at).total_seconds() if instance.started_at else 0
                }
                
            except Exception as e:
                logger.error(f"Error getting stats for instance {instance_id}: {e}")
                return None
    
    async def backup_instance(self, instance_id: int) -> Optional[str]:
        """Create backup of Odoo instance"""
        # TODO: Implement backup functionality
        # This would involve:
        # 1. Creating database dump
        # 2. Backing up filestore
        # 3. Storing backup in S3 or local storage
        # 4. Updating backup timestamp in database
        
        async with AsyncSessionLocal() as db:
            try:
                await db.execute(
                    update(OdooInstance)
                    .where(OdooInstance.id == instance_id)
                    .values(last_backup_at=datetime.utcnow())
                )
                await db.commit()
                
                logger.info(f"Backup created for instance {instance_id}")
                return f"backup-{instance_id}-{int(time.time())}.tar.gz"
                
            except Exception as e:
                logger.error(f"Error creating backup for instance {instance_id}: {e}")
                return None
    
    async def restore_instance(self, instance_id: int, backup_file: str) -> bool:
        """Restore Odoo instance from backup"""
        # TODO: Implement restore functionality
        logger.info(f"Restore initiated for instance {instance_id} from {backup_file}")
        return True
    
    async def update_instance_status(self, instance_id: int) -> bool:
        """Update instance status based on container state"""
        if not self.docker_client:
            return False
        
        async with AsyncSessionLocal() as db:
            try:
                # Get instance
                result = await db.execute(select(OdooInstance).where(OdooInstance.id == instance_id))
                instance = result.scalar_one_or_none()
                
                if not instance or not instance.container_id:
                    return False
                
                # Get container status
                container = self.docker_client.containers.get(instance.container_id)
                container_status = container.status
                
                # Map container status to instance status
                status_mapping = {
                    'running': InstanceStatus.RUNNING,
                    'exited': InstanceStatus.STOPPED,
                    'paused': InstanceStatus.STOPPED,
                    'restarting': InstanceStatus.UPDATING,
                    'dead': InstanceStatus.ERROR,
                    'created': InstanceStatus.CREATING
                }
                
                new_status = status_mapping.get(container_status, InstanceStatus.ERROR)
                
                # Update instance status if changed
                if instance.status != new_status:
                    await db.execute(
                        update(OdooInstance)
                        .where(OdooInstance.id == instance_id)
                        .values(status=new_status)
                    )
                    await db.commit()
                    
                    logger.info(f"Instance {instance_id} status updated to {new_status}")
                
                return True
                
            except Exception as e:
                logger.error(f"Error updating status for instance {instance_id}: {e}")
                return False

# Global instance manager
instance_manager = OdooInstanceManager()

# Background task functions
async def create_odoo_instance(tenant_id: int, instance_name: str = "default", **kwargs):
    """Background task to create Odoo instance"""
    await instance_manager.create_instance(tenant_id, instance_name, **kwargs)

async def start_instance(instance_id: int):
    """Background task to start instance"""
    await instance_manager.start_instance(instance_id)

async def stop_instance(instance_id: int):
    """Background task to stop instance"""
    await instance_manager.stop_instance(instance_id)

async def restart_instance(instance_id: int):
    """Background task to restart instance"""
    await instance_manager.restart_instance(instance_id)

