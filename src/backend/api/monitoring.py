from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Callable
from typing import AsyncGenerator, Coroutine
"""
API endpoints for monitoring, health, and status checks.
"""

import structlog
from fastapi import APIRouter

from backend.core.alerting import alert_manager
from backend.infrastructure.database.database import check_database_health

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health", tags=["Health"])
async def health_check() -> None:
    """Basic health check."""
    return {"status": "ok"}


@router.get("/ready", tags=["Health"])
async def ready_check() -> None:
    """Readiness check for services like database."""
    db_ok, db_status = await check_database_health()

    if not db_ok:
        logger.warning("readiness.check.failed", database_status=db_status)
        return {"status": "not_ready", "services": {"database": db_status}}

    return {"status": "ready", "services": {"database": db_status}}


@router.get("/metrics", tags=["Monitoring"])
async def metrics_endpoint() -> None:
    """Prometheus metrics endpoint."""
    # This would typically be handled by a Prometheus client library middleware
    # returning the metrics in the correct format.
    # This is a placeholder.
    return {"message": "Prometheus metrics would be exposed here."}


@router.get("/status", tags=["Monitoring"])
async def detailed_status() -> None:
    """Get detailed status of the application components."""
    # In a real app, this would check orchestrator pool, model status, etc.
    return {
        "service": "FoodSave AI Backend",
        "version": "1.0.0",
        "status": "healthy",
        "components": {
            "database": (await check_database_health())[1],
            "cache": "connected",  # Placeholder
            "orchestrator_pool": "active",  # Placeholder
        },
    }


@router.get("/alerts", tags=["Monitoring"])
async def get_alerts() -> None:
    """Get currently active alerts."""
    return alert_manager.get_active_alerts()


@router.get("/alerts/history", tags=["Monitoring"])
async def get_alert_history(hours: int = 24) -> None:
    """Get alert history for the last N hours."""
    return alert_manager.get_alert_history(hours=hours)


@router.post("/alerts/{rule_name}/acknowledge", tags=["Monitoring"])
async def acknowledge_alert(rule_name: str, user: str = "admin") -> None:
    """Acknowledge an active alert."""
    success = alert_manager.acknowledge_alert(rule_name, user)
    return {"status": "acknowledged" if success else "alert_not_found"}


@router.post("/alerts/{rule_name}/resolve", tags=["Monitoring"])
async def resolve_alert(rule_name: str) -> None:
    """Manually resolve an active alert."""
    success = alert_manager.resolve_alert(rule_name)
    return {"status": "resolved" if success else "alert_not_found"}


@router.post("/alerts/rules", tags=["Monitoring"])
async def add_alert_rule(rule_data: dict) -> None:
    """Add a new alerting rule."""
    try:
        alert_manager.add_rule(
            name=rule_data["name"],
            metric=rule_data["metric"],
            threshold=rule_data["threshold"],
            comparison=rule_data["comparison"],
            duration=rule_data["duration"],
            severity=rule_data["severity"],
            description=rule_data.get("description", ""),
        )
        return {"status": "rule_added"}
    except KeyError as e:
        return {"status": "error", "message": f"Missing required field: {e}"}


@router.delete("/alerts/rules/{rule_name}", tags=["Monitoring"])
async def remove_alert_rule(rule_name: str) -> None:
    """Remove an alerting rule."""
    success = alert_manager.remove_rule(rule_name)
    return {"status": "rule_removed" if success else "rule_not_found"}
