"""
Monitoring API endpoints for system health and performance
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.services.monitoring import MonitoringService

router = APIRouter()

@router.get("/health")
async def get_system_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get overall system health status"""
    monitoring_service = MonitoringService(db)
    return await monitoring_service.get_system_health()

@router.get("/health/public")
async def get_public_health() -> Dict[str, str]:
    """Public health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "odoo-saas-platform"
    }

@router.get("/metrics/prometheus")
async def get_prometheus_metrics(
    db: AsyncSession = Depends(get_db)
) -> Response:
    """Get Prometheus metrics in text format"""
    monitoring_service = MonitoringService(db)
    metrics_text = monitoring_service.get_prometheus_metrics()
    
    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )

@router.get("/instances/{instance_id}/metrics")
async def get_instance_metrics(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed metrics for a specific Odoo instance"""
    monitoring_service = MonitoringService(db)
    
    # Check if user has access to this instance
    if not current_user.is_admin:
        # Add tenant ownership check here
        pass
    
    return await monitoring_service.get_instance_metrics(instance_id)

@router.get("/tenants/{tenant_id}/metrics")
async def get_tenant_metrics(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive metrics for a tenant"""
    monitoring_service = MonitoringService(db)
    
    # Check if user has access to this tenant
    if not current_user.is_admin:
        # Add tenant ownership check here
        pass
    
    return await monitoring_service.get_tenant_metrics(tenant_id)

@router.get("/performance")
async def get_performance_metrics(
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get performance metrics over time"""
    if hours > 168:  # Limit to 1 week
        raise HTTPException(status_code=400, detail="Hours parameter cannot exceed 168 (1 week)")
    
    monitoring_service = MonitoringService(db)
    return await monitoring_service.get_performance_metrics(hours)

@router.get("/alerts")
async def get_system_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> List[Dict[str, Any]]:
    """Get current system alerts"""
    monitoring_service = MonitoringService(db)
    return await monitoring_service.get_alerts()

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get comprehensive dashboard statistics"""
    monitoring_service = MonitoringService(db)
    
    # Get system health
    system_health = await monitoring_service.get_system_health()
    
    # Get alerts
    alerts = await monitoring_service.get_alerts()
    
    # Get performance metrics for last 24 hours
    performance = await monitoring_service.get_performance_metrics(24)
    
    return {
        "system_health": system_health,
        "alerts": alerts,
        "performance": performance,
        "summary": {
            "health_status": system_health.get("status", "unknown"),
            "critical_alerts": len([a for a in alerts if a.get("type") == "critical"]),
            "warning_alerts": len([a for a in alerts if a.get("type") == "warning"]),
            "total_activities_24h": performance.get("total_activities", 0),
            "new_instances_24h": performance.get("total_new_instances", 0)
        }
    }

@router.post("/api-request")
async def record_api_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration: float,
    db: AsyncSession = Depends(get_db)
):
    """Record API request metrics (internal use)"""
    monitoring_service = MonitoringService(db)
    await monitoring_service.record_api_request(method, endpoint, status_code, duration)
    return {"status": "recorded"}

@router.get("/system/resources")
async def get_system_resources(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get current system resource usage"""
    import psutil
    
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get network stats
    network = psutil.net_io_counters()
    
    # Get process count
    process_count = len(psutil.pids())
    
    return {
        "timestamp": datetime.utcnow(),
        "cpu": {
            "percent": cpu_percent,
            "count": psutil.cpu_count(),
            "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
        },
        "memory": {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_gb": memory.used / (1024**3),
            "percent": memory.percent
        },
        "disk": {
            "total_gb": disk.total / (1024**3),
            "used_gb": disk.used / (1024**3),
            "free_gb": disk.free / (1024**3),
            "percent": disk.percent
        },
        "network": {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        },
        "processes": {
            "count": process_count
        }
    }

@router.get("/docker/containers")
async def get_docker_containers(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get Docker container information"""
    try:
        import docker
        client = docker.from_env()
        
        containers = client.containers.list(all=True)
        
        container_info = []
        for container in containers:
            info = {
                "id": container.id[:12],
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "created": container.attrs['Created'],
                "ports": container.ports
            }
            
            # Get stats for running containers
            if container.status == 'running':
                try:
                    stats = container.stats(stream=False)
                    
                    # Calculate CPU usage
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                               stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                  stats['precpu_stats']['system_cpu_usage']
                    cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
                    
                    # Memory usage
                    memory_usage = stats['memory_stats']['usage']
                    memory_limit = stats['memory_stats']['limit']
                    
                    info.update({
                        "cpu_percent": round(cpu_percent, 2),
                        "memory_usage_mb": round(memory_usage / (1024**2), 2),
                        "memory_limit_mb": round(memory_limit / (1024**2), 2),
                        "memory_percent": round((memory_usage / memory_limit) * 100, 2) if memory_limit > 0 else 0
                    })
                except Exception as e:
                    info["stats_error"] = str(e)
            
            container_info.append(info)
        
        # Summary stats
        total_containers = len(containers)
        running_containers = len([c for c in containers if c.status == 'running'])
        odoo_containers = len([c for c in containers if 'odoo' in c.name.lower()])
        
        return {
            "summary": {
                "total": total_containers,
                "running": running_containers,
                "stopped": total_containers - running_containers,
                "odoo_containers": odoo_containers
            },
            "containers": container_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")

@router.get("/logs/recent")
async def get_recent_logs(
    limit: int = 100,
    level: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> List[Dict[str, Any]]:
    """Get recent system logs"""
    from app.models.audit_log import AuditLog
    from sqlalchemy import select
    
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    
    if level:
        query = query.where(AuditLog.level == level)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "tenant_id": log.tenant_id,
            "action": log.action,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at
        }
        for log in logs
    ]

