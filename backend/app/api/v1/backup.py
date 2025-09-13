"""
Backup API endpoints for automated backup management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.services.backup import BackupService

router = APIRouter()

class BackupRequest(BaseModel):
    tenant_id: Optional[int] = None
    backup_type: str = "both"  # "database", "files", "both"

class RestoreRequest(BaseModel):
    backup_id: int

@router.post("/create")
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Create a new backup"""
    backup_service = BackupService(db)
    
    results = {}
    
    try:
        if request.backup_type in ["database", "both"]:
            # Create database backup in background
            background_tasks.add_task(
                backup_service.create_database_backup,
                request.tenant_id
            )
            results["database_backup"] = "scheduled"
        
        if request.backup_type in ["files", "both"]:
            # Create file backup in background
            background_tasks.add_task(
                backup_service.create_file_backup,
                request.tenant_id
            )
            results["file_backup"] = "scheduled"
        
        return {
            "status": "backup_scheduled",
            "tenant_id": request.tenant_id,
            "backup_type": request.backup_type,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup creation failed: {str(e)}")

@router.post("/database")
async def create_database_backup(
    tenant_id: Optional[int] = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Create database backup"""
    backup_service = BackupService(db)
    
    try:
        if background_tasks:
            # Run in background
            background_tasks.add_task(
                backup_service.create_database_backup,
                tenant_id
            )
            return {
                "status": "scheduled",
                "message": "Database backup scheduled"
            }
        else:
            # Run synchronously
            result = await backup_service.create_database_backup(tenant_id)
            return result
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database backup failed: {str(e)}")

@router.post("/files")
async def create_file_backup(
    tenant_id: Optional[int] = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Create file backup"""
    backup_service = BackupService(db)
    
    try:
        if background_tasks:
            # Run in background
            background_tasks.add_task(
                backup_service.create_file_backup,
                tenant_id
            )
            return {
                "status": "scheduled",
                "message": "File backup scheduled"
            }
        else:
            # Run synchronously
            result = await backup_service.create_file_backup(tenant_id)
            return result
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File backup failed: {str(e)}")

@router.post("/restore")
async def restore_backup(
    request: RestoreRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Restore from backup"""
    backup_service = BackupService(db)
    
    try:
        # Run restore in background (dangerous operation)
        background_tasks.add_task(
            backup_service.restore_database_backup,
            request.backup_id
        )
        
        return {
            "status": "restore_scheduled",
            "backup_id": request.backup_id,
            "message": "Restore operation scheduled - this may take several minutes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

@router.get("/list")
async def list_backups(
    tenant_id: Optional[int] = None,
    backup_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """List backups with filtering"""
    from app.models.backup import BackupRecord
    from sqlalchemy import select, and_, func
    
    # Build query
    query = select(BackupRecord).order_by(BackupRecord.created_at.desc())
    
    # Apply filters
    filters = []
    if tenant_id:
        filters.append(BackupRecord.tenant_id == tenant_id)
    if backup_type:
        filters.append(BackupRecord.backup_type == backup_type)
    if status:
        filters.append(BackupRecord.status == status)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    backups = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(BackupRecord.id))
    if filters:
        count_query = count_query.where(and_(*filters))
    
    count_result = await db.execute(count_query)
    total_count = count_result.scalar()
    
    return {
        "backups": [
            {
                "id": backup.id,
                "tenant_id": backup.tenant_id,
                "backup_type": backup.backup_type,
                "backup_name": backup.backup_name,
                "file_path": backup.file_path,
                "file_size": backup.file_size,
                "s3_url": backup.s3_url,
                "status": backup.status,
                "error_message": backup.error_message,
                "created_at": backup.created_at
            }
            for backup in backups
        ],
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }

@router.get("/status")
async def get_backup_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get backup system status"""
    backup_service = BackupService(db)
    return await backup_service.get_backup_status()

@router.delete("/cleanup")
async def cleanup_old_backups(
    retention_days: int = 30,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Clean up old backups"""
    backup_service = BackupService(db)
    
    try:
        if background_tasks:
            # Run cleanup in background
            background_tasks.add_task(
                backup_service.cleanup_old_backups,
                retention_days
            )
            return {
                "status": "cleanup_scheduled",
                "retention_days": retention_days,
                "message": "Backup cleanup scheduled"
            }
        else:
            # Run synchronously
            result = await backup_service.cleanup_old_backups(retention_days)
            return result
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup cleanup failed: {str(e)}")

@router.get("/{backup_id}")
async def get_backup_details(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get backup details"""
    from app.models.backup import BackupRecord
    from sqlalchemy import select
    
    result = await db.execute(
        select(BackupRecord).where(BackupRecord.id == backup_id)
    )
    backup = result.scalar_one_or_none()
    
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    return {
        "id": backup.id,
        "tenant_id": backup.tenant_id,
        "backup_type": backup.backup_type,
        "backup_name": backup.backup_name,
        "file_path": backup.file_path,
        "file_size": backup.file_size,
        "s3_url": backup.s3_url,
        "status": backup.status,
        "error_message": backup.error_message,
        "created_at": backup.created_at
    }

@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """Delete a specific backup"""
    from app.models.backup import BackupRecord
    from sqlalchemy import select
    import os
    
    # Get backup record
    result = await db.execute(
        select(BackupRecord).where(BackupRecord.id == backup_id)
    )
    backup = result.scalar_one_or_none()
    
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    try:
        # Delete local file if exists
        if backup.file_path and os.path.exists(backup.file_path):
            os.remove(backup.file_path)
        
        # Delete from S3 if exists (would need S3 client)
        # This would be implemented with boto3
        
        # Delete backup record
        await db.delete(backup)
        await db.commit()
        
        return {
            "status": "deleted",
            "backup_id": str(backup_id)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup deletion failed: {str(e)}")

@router.post("/schedule")
async def schedule_automated_backup(
    backup_type: str = "both",
    schedule: str = "daily",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Schedule automated backups"""
    backup_service = BackupService(db)
    return await backup_service.schedule_automated_backup(backup_type, schedule)

@router.get("/dashboard")
async def get_backup_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get backup dashboard data"""
    backup_service = BackupService(db)
    
    # Get backup status
    status = await backup_service.get_backup_status()
    
    # Get recent backup activity
    from app.models.backup import BackupRecord
    from sqlalchemy import select
    from datetime import datetime, timedelta
    
    recent_backups_result = await db.execute(
        select(BackupRecord).where(
            BackupRecord.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(BackupRecord.created_at.desc()).limit(20)
    )
    recent_backups = recent_backups_result.scalars().all()
    
    # Calculate backup health score
    total_backups = status["total_backups"]
    failed_backups = sum(
        stat["count"] for stat in status["backup_statistics"]
        if stat["status"] == "failed"
    )
    
    health_score = 100
    if total_backups > 0:
        failure_rate = (failed_backups / total_backups) * 100
        health_score = max(0, 100 - failure_rate * 2)
    
    # Check for backup alerts
    alerts = []
    
    # Check if backups are recent
    if status["oldest_backup"]:
        days_since_last = (datetime.utcnow() - status["oldest_backup"]).days
        if days_since_last > 7:
            alerts.append({
                "type": "warning",
                "message": f"No backups created in {days_since_last} days"
            })
    
    # Check storage usage
    storage_gb = status["total_storage_bytes"] / (1024**3)
    if storage_gb > 100:  # Alert if over 100GB
        alerts.append({
            "type": "info",
            "message": f"Backup storage usage: {storage_gb:.1f} GB"
        })
    
    return {
        "health_score": health_score,
        "status": status,
        "recent_activity": [
            {
                "id": backup.id,
                "type": backup.backup_type,
                "status": backup.status,
                "size": backup.file_size,
                "created_at": backup.created_at
            }
            for backup in recent_backups
        ],
        "alerts": alerts,
        "recommendations": [
            "Schedule automated daily backups",
            "Test backup restoration regularly",
            "Monitor backup storage usage",
            "Configure S3 for offsite backups"
        ] if not status["s3_configured"] else [
            "Backup system is properly configured",
            "Test restoration procedures monthly"
        ]
    }

