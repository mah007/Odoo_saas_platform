"""
Security service for comprehensive platform security management
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
import secrets
import re
import logging
from ipaddress import ip_address, ip_network
import asyncio
from collections import defaultdict
import json

from app.models.user import User
from app.models.audit_log import AuditLog
from app.core.config import settings

logger = logging.getLogger(__name__)

class SecurityService:
    """Service for security management and threat detection"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rate_limit_cache = defaultdict(list)
        self.failed_login_cache = defaultdict(list)
        self.suspicious_activity_cache = defaultdict(list)
    
    async def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength according to security policy"""
        issues = []
        score = 0
        
        # Length check
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        elif len(password) >= 12:
            score += 2
        else:
            score += 1
        
        # Character variety checks
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain lowercase letters")
        else:
            score += 1
            
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain uppercase letters")
        else:
            score += 1
            
        if not re.search(r'\d', password):
            issues.append("Password must contain numbers")
        else:
            score += 1
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain special characters")
        else:
            score += 1
        
        # Common password check
        common_passwords = [
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "dragon", "master"
        ]
        if password.lower() in common_passwords:
            issues.append("Password is too common")
            score = max(0, score - 2)
        
        # Sequential characters check
        if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde)', password.lower()):
            issues.append("Password contains sequential characters")
            score = max(0, score - 1)
        
        # Determine strength
        if score >= 6:
            strength = "strong"
        elif score >= 4:
            strength = "medium"
        elif score >= 2:
            strength = "weak"
        else:
            strength = "very_weak"
        
        return {
            "valid": len(issues) == 0,
            "strength": strength,
            "score": score,
            "issues": issues
        }
    
    async def check_rate_limit(self, identifier: str, limit: int = 100, window_minutes: int = 15) -> Dict[str, Any]:
        """Check if identifier has exceeded rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old entries
        self.rate_limit_cache[identifier] = [
            timestamp for timestamp in self.rate_limit_cache[identifier]
            if timestamp > window_start
        ]
        
        # Check current count
        current_count = len(self.rate_limit_cache[identifier])
        
        if current_count >= limit:
            return {
                "allowed": False,
                "current_count": current_count,
                "limit": limit,
                "reset_time": window_start + timedelta(minutes=window_minutes),
                "retry_after": window_minutes * 60
            }
        
        # Add current request
        self.rate_limit_cache[identifier].append(now)
        
        return {
            "allowed": True,
            "current_count": current_count + 1,
            "limit": limit,
            "remaining": limit - current_count - 1
        }
    
    async def detect_brute_force_attack(self, ip_address: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Detect potential brute force attacks"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=30)  # 30-minute window
        
        # Check failed login attempts from IP
        ip_key = f"ip_{ip_address}"
        self.failed_login_cache[ip_key] = [
            timestamp for timestamp in self.failed_login_cache[ip_key]
            if timestamp > window_start
        ]
        
        ip_failures = len(self.failed_login_cache[ip_key])
        
        # Check failed login attempts for user
        user_failures = 0
        if user_id:
            user_key = f"user_{user_id}"
            self.failed_login_cache[user_key] = [
                timestamp for timestamp in self.failed_login_cache[user_key]
                if timestamp > window_start
            ]
            user_failures = len(self.failed_login_cache[user_key])
        
        # Determine threat level
        threat_level = "low"
        is_suspicious = False
        
        if ip_failures >= 20 or user_failures >= 10:
            threat_level = "critical"
            is_suspicious = True
        elif ip_failures >= 10 or user_failures >= 5:
            threat_level = "high"
            is_suspicious = True
        elif ip_failures >= 5 or user_failures >= 3:
            threat_level = "medium"
            is_suspicious = True
        
        return {
            "is_suspicious": is_suspicious,
            "threat_level": threat_level,
            "ip_failures": ip_failures,
            "user_failures": user_failures,
            "window_minutes": 30
        }
    
    async def record_failed_login(self, ip_address: str, user_id: Optional[int] = None, details: Optional[str] = None):
        """Record failed login attempt"""
        now = datetime.utcnow()
        
        # Add to cache
        ip_key = f"ip_{ip_address}"
        self.failed_login_cache[ip_key].append(now)
        
        if user_id:
            user_key = f"user_{user_id}"
            self.failed_login_cache[user_key].append(now)
        
        # Log to audit
        audit_log = AuditLog(
            user_id=user_id,
            action="failed_login",
            details=details or f"Failed login attempt from {ip_address}",
            ip_address=ip_address,
            created_at=now
        )
        
        self.db.add(audit_log)
        await self.db.commit()
    
    async def validate_ip_address(self, ip_addr: str) -> Dict[str, Any]:
        """Validate and analyze IP address"""
        try:
            ip = ip_address(ip_addr)
            
            # Check if IP is in allowed/blocked lists
            is_private = ip.is_private
            is_loopback = ip.is_loopback
            is_multicast = ip.is_multicast
            
            # Check against known malicious IP ranges (simplified)
            blocked_ranges = [
                "10.0.0.0/8",      # Private
                "172.16.0.0/12",   # Private
                "192.168.0.0/16",  # Private
            ]
            
            is_blocked = False
            for range_str in blocked_ranges:
                if ip in ip_network(range_str):
                    is_blocked = True
                    break
            
            # Geolocation check (simplified - in production use a service like MaxMind)
            country_code = "unknown"
            is_tor = False  # Would check against Tor exit node list
            is_vpn = False  # Would check against VPN IP ranges
            
            return {
                "valid": True,
                "ip_address": str(ip),
                "version": ip.version,
                "is_private": is_private,
                "is_loopback": is_loopback,
                "is_multicast": is_multicast,
                "is_blocked": is_blocked,
                "country_code": country_code,
                "is_tor": is_tor,
                "is_vpn": is_vpn,
                "risk_score": self._calculate_ip_risk_score(ip, is_tor, is_vpn, country_code)
            }
            
        except ValueError:
            return {
                "valid": False,
                "error": "Invalid IP address format"
            }
    
    def _calculate_ip_risk_score(self, ip, is_tor: bool, is_vpn: bool, country_code: str) -> int:
        """Calculate risk score for IP address (0-100)"""
        score = 0
        
        if is_tor:
            score += 50
        if is_vpn:
            score += 30
        if ip.is_private:
            score -= 20  # Private IPs are generally safer
        
        # High-risk countries (simplified)
        high_risk_countries = ["XX", "YY"]  # Would be actual country codes
        if country_code in high_risk_countries:
            score += 25
        
        return max(0, min(100, score))
    
    async def scan_for_vulnerabilities(self) -> Dict[str, Any]:
        """Scan system for common vulnerabilities"""
        vulnerabilities = []
        
        # Check for weak passwords
        weak_password_result = await self.db.execute(
            select(func.count(User.id)).where(
                User.password_hash.like('%weak%')  # Simplified check
            )
        )
        weak_passwords = weak_password_result.scalar() or 0
        
        if weak_passwords > 0:
            vulnerabilities.append({
                "type": "weak_passwords",
                "severity": "medium",
                "count": weak_passwords,
                "description": f"{weak_passwords} users have weak passwords"
            })
        
        # Check for inactive admin accounts
        inactive_admins_result = await self.db.execute(
            select(func.count(User.id)).where(
                and_(
                    User.is_admin == True,
                    User.last_login < datetime.utcnow() - timedelta(days=90)
                )
            )
        )
        inactive_admins = inactive_admins_result.scalar() or 0
        
        if inactive_admins > 0:
            vulnerabilities.append({
                "type": "inactive_admin_accounts",
                "severity": "high",
                "count": inactive_admins,
                "description": f"{inactive_admins} admin accounts inactive for 90+ days"
            })
        
        # Check for users without MFA (if implemented)
        # This would check for users without two-factor authentication
        
        # Check for excessive privileges
        # This would analyze user permissions and flag over-privileged accounts
        
        return {
            "scan_time": datetime.utcnow(),
            "total_vulnerabilities": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "risk_level": self._calculate_overall_risk_level(vulnerabilities)
        }
    
    def _calculate_overall_risk_level(self, vulnerabilities: List[Dict]) -> str:
        """Calculate overall risk level based on vulnerabilities"""
        if not vulnerabilities:
            return "low"
        
        severity_scores = {"low": 1, "medium": 3, "high": 5, "critical": 10}
        total_score = sum(severity_scores.get(vuln.get("severity", "low"), 1) for vuln in vulnerabilities)
        
        if total_score >= 20:
            return "critical"
        elif total_score >= 10:
            return "high"
        elif total_score >= 5:
            return "medium"
        else:
            return "low"
    
    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive security metrics"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Failed login attempts
        failed_logins_24h = await self.db.execute(
            select(func.count(AuditLog.id)).where(
                and_(
                    AuditLog.action == "failed_login",
                    AuditLog.created_at >= last_24h
                )
            )
        )
        failed_logins_count = failed_logins_24h.scalar() or 0
        
        # Successful logins
        successful_logins_24h = await self.db.execute(
            select(func.count(AuditLog.id)).where(
                and_(
                    AuditLog.action == "login",
                    AuditLog.created_at >= last_24h
                )
            )
        )
        successful_logins_count = successful_logins_24h.scalar() or 0
        
        # Active sessions (simplified)
        active_users_result = await self.db.execute(
            select(func.count(User.id)).where(
                User.last_login >= last_24h
            )
        )
        active_users = active_users_result.scalar() or 0
        
        # Security events
        security_events_result = await self.db.execute(
            select(func.count(AuditLog.id)).where(
                and_(
                    AuditLog.action.in_(["failed_login", "password_reset", "account_locked"]),
                    AuditLog.created_at >= last_7d
                )
            )
        )
        security_events = security_events_result.scalar() or 0
        
        return {
            "period": {
                "last_24h": last_24h,
                "last_7d": last_7d,
                "current": now
            },
            "authentication": {
                "failed_logins_24h": failed_logins_count,
                "successful_logins_24h": successful_logins_count,
                "success_rate": (successful_logins_count / (successful_logins_count + failed_logins_count) * 100) if (successful_logins_count + failed_logins_count) > 0 else 100
            },
            "activity": {
                "active_users_24h": active_users,
                "security_events_7d": security_events
            },
            "threat_detection": {
                "blocked_ips": len([k for k in self.failed_login_cache.keys() if k.startswith("ip_") and len(self.failed_login_cache[k]) >= 10]),
                "suspicious_activities": len(self.suspicious_activity_cache)
            }
        }
    
    async def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        # Get security metrics
        metrics = await self.get_security_metrics()
        
        # Scan for vulnerabilities
        vulnerability_scan = await self.scan_for_vulnerabilities()
        
        # Get recent security events
        recent_events_result = await self.db.execute(
            select(AuditLog).where(
                and_(
                    AuditLog.action.in_(["failed_login", "login", "password_reset", "account_locked"]),
                    AuditLog.created_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).order_by(AuditLog.created_at.desc()).limit(50)
        )
        recent_events = recent_events_result.scalars().all()
        
        # Calculate security score
        security_score = self._calculate_security_score(metrics, vulnerability_scan)
        
        return {
            "report_generated": datetime.utcnow(),
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
            "recommendations": self._generate_security_recommendations(vulnerability_scan, metrics)
        }
    
    def _calculate_security_score(self, metrics: Dict, vulnerabilities: Dict) -> int:
        """Calculate overall security score (0-100)"""
        base_score = 100
        
        # Deduct points for vulnerabilities
        vuln_deductions = {
            "critical": 30,
            "high": 20,
            "medium": 10,
            "low": 5
        }
        
        for vuln in vulnerabilities.get("vulnerabilities", []):
            severity = vuln.get("severity", "low")
            base_score -= vuln_deductions.get(severity, 5)
        
        # Deduct points for poor authentication metrics
        auth_metrics = metrics.get("authentication", {})
        success_rate = auth_metrics.get("success_rate", 100)
        
        if success_rate < 90:
            base_score -= (90 - success_rate) * 2
        
        # Deduct points for high threat activity
        threat_metrics = metrics.get("threat_detection", {})
        blocked_ips = threat_metrics.get("blocked_ips", 0)
        
        if blocked_ips > 10:
            base_score -= min(20, blocked_ips)
        
        return max(0, min(100, base_score))
    
    def _generate_security_recommendations(self, vulnerabilities: Dict, metrics: Dict) -> List[str]:
        """Generate security recommendations based on scan results"""
        recommendations = []
        
        # Vulnerability-based recommendations
        for vuln in vulnerabilities.get("vulnerabilities", []):
            if vuln["type"] == "weak_passwords":
                recommendations.append("Enforce stronger password policies and require password updates")
            elif vuln["type"] == "inactive_admin_accounts":
                recommendations.append("Review and disable inactive administrator accounts")
        
        # Metrics-based recommendations
        auth_metrics = metrics.get("authentication", {})
        if auth_metrics.get("success_rate", 100) < 95:
            recommendations.append("Investigate high failure rate in authentication attempts")
        
        threat_metrics = metrics.get("threat_detection", {})
        if threat_metrics.get("blocked_ips", 0) > 5:
            recommendations.append("Consider implementing additional IP-based security measures")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Security posture is good. Continue regular monitoring and updates")
        
        return recommendations

