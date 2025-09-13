"""
Backup service for automated database and file backups
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import subprocess
import os
import shutil
import tarfile
import gzip
import json
import logging
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

from app.models.tenant import Tenant
from app.models.odoo_instance import OdooInstance
from app.models.backup import BackupRecord
from app.core.config import settings

logger = logging.getLogger(__name__)

class BackupService:
    """Service for managing backups and disaster recovery"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.backup_base_path = Path(settings.BACKUP_PATH or "/app/backups")
        self.backup_base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize S3 client if configured
        self.s3_client = None
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION or 'us-east-1'
            )
    
    async def create_database_backup(self, tenant_id: Optional[int] = None) -> Dict[str, Any]:
        """Create database backup for specific tenant or entire platform"""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            if tenant_id:
                # Backup specific tenant's database
                backup_name = f"tenant_{tenant_id}_db_{timestamp}"
                backup_path = self.backup_base_path / f"{backup_name}.sql.gz"
                
                # Get tenant's database connection info
                tenant_result = await self.db.execute(
                    select(Tenant).where(Tenant.id == tenant_id)
                )
                tenant = tenant_result.scalar_one_or_none()
                
                if not tenant:
                    raise ValueError(f"Tenant {tenant_id} not found")
                
                # Create tenant-specific database dump
                await self._dump_tenant_database(tenant, backup_path)
                
            else:
                # Backup entire platform database
                backup_name = f"platform_db_{timestamp}"
                backup_path = self.backup_base_path / f"{backup_name}.sql.gz"
                
                # Create full database dump
                await self._dump_platform_database(backup_path)
            
            # Get backup file size
            backup_size = backup_path.stat().st_size
            
            # Upload to S3 if configured
            s3_url = None
            if self.s3_client and settings.S3_BACKUP_BUCKET:
                s3_url = await self._upload_to_s3(backup_path, settings.S3_BACKUP_BUCKET)
            
            # Create backup record
            backup_record = BackupRecord(
                tenant_id=tenant_id,
                backup_type="database",
                backup_name=backup_name,
                file_path=str(backup_path),
                file_size=backup_size,
                s3_url=s3_url,
                status="completed",
                created_at=datetime.utcnow()
            )
            
            self.db.add(backup_record)
            await self.db.commit()
            await self.db.refresh(backup_record)
            
            return {
                "backup_id": backup_record.id,
                "backup_name": backup_name,
                "file_path": str(backup_path),
                "file_size": backup_size,
                "s3_url": s3_url,
                "created_at": backup_record.created_at
            }
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            
            # Create failed backup record
            backup_record = BackupRecord(
                tenant_id=tenant_id,
                backup_type="database",
                backup_name=f"failed_{timestamp}",
                status="failed",
                error_message=str(e),
                created_at=datetime.utcnow()
            )
            
            self.db.add(backup_record)
            await self.db.commit()
            
            raise Exception(f"Database backup failed: {e}")
    
    async def _dump_tenant_database(self, tenant: Tenant, backup_path: Path):
        """Create database dump for specific tenant"""
        # This would connect to the tenant's specific database
        # For now, we'll create a filtered dump of the main database
        
        cmd = [
            "pg_dump",
            f"--host={settings.DATABASE_HOST}",
            f"--port={settings.DATABASE_PORT}",
            f"--username={settings.DATABASE_USER}",
            f"--dbname={settings.DATABASE_NAME}",
            "--no-password",
            "--verbose",
            "--clean",
            "--no-acl",
            "--no-owner",
            f"--where=tenant_id={tenant.id}",  # Filter by tenant
        ]
        
        # Set password via environment
        env = os.environ.copy()
        env["PGPASSWORD"] = settings.DATABASE_PASSWORD
        
        # Run pg_dump and compress
        with gzip.open(backup_path, 'wt') as f:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"pg_dump failed: {stderr.decode()}")
            
            f.write(stdout.decode())
    
    async def _dump_platform_database(self, backup_path: Path):
        """Create full platform database dump"""
        cmd = [
            "pg_dump",
            f"--host={settings.DATABASE_HOST}",
            f"--port={settings.DATABASE_PORT}",
            f"--username={settings.DATABASE_USER}",
            f"--dbname={settings.DATABASE_NAME}",
            "--no-password",
            "--verbose",
            "--clean",
            "--no-acl",
            "--no-owner",
        ]
        
        # Set password via environment
        env = os.environ.copy()
        env["PGPASSWORD"] = settings.DATABASE_PASSWORD
        
        # Run pg_dump and compress
        with gzip.open(backup_path, 'wt') as f:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"pg_dump failed: {stderr.decode()}")
            
            f.write(stdout.decode())
    
    async def create_file_backup(self, tenant_id: Optional[int] = None) -> Dict[str, Any]:
        """Create file backup for tenant data or entire platform"""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            if tenant_id:
                # Backup specific tenant's files
                backup_name = f"tenant_{tenant_id}_files_{timestamp}"
                backup_path = self.backup_base_path / f"{backup_name}.tar.gz"
                
                # Get tenant's file paths
                tenant_result = await self.db.execute(
                    select(Tenant).where(Tenant.id == tenant_id)
                )
                tenant = tenant_result.scalar_one_or_none()
                
                if not tenant:
                    raise ValueError(f"Tenant {tenant_id} not found")
                
                # Create tenant file backup
                await self._create_tenant_file_backup(tenant, backup_path)
                
            else:
                # Backup entire platform files
                backup_name = f"platform_files_{timestamp}"
                backup_path = self.backup_base_path / f"{backup_name}.tar.gz"
                
                # Create full file backup
                await self._create_platform_file_backup(backup_path)
            
            # Get backup file size
            backup_size = backup_path.stat().st_size
            
            # Upload to S3 if configured
            s3_url = None
            if self.s3_client and settings.S3_BACKUP_BUCKET:
                s3_url = await self._upload_to_s3(backup_path, settings.S3_BACKUP_BUCKET)
            
            # Create backup record
            backup_record = BackupRecord(
                tenant_id=tenant_id,
                backup_type="files",
                backup_name=backup_name,
                file_path=str(backup_path),
                file_size=backup_size,
                s3_url=s3_url,
                status="completed",
                created_at=datetime.utcnow()
            )
            
            self.db.add(backup_record)
            await self.db.commit()
            await self.db.refresh(backup_record)
            
            return {
                "backup_id": backup_record.id,
                "backup_name": backup_name,
                "file_path": str(backup_path),
                "file_size": backup_size,
                "s3_url": s3_url,
                "created_at": backup_record.created_at
            }
            
        except Exception as e:
            logger.error(f"File backup failed: {e}")
            
            # Create failed backup record
            backup_record = BackupRecord(
                tenant_id=tenant_id,
                backup_type="files",
                backup_name=f"failed_{timestamp}",
                status="failed",
                error_message=str(e),
                created_at=datetime.utcnow()
            )
            
            self.db.add(backup_record)
            await self.db.commit()
            
            raise Exception(f"File backup failed: {e}")
    
    async def _create_tenant_file_backup(self, tenant: Tenant, backup_path: Path):
        """Create file backup for specific tenant"""
        # Define tenant-specific file paths
        tenant_paths = [
            f"/app/data/tenants/{tenant.id}",
            f"/app/uploads/tenants/{tenant.id}",
            f"/app/logs/tenants/{tenant.id}"
        ]
        
        # Create tar.gz archive
        with tarfile.open(backup_path, 'w:gz') as tar:
            for path in tenant_paths:
                if os.path.exists(path):
                    tar.add(path, arcname=f"tenant_{tenant.id}/{os.path.basename(path)}")
    
    async def _create_platform_file_backup(self, backup_path: Path):
        """Create file backup for entire platform"""
        # Define platform file paths
        platform_paths = [
            "/app/data",
            "/app/uploads",
            "/app/logs",
            "/app/config"
        ]
        
        # Create tar.gz archive
        with tarfile.open(backup_path, 'w:gz') as tar:
            for path in platform_paths:
                if os.path.exists(path):
                    tar.add(path, arcname=os.path.basename(path))
    
    async def _upload_to_s3(self, file_path: Path, bucket_name: str) -> Optional[str]:
        """Upload backup file to S3"""
        if not self.s3_client:
            return None
        
        try:
            s3_key = f"backups/{file_path.name}"
            
            # Upload file
            self.s3_client.upload_file(
                str(file_path),
                bucket_name,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'  # Infrequent Access for cost optimization
                }
            )
            
            # Generate S3 URL
            s3_url = f"s3://{bucket_name}/{s3_key}"
            return s3_url
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return None
    
    async def restore_database_backup(self, backup_id: int) -> Dict[str, Any]:
        """Restore database from backup"""
        try:
            # Get backup record
            backup_result = await self.db.execute(
                select(BackupRecord).where(BackupRecord.id == backup_id)
            )
            backup = backup_result.scalar_one_or_none()
            
            if not backup:
                raise ValueError(f"Backup {backup_id} not found")
            
            if backup.backup_type != "database":
                raise ValueError("Invalid backup type for database restore")
            
            # Download from S3 if needed
            restore_path = Path(backup.file_path)
            if backup.s3_url and not restore_path.exists():
                restore_path = await self._download_from_s3(backup.s3_url)
            
            if not restore_path.exists():
                raise ValueError("Backup file not found")
            
            # Restore database
            await self._restore_database_from_file(restore_path, backup.tenant_id)
            
            return {
                "backup_id": backup_id,
                "restored_at": datetime.utcnow(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            raise Exception(f"Database restore failed: {e}")
    
    async def _restore_database_from_file(self, backup_path: Path, tenant_id: Optional[int] = None):
        """Restore database from backup file"""
        if tenant_id:
            # Restore specific tenant data
            # This would involve careful restoration to avoid conflicts
            cmd = [
                "psql",
                f"--host={settings.DATABASE_HOST}",
                f"--port={settings.DATABASE_PORT}",
                f"--username={settings.DATABASE_USER}",
                f"--dbname={settings.DATABASE_NAME}",
                "--no-password",
            ]
        else:
            # Full database restore (dangerous - should be done carefully)
            cmd = [
                "psql",
                f"--host={settings.DATABASE_HOST}",
                f"--port={settings.DATABASE_PORT}",
                f"--username={settings.DATABASE_USER}",
                f"--dbname={settings.DATABASE_NAME}",
                "--no-password",
            ]
        
        # Set password via environment
        env = os.environ.copy()
        env["PGPASSWORD"] = settings.DATABASE_PASSWORD
        
        # Restore from compressed backup
        with gzip.open(backup_path, 'rt') as f:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = await process.communicate(input=f.read().encode())
            
            if process.returncode != 0:
                raise Exception(f"Database restore failed: {stderr.decode()}")
    
    async def _download_from_s3(self, s3_url: str) -> Path:
        """Download backup file from S3"""
        if not self.s3_client:
            raise Exception("S3 client not configured")
        
        # Parse S3 URL
        s3_parts = s3_url.replace("s3://", "").split("/", 1)
        bucket_name = s3_parts[0]
        s3_key = s3_parts[1]
        
        # Download to temporary location
        download_path = self.backup_base_path / f"temp_{s3_key.split('/')[-1]}"
        
        try:
            self.s3_client.download_file(bucket_name, s3_key, str(download_path))
            return download_path
        except ClientError as e:
            raise Exception(f"S3 download failed: {e}")
    
    async def cleanup_old_backups(self, retention_days: int = 30) -> Dict[str, Any]:
        """Clean up old backup files"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Get old backup records
        old_backups_result = await self.db.execute(
            select(BackupRecord).where(BackupRecord.created_at < cutoff_date)
        )
        old_backups = old_backups_result.scalars().all()
        
        deleted_count = 0
        freed_space = 0
        
        for backup in old_backups:
            try:
                # Delete local file if exists
                if backup.file_path and os.path.exists(backup.file_path):
                    file_size = os.path.getsize(backup.file_path)
                    os.remove(backup.file_path)
                    freed_space += file_size
                
                # Delete from S3 if exists
                if backup.s3_url and self.s3_client:
                    s3_parts = backup.s3_url.replace("s3://", "").split("/", 1)
                    bucket_name = s3_parts[0]
                    s3_key = s3_parts[1]
                    
                    try:
                        self.s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
                    except ClientError:
                        pass  # Continue even if S3 deletion fails
                
                # Delete backup record
                await self.db.delete(backup)
                deleted_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to delete backup {backup.id}: {e}")
        
        await self.db.commit()
        
        return {
            "deleted_backups": deleted_count,
            "freed_space_bytes": freed_space,
            "retention_days": retention_days
        }
    
    async def get_backup_status(self) -> Dict[str, Any]:
        """Get backup system status and statistics"""
        # Get backup counts by type and status
        backup_stats_result = await self.db.execute(
            select(
                BackupRecord.backup_type,
                BackupRecord.status,
                func.count(BackupRecord.id).label('count'),
                func.sum(BackupRecord.file_size).label('total_size')
            ).group_by(BackupRecord.backup_type, BackupRecord.status)
        )
        backup_stats = backup_stats_result.all()
        
        # Get recent backups
        recent_backups_result = await self.db.execute(
            select(BackupRecord).order_by(BackupRecord.created_at.desc()).limit(10)
        )
        recent_backups = recent_backups_result.scalars().all()
        
        # Calculate total storage used
        total_size_result = await self.db.execute(
            select(func.sum(BackupRecord.file_size)).where(BackupRecord.status == "completed")
        )
        total_storage = total_size_result.scalar() or 0
        
        # Get oldest and newest backups
        oldest_backup_result = await self.db.execute(
            select(BackupRecord).order_by(BackupRecord.created_at.asc()).limit(1)
        )
        oldest_backup = oldest_backup_result.scalar_one_or_none()
        
        return {
            "total_backups": sum(stat.count for stat in backup_stats),
            "total_storage_bytes": total_storage,
            "backup_statistics": [
                {
                    "type": stat.backup_type,
                    "status": stat.status,
                    "count": stat.count,
                    "total_size": stat.total_size or 0
                }
                for stat in backup_stats
            ],
            "recent_backups": [
                {
                    "id": backup.id,
                    "tenant_id": backup.tenant_id,
                    "type": backup.backup_type,
                    "name": backup.backup_name,
                    "status": backup.status,
                    "size": backup.file_size,
                    "created_at": backup.created_at
                }
                for backup in recent_backups
            ],
            "oldest_backup": oldest_backup.created_at if oldest_backup else None,
            "s3_configured": self.s3_client is not None
        }
    
    async def schedule_automated_backup(self, backup_type: str = "both", schedule: str = "daily") -> Dict[str, Any]:
        """Schedule automated backups"""
        # This would integrate with a task scheduler like Celery
        # For now, return configuration
        
        return {
            "backup_type": backup_type,
            "schedule": schedule,
            "next_run": datetime.utcnow() + timedelta(days=1),
            "status": "scheduled"
        }

