"""
Health Check Routes

Provides comprehensive health checks for all service dependencies:
- Database (PostgreSQL)
- Redis (cache + Celery broker)
- Celery workers (via ping)

Used by load balancers, monitoring systems, and orchestration platforms.
"""
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text
import logging

bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)


@bp.route('/api/v1/health', methods=['GET'])
def health():
    """
    Basic health check - returns 200 if service is running.
    Use /api/v1/health/full for detailed dependency checks.
    """
    return jsonify({
        "status": "healthy",
        "service": "backend"
    }), 200


@bp.route('/api/v1/health/full', methods=['GET'])
def health_full():
    """
    Comprehensive health check - verifies all dependencies.
    Returns 200 only if all systems operational, 503 otherwise.
    """
    health_status = {
        "status": "healthy",
        "service": "backend",
        "checks": {}
    }
    
    all_healthy = True
    
    # Check Database
    try:
        from app.extensions import db
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        all_healthy = False
    
    # Check Redis
    try:
        redis_client = current_app.redis
        redis_client.ping()
        health_status["checks"]["redis"] = {"status": "healthy"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        all_healthy = False
    
    # Check Celery (optional - don't fail if workers are down)
    try:
        from app.tasks.celery_app import celery
        # Ping workers with 1 second timeout
        inspector = celery.control.inspect(timeout=1.0)
        active_workers = inspector.ping()
        
        if active_workers:
            health_status["checks"]["celery"] = {
                "status": "healthy",
                "workers": len(active_workers)
            }
        else:
            logger.warning("No Celery workers responding")
            health_status["checks"]["celery"] = {
                "status": "degraded",
                "message": "No workers responding"
            }
            # Don't mark entire service unhealthy if just celery workers are down
    except Exception as e:
        logger.warning(f"Celery health check failed: {e}")
        health_status["checks"]["celery"] = {
            "status": "degraded",
            "error": str(e)
        }
    
    # Set overall status
    if not all_healthy:
        health_status["status"] = "unhealthy"
        return jsonify(health_status), 503
    
    return jsonify(health_status), 200


@bp.route('/api/v1/health/ready', methods=['GET'])
def health_ready():
    """
    Readiness check - returns 200 when service is ready to accept traffic.
    Used by Kubernetes readiness probes.
    """
    try:
        from app.extensions import db
        # Quick database check
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        
        # Check Redis
        current_app.redis.ping()
        
        return jsonify({"status": "ready"}), 200
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({"status": "not_ready", "error": str(e)}), 503


@bp.route('/api/v1/health/live', methods=['GET'])
def health_live():
    """
    Liveness check - returns 200 if service is alive (but not necessarily ready).
    Used by Kubernetes liveness probes.
    """
    return jsonify({"status": "alive"}), 200
