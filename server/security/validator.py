"""
Security Validator - ZombieCoder Local AI
Agent Workstation Layer - "যেখানে কোড ও কথা বলে"
"""

import re
import logging
import hashlib
import secrets
from typing import Tuple, List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Security validation result"""
    is_valid: bool
    sanitized_content: str
    issues: List[str]
    risk_level: str  # low, medium, high, critical
    metadata: Dict[str, Any]


class SecurityValidator:
    """Comprehensive security validator with multi-layer protection"""
    
    def __init__(self):
        self.dangerous_patterns = self._compile_dangerous_patterns()
        self.sensitive_data_patterns = self._compile_sensitive_patterns()
        self.allowed_paths = self._get_allowed_paths()
        self.stats = {
            'validations': 0,
            'blocked': 0,
            'sanitized': 0,
            'high_risk': 0
        }
    
    def _compile_dangerous_patterns(self) -> Dict[str, re.Pattern]:
        """Compile dangerous pattern regexes"""
        patterns = {
            # System commands
            'system_commands': re.compile(
                r'\b(exec|eval|system|subprocess|os\.system|os\.popen|'
                r'commands\.getoutput|popen|spawn|fork)\b', 
                re.IGNORECASE
            ),
            
            # File operations
            'file_operations': re.compile(
                r'\b(open|write|read|delete|remove|unlink|rename|chmod|chown)\s*\([^)]*\)',
                re.IGNORECASE
            ),
            
            # Network operations
            'network_operations': re.compile(
                r'\b(socket|urllib|requests|http\.client|ftplib|telnetlib)\b',
                re.IGNORECASE
            ),
            
            # Code injection
            'code_injection': re.compile(
                r'(<script[^>]*>.*?</script>|on\w+\s*=|javascript:|vbscript:)',
                re.IGNORECASE | re.DOTALL
            ),
            
            # SQL injection
            'sql_injection': re.compile(
                r'\b(union\s+select|insert\s+into|delete\s+from|drop\s+table|'
                r'exec\s+master\.\w+|xp_cmdshell)\b',
                re.IGNORECASE
            ),
            
            # Path traversal
            'path_traversal': re.compile(
                r'(\.\.[\\/]|~[/\\]|[/\\]\.\.[/\\])',
                re.IGNORECASE
            ),
            
            # Shell injection
            'shell_injection': re.compile(
                r'[;&|`$\x00-\x1f\x7f-\x9f]',
                re.IGNORECASE
            )
        }
        return patterns
    
    def _compile_sensitive_patterns(self) -> Dict[str, re.Pattern]:
        """Compile sensitive data patterns"""
        patterns = {
            # API keys and secrets
            'api_keys': re.compile(
                r'\b(sk-[a-zA-Z0-9]{32}|[a-zA-Z0-9]{32}|[a-zA-Z0-9]{40})\b'
            ),
            
            # Email addresses
            'emails': re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            
            # Phone numbers
            'phone_numbers': re.compile(
                r'\b(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
            ),
            
            # Credit cards (simplified)
            'credit_cards': re.compile(
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
            ),
            
            # Social Security Numbers
            'ssn': re.compile(
                r'\b\d{3}-?\d{2}-?\d{4}\b'
            )
        }
        return patterns
    
    def _get_allowed_paths(self) -> List[str]:
        """Get list of allowed file paths"""
        return [
            './data/',
            './logs/',
            './workspace/',
            './temp/',
            './cache/'
        ]
    
    async def initialize(self):
        """Initialize security manager"""
        logger.info("🔐 Security validator initialized")
        return True
    
    def _calculate_risk_level(self, issues: List[str]) -> str:
        """Calculate risk level based on issues"""
        if any('critical' in issue.lower() for issue in issues):
            return 'critical'
        elif any('high' in issue.lower() for issue in issues):
            return 'high'
        elif any('medium' in issue.lower() for issue in issues):
            return 'medium'
        else:
            return 'low'
    
    def validate_input(self, content: str, context: str = "") -> ValidationResult:
        """Validate input content"""
        self.stats['validations'] += 1
        
        issues = []
        sanitized_content = content
        
        # Check for dangerous patterns
        for pattern_name, pattern in self.dangerous_patterns.items():
            matches = pattern.findall(content)
            if matches:
                issues.append(f"Dangerous pattern detected: {pattern_name}")
                # Sanitize by removing dangerous patterns
                sanitized_content = pattern.sub('[REDACTED]', sanitized_content)
        
        # Check for sensitive data
        sensitive_found = []
        for data_type, pattern in self.sensitive_data_patterns.items():
            matches = pattern.findall(sanitized_content)
            if matches:
                sensitive_found.append(data_type)
                # Redact sensitive data
                sanitized_content = pattern.sub(f'[{data_type.upper()}_REDACTED]', sanitized_content)
        
        if sensitive_found:
            issues.append(f"Sensitive data detected: {', '.join(sensitive_found)}")
        
        # Determine validity
        is_valid = len([issue for issue in issues if 'critical' in issue.lower() or 'high' in issue.lower()]) == 0
        
        if not is_valid:
            self.stats['blocked'] += 1
        if sanitized_content != content:
            self.stats['sanitized'] += 1
        if 'high' in self._calculate_risk_level(issues) or 'critical' in self._calculate_risk_level(issues):
            self.stats['high_risk'] += 1
        
        return ValidationResult(
            is_valid=is_valid,
            sanitized_content=sanitized_content,
            issues=issues,
            risk_level=self._calculate_risk_level(issues),
            metadata={
                'context': context,
                'original_length': len(content),
                'sanitized_length': len(sanitized_content),
                'timestamp': datetime.now().isoformat()
            }
        )
    
    async def validate_request(self, content: str, session_id: str = "", context: str = "") -> Tuple[bool, Dict[str, Any]]:
        """Async validation for requests"""
        result = self.validate_input(content, context)
        
        return result.is_valid, {
            'sanitized_content': result.sanitized_content,
            'issues': result.issues,
            'risk_level': result.risk_level,
            'metadata': result.metadata,
            'session_id': session_id
        }
    
    def validate_file_path(self, path: str) -> bool:
        """Validate file path is within allowed directories"""
        import os
        
        # Normalize path
        normalized_path = os.path.normpath(path)
        
        # Check if path is absolute
        if os.path.isabs(normalized_path):
            logger.warning(f"Blocked absolute path: {path}")
            return False
        
        # Check for path traversal attempts
        if '..' in normalized_path or '~' in normalized_path:
            logger.warning(f"Blocked path traversal attempt: {path}")
            return False
        
        # Check if path is within allowed directories
        for allowed_path in self.allowed_paths:
            if normalized_path.startswith(allowed_path.rstrip('/')):
                return True
        
        logger.warning(f"Blocked unauthorized path access: {path}")
        return False
    
    def sanitize_output(self, content: str) -> str:
        """Sanitize output content"""
        sanitized = content
        
        # Remove sensitive data from output
        for data_type, pattern in self.sensitive_data_patterns.items():
            sanitized = pattern.sub(f'[{data_type.upper()}_REDACTED]', sanitized)
        
        # Remove dangerous patterns from output
        for pattern_name, pattern in self.dangerous_patterns.items():
            sanitized = pattern.sub('[SANITIZED]', sanitized)
        
        return sanitized
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    def hash_content(self, content: str) -> str:
        """Hash content for integrity checking"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        return {
            'validations': self.stats['validations'],
            'blocked': self.stats['blocked'],
            'sanitized': self.stats['sanitized'],
            'high_risk': self.stats['high_risk'],
            'risk_percentage': round(
                (self.stats['high_risk'] / max(self.stats['validations'], 1)) * 100, 2
            )
        }
    
    def reset_stats(self):
        """Reset security statistics"""
        self.stats = {
            'validations': 0,
            'blocked': 0,
            'sanitized': 0,
            'high_risk': 0
        }


def create_security_manager() -> SecurityValidator:
    """Factory function to create security manager"""
    return SecurityValidator()