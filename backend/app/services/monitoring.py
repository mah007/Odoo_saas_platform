"""
Monitoring service for system health and performance tracking
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import psutil
import docker
import asyncio
import logging
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import json
import os

from app.models.tenant import Tenant
from app.models.odoo_instance import OdooInstance
from app.models.audit_log import AuditLog
from app.models.billing import Subscription, Payment
from app.core.config import settings

# Prometheus metrics
REGISTRY = CollectorRegistry()

# System metrics
SYSTEM_CPU_USAGE = Gauge('system_cpu_usage_percent', 'System CPU usage percentage', registry=REGISTRY)
SYSTEM_MEMORY_USAGE = Gauge('system_memory_usage_percent', 'System memory usage percentage', registry=REGISTRY)
SYSTEM_DISK_USAGE = Gauge('system_disk_usage_percent', 'System disk usage percentage', registry=REGISTRY)

# Application metrics
ACTIVE_TENANTS = Gauge('active_tenants_total', 'Total number of active tenants', registry=REGISTRY)
RUNNING_INSTANCES = Gauge('running_instances_total', 'Total number of running Odoo instances', registry=REGISTRY)
API_REQUESTS = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'], registry=REGISTRY)
API_REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration', ['method', 'endpoint'], registry=REGISTRY)

# Business metrics
MONTHLY_REVENUE = Gauge('monthly_revenue_usd', 'Monthly revenue in USD', registry=REGISTRY)
ACTIVE_SUBSCRIPTIONS = Gauge('active_subscriptions_total', 'Total active subscriptions', registry=REGISTRY)

logger = logging.getLogger(__name__)

class MonitoringService:
    """Service for monitoring system health and performance"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker client not available: {e}")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Update Prometheus metrics
            SYSTEM_CPU_USAGE.set(cpu_percent)
            SYSTEM_MEMORY_USAGE.set(memory.percent)
            SYSTEM_DISK_USAGE.set(disk.percent)
            
            # Database health
            db_health = await self._check_database_health()
            
            # Docker health
            docker_health = await self._check_docker_health()
            
            # Application metrics
            app_metrics = await self._get_application_metrics()
            
            # Determine overall health status
            health_status = "healthy"
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                health_status = "critical"
            elif cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
                health_status = "warning"
            
            return {
                "status": health_status,
                "timestamp": datetime.utcnow(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3),
                    "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
                },
                "database": db_health,
                "docker": docker_health,
                "application": app_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                "status": "error",
                "timestamp": datetime.utcnow(),
                "error": str(e)
            }
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = datetime.utcnow()
            
            # Simple query to test connectivity
            result = await self.db.execute(select(func.count()).select_from(Tenant))
            tenant_count = result.scalar()
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "response_time_ms": response_time * 1000,
                "tenant_count": tenant_count
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_docker_health(self) -> Dict[str, Any]:
        """Check Docker daemon and container health"""
        if not self.docker_client:
            return {
                "status": "unavailable",
                "error": "Docker client not available"
            }
        
        try:
            # Check Docker daemon
            self.docker_client.ping()
            
            # Get container stats
            containers = self.docker_client.containers.list()
            running_containers = len([c for c in containers if c.status == 'running'])
            
            # Get Odoo containers specifically
            odoo_containers = [c for c in containers if 'odoo' in c.name.lower()]
            running_odoo = len([c for c in odoo_containers if c.status == 'running'])
            
            return {
                "status": "healthy",
                "total_containers": len(containers),
                "running_containers": running_containers,
                "odoo_containers": len(odoo_containers),
                "running_odoo_containers": running_odoo
            }
            
        except Exception as e:
            logger.error(f"Docker health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        try:
            # Active tenants
            active_tenants_result = await self.db.execute(
                select(func.count(Tenant.id)).where(Tenant.status == 'active')
            )
            active_tenants = active_tenants_result.scalar() or 0
            
            # Running instances
            running_instances_result = await self.db.execute(
                select(func.count(OdooInstance.id)).where(OdooInstance.status == 'running')
            )
            running_instances = running_instances_result.scalar() or 0
            
            # Active subscriptions
            active_subs_result = await self.db.execute(
                select(func.count(Subscription.id)).where(
                    Subscription.status.in_(['active', 'trialing'])
                )
            )
            active_subscriptions = active_subs_result.scalar() or 0
            
            # Monthly revenue
            start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_revenue_result = await self.db.execute(
                select(func.sum(Payment.amount)).where(
                    and_(
                        Payment.status == 'completed',
                        Payment.created_at >= start_of_month
                    )
                )
            )
            monthly_revenue = float(monthly_revenue_result.scalar() or 0)
            
            # Update Prometheus metrics
            ACTIVE_TENANTS.set(active_tenants)
            RUNNING_INSTANCES.set(running_instances)
            ACTIVE_SUBSCRIPTIONS.set(active_subscriptions)
            MONTHLY_REVENUE.set(monthly_revenue)
            
            return {
                "active_tenants": active_tenants,
                "running_instances": running_instances,
                "active_subscriptions": active_subscriptions,
                "monthly_revenue": monthly_revenue
            }
            
        except Exception as e:
            logger.error(f"Error getting application metrics: {e}")
            return {
                "error": str(e)
            }
    
    async def get_instance_metrics(self, instance_id: int) -> Dict[str, Any]:
        """Get detailed metrics for a specific Odoo instance"""
        try:
            # Get instance info
            result = await self.db.execute(
                select(OdooInstance).where(OdooInstance.id == instance_id)
            )
            instance = result.scalar_one_or_none()
            
            if not instance:
                return {"error": "Instance not found"}
            
            metrics = {
                "instance_id": instance_id,
                "container_name": instance.container_name,
                "status": instance.status,
                "port": instance.port,
                "created_at": instance.created_at,
                "started_at": instance.started_at
            }
            
            # Get container metrics if Docker is available
            if self.docker_client and instance.container_id:
                try:
                    container = self.docker_client.containers.get(instance.container_id)
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
                    memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0.0
                    
                    metrics.update({
                        "container_status": container.status,
                        "cpu_percent": cpu_percent,
                        "memory_usage_mb": memory_usage / (1024**2),
                        "memory_limit_mb": memory_limit / (1024**2),
                        "memory_percent": memory_percent,
                        "network_rx_bytes": stats['networks']['eth0']['rx_bytes'] if 'networks' in stats else 0,
                        "network_tx_bytes": stats['networks']['eth0']['tx_bytes'] if 'networks' in stats else 0
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not get container stats for {instance.container_name}: {e}")
                    metrics["container_error"] = str(e)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting instance metrics: {e}")
            return {"error": str(e)}
    
    async def get_tenant_metrics(self, tenant_id: int) -> Dict[str, Any]:
        """Get comprehensive metrics for a tenant"""
        try:
            # Get tenant info
            tenant_result = await self.db.execute(
                select(Tenant).where(Tenant.id == tenant_id)
            )
            tenant = tenant_result.scalar_one_or_none()
            
            if not tenant:
                return {"error": "Tenant not found"}
            
            # Get tenant instances
            instances_result = await self.db.execute(
                select(OdooInstance).where(OdooInstance.tenant_id == tenant_id)
            )
            instances = instances_result.scalars().all()
            
            # Get subscription info
            subscription_result = await self.db.execute(
                select(Subscription).where(
                    and_(
                        Subscription.tenant_id == tenant_id,
                        Subscription.status.in_(['active', 'trialing'])
                    )
                ).order_by(Subscription.created_at.desc())
            )
            subscription = subscription_result.scalar_one_or_none()
            
            # Calculate usage metrics
            total_instances = len(instances)
            running_instances = len([i for i in instances if i.status == 'running'])
            
            # Get recent audit logs
            audit_logs_result = await self.db.execute(
                select(AuditLog).where(
                    AuditLog.tenant_id == tenant_id
                ).order_by(AuditLog.created_at.desc()).limit(10)
            )
            recent_activities = audit_logs_result.scalars().all()
            
            return {
                "tenant_id": tenant_id,
                "tenant_name": tenant.name,
                "status": tenant.status,
                "created_at": tenant.created_at,
                "instances": {
                    "total": total_instances,
                    "running": running_instances,
                    "stopped": total_instances - running_instances
                },
                "subscription": {
                    "plan_id": subscription.plan_id if subscription else None,
                    "status": subscription.status if subscription else None,
                    "current_period_end": subscription.current_period_end if subscription else None
                },
                "usage": {
                    "user_count": tenant.user_count,
                    "max_users": tenant.max_users,
                    "storage_used": tenant.storage_used,
                    "storage_limit": tenant.storage_limit
                },
                "recent_activities": [
                    {
                        "action": log.action,
                        "details": log.details,
                        "created_at": log.created_at
                    }
                    for log in recent_activities
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting tenant metrics: {e}")
            return {"error": str(e)}
    
    async def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics over time"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get audit logs for activity tracking
            audit_logs_result = await self.db.execute(
                select(AuditLog).where(
                    AuditLog.created_at >= start_time
                ).order_by(AuditLog.created_at)
            )
            audit_logs = audit_logs_result.scalars().all()
            
            # Group activities by hour
            hourly_activity = {}
            for log in audit_logs:
                hour_key = log.created_at.strftime("%Y-%m-%d %H:00")
                if hour_key not in hourly_activity:
                    hourly_activity[hour_key] = 0
                hourly_activity[hour_key] += 1
            
            # Get instance creation/deletion trends
            instances_result = await self.db.execute(
                select(OdooInstance).where(
                    OdooInstance.created_at >= start_time
                )
            )
            new_instances = instances_result.scalars().all()
            
            hourly_instances = {}
            for instance in new_instances:
                hour_key = instance.created_at.strftime("%Y-%m-%d %H:00")
                if hour_key not in hourly_instances:
                    hourly_instances[hour_key] = 0
                hourly_instances[hour_key] += 1
            
            return {
                "period_hours": hours,
                "start_time": start_time,
                "end_time": datetime.utcnow(),
                "activity_by_hour": hourly_activity,
                "new_instances_by_hour": hourly_instances,
                "total_activities": len(audit_logs),
                "total_new_instances": len(new_instances)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}
    
    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get system alerts based on thresholds"""
        alerts = []
        
        try:
            # System resource alerts
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            if cpu_percent > 90:
                alerts.append({
                    "type": "critical",
                    "category": "system",
                    "message": f"High CPU usage: {cpu_percent:.1f}%",
                    "value": cpu_percent,
                    "threshold": 90,
                    "timestamp": datetime.utcnow()
                })
            elif cpu_percent > 80:
                alerts.append({
                    "type": "warning",
                    "category": "system",
                    "message": f"Elevated CPU usage: {cpu_percent:.1f}%",
                    "value": cpu_percent,
                    "threshold": 80,
                    "timestamp": datetime.utcnow()
                })
            
            if memory.percent > 90:
                alerts.append({
                    "type": "critical",
                    "category": "system",
                    "message": f"High memory usage: {memory.percent:.1f}%",
                    "value": memory.percent,
                    "threshold": 90,
                    "timestamp": datetime.utcnow()
                })
            
            if disk.percent > 90:
                alerts.append({
                    "type": "critical",
                    "category": "system",
                    "message": f"High disk usage: {disk.percent:.1f}%",
                    "value": disk.percent,
                    "threshold": 90,
                    "timestamp": datetime.utcnow()
                })
            
            # Application alerts
            # Check for failed instances
            failed_instances_result = await self.db.execute(
                select(func.count(OdooInstance.id)).where(OdooInstance.status == 'error')
            )
            failed_instances = failed_instances_result.scalar() or 0
            
            if failed_instances > 0:
                alerts.append({
                    "type": "warning",
                    "category": "application",
                    "message": f"{failed_instances} Odoo instances in error state",
                    "value": failed_instances,
                    "timestamp": datetime.utcnow()
                })
            
            # Check for overdue payments
            overdue_payments_result = await self.db.execute(
                select(func.count(Payment.id)).where(
                    and_(
                        Payment.status == 'pending',
                        Payment.created_at < datetime.utcnow() - timedelta(days=7)
                    )
                )
            )
            overdue_payments = overdue_payments_result.scalar() or 0
            
            if overdue_payments > 0:
                alerts.append({
                    "type": "warning",
                    "category": "billing",
                    "message": f"{overdue_payments} overdue payments",
                    "value": overdue_payments,
                    "timestamp": datetime.utcnow()
                })
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            alerts.append({
                "type": "error",
                "category": "system",
                "message": f"Error checking alerts: {str(e)}",
                "timestamp": datetime.utcnow()
            })
        
        return alerts
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        return generate_latest(REGISTRY).decode('utf-8')
    
    async def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record API request metrics"""
        API_REQUESTS.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        API_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

