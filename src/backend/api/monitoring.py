from __future__ import annotations

from typing import Any, AsyncGenerator, Callable, Coroutine, Dict, List, Optional, Union

"""
API endpoints for monitoring, health, and status checks.
"""

import json
import time
from datetime import datetime

import structlog
from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from backend.agents.agent_factory import AgentFactory
from backend.core.alerting import alert_manager
from backend.core.perplexity_client import perplexity_client
from backend.infrastructure.database.database import check_database_health

router = APIRouter()
logger = structlog.get_logger()


async def check_agents_health() -> Dict[str, Any]:
    """Check health of all registered agents"""
    try:
        factory = AgentFactory()
        agent_status = {}

        # Test each registered agent type
        for agent_type in factory.AGENT_REGISTRY.keys():
            try:
                agent = factory.create_agent(agent_type)
                # Check if agent has health check method
                if hasattr(agent, "is_healthy"):
                    is_healthy = agent.is_healthy()
                else:
                    # Basic health check - try to get metadata
                    metadata = agent.get_metadata()
                    is_healthy = metadata is not None

                agent_status[agent_type] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "last_check": datetime.now().isoformat(),
                }
            except Exception as e:
                agent_status[agent_type] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.now().isoformat(),
                }

        return {
            "status": (
                "healthy"
                if all(
                    status["status"] == "healthy" for status in agent_status.values()
                )
                else "unhealthy"
            ),
            "agents": agent_status,
        }
    except Exception as e:
        logger.error(f"Agent health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "agents": {}}


async def check_external_apis_health() -> Dict[str, Any]:
    """Check health of external APIs"""
    api_status = {}

    # Check Perplexity API
    try:
        perplexity_configured = perplexity_client.is_configured()
        perplexity_available = perplexity_client.is_available
        api_status["perplexity"] = {
            "status": (
                "healthy"
                if perplexity_configured and perplexity_available
                else "unhealthy"
            ),
            "configured": perplexity_configured,
            "available": perplexity_available,
            "last_check": datetime.now().isoformat(),
        }
    except Exception as e:
        api_status["perplexity"] = {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.now().isoformat(),
        }

    # Check MMLW embeddings (if available)
    try:
        from backend.core.mmlw_embedding_client import mmlw_client

        mmlw_status = await mmlw_client.health_check()
        api_status["mmlw"] = {
            "status": "healthy" if mmlw_status.get("status") == "ok" else "unhealthy",
            "details": mmlw_status,
            "last_check": datetime.now().isoformat(),
        }
    except ImportError:
        api_status["mmlw"] = {
            "status": "unavailable",
            "error": "MMLW client not available",
            "last_check": datetime.now().isoformat(),
        }
    except Exception as e:
        api_status["mmlw"] = {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.now().isoformat(),
        }

    return {
        "status": (
            "healthy"
            if all(status["status"] == "healthy" for status in api_status.values())
            else "unhealthy"
        ),
        "apis": api_status,
    }


@router.get("/health", tags=["Health"])
async def health_check() -> Response:
    """✅ REQUIRED: Health checks for all services"""
    start_time = time.time()

    # Perform all health checks
    db_health = await check_database_health()
    agents_health = await check_agents_health()
    external_apis_health = await check_external_apis_health()

    checks = {
        "database": db_health,
        "agents": agents_health,
        "external_apis": external_apis_health,
    }

    # Determine overall health
    all_healthy = (
        db_health.get("status") == "healthy"
        and agents_health.get("status") == "healthy"
        and external_apis_health.get("status") == "healthy"
    )

    status_code = 200 if all_healthy else 503
    response_time = time.time() - start_time

    response_data = {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "response_time": round(response_time, 3),
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }

    return JSONResponse(content=response_data, status_code=status_code)


@router.get("/ready", tags=["Health"])
async def ready_check() -> Response:
    """Readiness check for services like database."""
    db_health = await check_database_health()

    if db_health.get("status") != "healthy":
        logger.warning("readiness.check.failed", database_status=db_health)
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "services": {"database": db_health},
                "timestamp": datetime.now().isoformat(),
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "ready",
            "services": {"database": db_health},
            "timestamp": datetime.now().isoformat(),
        },
    )


@router.get("/metrics", tags=["Monitoring"])
async def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint."""
    # This would typically be handled by a Prometheus client library middleware
    # returning the metrics in the correct format.
    # This is a placeholder.
    return JSONResponse(
        content={
            "message": "Prometheus metrics would be exposed here.",
            "timestamp": datetime.now().isoformat(),
        }
    )


@router.get("/status", tags=["Monitoring"])
async def detailed_status() -> Response:
    """Get detailed status of the application components."""
    # Perform comprehensive health checks
    db_health = await check_database_health()
    agents_health = await check_agents_health()
    external_apis_health = await check_external_apis_health()

    # Get system metrics (placeholder)
    import psutil

    memory_usage = psutil.virtual_memory().used
    cpu_usage = psutil.cpu_percent(interval=1)

    return JSONResponse(
        content={
            "service": "FoodSave AI Backend",
            "version": "1.0.0",
            "status": (
                "healthy"
                if all(
                    [
                        db_health.get("status") == "healthy",
                        agents_health.get("status") == "healthy",
                        external_apis_health.get("status") == "healthy",
                    ]
                )
                else "unhealthy"
            ),
            "components": {
                "database": db_health,
                "agents": agents_health,
                "external_apis": external_apis_health,
                "cache": "connected",  # Placeholder
                "orchestrator_pool": "active",  # Placeholder
            },
            "performance": {
                "memory_usage": memory_usage,
                "cpu_usage": cpu_usage,
                "active_connections": 5,  # Placeholder
            },
            "timestamp": datetime.now().isoformat(),
        }
    )


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
