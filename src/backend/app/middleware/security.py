"""
Security Middleware

Provides HTTPS enforcement and security headers.
"""
from flask import request, redirect
import logging

logger = logging.getLogger(__name__)


def register_security_middleware(app):
    """
    Register security middleware for HTTPS enforcement and security headers.
    """
    force_https = app.config.get('FORCE_HTTPS', False)
    security_headers_enabled = app.config.get('SECURITY_HEADERS_ENABLED', True)
    
    if force_https:
        @app.before_request
        def enforce_https():
            """Redirect HTTP to HTTPS in production"""
            if not request.is_secure and request.headers.get('X-Forwarded-Proto', 'http') != 'https':
                # Skip health checks and local development
                if request.path.startswith('/api/v1/health'):
                    return None
                if request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
                    return None
                
                url = request.url.replace('http://', 'https://', 1)
                logger.info(f"Redirecting HTTP to HTTPS: {request.url} -> {url}")
                return redirect(url, code=301)
    
    if security_headers_enabled:
        @app.after_request
        def add_security_headers(response):
            """Add security headers to all responses"""
            # Prevent clickjacking
            response.headers['X-Frame-Options'] = 'DENY'
            
            # Prevent MIME type sniffing
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # Enable XSS protection (for older browsers)
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Strict Transport Security (HSTS) - only add if using HTTPS
            if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https':
                # max-age=31536000 = 1 year
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            # Content Security Policy (basic policy)
            # Adjust as needed for your frontend requirements
            response.headers['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'none'"
            
            # Referrer Policy
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions Policy (formerly Feature Policy)
            response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
            
            return response
        
        logger.info("Security headers enabled")
    
    if force_https:
        logger.info("HTTPS enforcement enabled")
