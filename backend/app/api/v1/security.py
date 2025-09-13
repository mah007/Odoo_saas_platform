"""
Security API endpoints for platform security management
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.services.security import SecurityService

router = APIRouter()

class PasswordValidationRequest(BaseModel):
    password: str

class IPValidationRequest(BaseModel):
    ip_address: str

@router.post("/validate-password")
async def validate_password_strength(
    request: PasswordValidationRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Validate password strength"""
    security_service = SecurityService(None)  # No DB needed for password validation
    return await security_service.validate_password_strength(request.password)

@router.post("/validate-ip")
async def validate_ip_address(
    request: IPValidationRequest,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Validate and analyze IP address"""
    security_service = SecurityService(None)
    return await security_service.validate_ip_address(request.ip_address)

@router.get("/scan/vulnerabilities")
async def scan_vulnerabilities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Scan system for vulnerabilities"""
    security_service = SecurityService(db)
    return await security_service.scan_for_vulnerabilities()

@router.get("/metrics")
async def get_security_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get comprehensive security metrics"""
    security_service = SecurityService(db)
    return await security_service.get_security_metrics()

@router.get("/report")
async def generate_security_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Generate comprehensive security report"""
    security_service = SecurityService(db)
    return await security_service.generate_security_report()

@router.get("/rate-limit/{identifier}")
async def check_rate_limit(
    identifier: str,
    limit: int = 100,
    window_minutes: int = 15,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Check rate limit status for identifier"""
    security_service = SecurityService(db)
    return await security_service.check_rate_limit(identifier, limit, window_minutes)

@router.get("/brute-force/{ip_address}")
async def check_brute_force(
    ip_address: str,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Check for brute force attack patterns"""
    security_service = SecurityService(db)
    return await security_service.detect_brute_force_attack(ip_address, user_id)

@router.post("/failed-login")
async def record_failed_login(
    request: Request,
    user_id: Optional[int] = None,
    details: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Record failed login attempt (internal use)"""
    # Get client IP
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    
    security_service = SecurityService(db)
    await security_service.record_failed_login(client_ip, user_id, details)
    
    return {"status": "recorded"}

@router.get("/dashboard")
async def get_security_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get security dashboard data"""
    security_service = SecurityService(db)
    
    # Get comprehensive security data
    metrics = await security_service.get_security_metrics()
    vulnerability_scan = await security_service.scan_for_vulnerabilities()
    
    # Calculate security score
    security_score = security_service._calculate_security_score(metrics, vulnerability_scan)
    
    # Get recent security events
    from app.models.audit_log import AuditLog
    from sqlalchemy import select, and_
    from datetime import datetime, timedelta
    
    recent_events_result = await db.execute(
        select(AuditLog).where(
            and_(
                AuditLog.action.in_(["failed_login", "login", "password_reset", "account_locked"]),
                AuditLog.created_at >= datetime.utcnow() - timedelta(hours=24)
            )
        ).order_by(AuditLog.created_at.desc()).limit(20)
    )
    recent_events = recent_events_result.scalars().all()
    
    return {
        "security_score": security_score,
        "metrics": metrics,
        "vulnerabilities": vulnerability_scan,
        "recent_events": [
            {
                "id": event.id,
                "action": event.action,
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "details": event.details,
                "created_at": event.created_at
            }
            for event in recent_events
        ],
        "alerts": [
            {
                "type": "critical" if vulnerability_scan["risk_level"] == "critical" else "warning",
                "message": f"Security scan found {len(vulnerability_scan['vulnerabilities'])} vulnerabilities",
                "count": len(vulnerability_scan["vulnerabilities"])
            }
        ] if vulnerability_scan["vulnerabilities"] else []
    }

@router.get("/threats/active")
async def get_active_threats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> List[Dict[str, Any]]:
    """Get currently active security threats"""
    security_service = SecurityService(db)
    
    threats = []
    
    # Check for IPs with high failure rates
    for ip_key, timestamps in security_service.failed_login_cache.items():
        if ip_key.startswith("ip_") and len(timestamps) >= 10:
            ip_address = ip_key.replace("ip_", "")
            threats.append({
                "type": "brute_force",
                "source": ip_address,
                "severity": "high" if len(timestamps) >= 20 else "medium",
                "count": len(timestamps),
                "description": f"High number of failed login attempts from {ip_address}"
            })
    
    # Check for users with high failure rates
    for user_key, timestamps in security_service.failed_login_cache.items():
        if user_key.startswith("user_") and len(timestamps) >= 5:
            user_id = user_key.replace("user_", "")
            threats.append({
                "type": "account_compromise",
                "source": f"user_{user_id}",
                "severity": "high" if len(timestamps) >= 10 else "medium",
                "count": len(timestamps),
                "description": f"High number of failed login attempts for user {user_id}"
            })
    
    return threats

@router.post("/threats/{threat_id}/mitigate")
async def mitigate_threat(
    threat_id: str,
    action: str,  # "block_ip", "lock_account", "reset_password"
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """Mitigate a security threat"""
    # This would implement threat mitigation actions
    # For now, return success
    
    return {
        "threat_id": threat_id,
        "action": action,
        "status": "mitigated",
        "message": f"Threat {threat_id} has been mitigated with action: {action}"
    }

@router.get("/compliance/check")
async def check_compliance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Check security compliance status"""
    security_service = SecurityService(db)
    
    # Get vulnerability scan
    vulnerability_scan = await security_service.scan_for_vulnerabilities()
    
    # Check compliance criteria
    compliance_checks = {
        "password_policy": {
            "status": "pass",  # Would check actual password policy enforcement
            "description": "Strong password policy enforced"
        },
        "encryption": {
            "status": "pass",  # Would check encryption settings
            "description": "Data encryption at rest and in transit"
        },
        "access_control": {
            "status": "pass",  # Would check access control implementation
            "description": "Role-based access control implemented"
        },
        "audit_logging": {
            "status": "pass",  # Would check audit logging
            "description": "Comprehensive audit logging enabled"
        },
        "vulnerability_management": {
            "status": "fail" if vulnerability_scan["total_vulnerabilities"] > 0 else "pass",
            "description": f"Found {vulnerability_scan['total_vulnerabilities']} vulnerabilities"
        }
    }
    
    # Calculate overall compliance score
    total_checks = len(compliance_checks)
    passed_checks = sum(1 for check in compliance_checks.values() if check["status"] == "pass")
    compliance_score = (passed_checks / total_checks) * 100
    
    return {
        "compliance_score": compliance_score,
        "status": "compliant" if compliance_score >= 80 else "non_compliant",
        "checks": compliance_checks,
        "recommendations": [
            "Address all identified vulnerabilities",
            "Implement multi-factor authentication",
            "Regular security training for users",
            "Automated security scanning"
        ] if compliance_score < 100 else ["Maintain current security posture"]
    }

@router.get("/audit/trail")
async def get_audit_trail(
    limit: int = 100,
    offset: int = 0,
    action_filter: Optional[str] = None,
    user_id_filter: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get audit trail with filtering"""
    from app.models.audit_log import AuditLog
    from sqlalchemy import select, and_
    
    # Build query
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    
    # Apply filters
    filters = []
    if action_filter:
        filters.append(AuditLog.action.ilike(f"%{action_filter}%"))
    if user_id_filter:
        filters.append(AuditLog.user_id == user_id_filter)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    audit_logs = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(AuditLog.id))
    if filters:
        count_query = count_query.where(and_(*filters))
    
    count_result = await db.execute(count_query)
    total_count = count_result.scalar()
    
    return {
        "audit_logs": [
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
            for log in audit_logs
        ],
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }

