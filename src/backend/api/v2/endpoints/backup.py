"""
Backup Management API Endpoints

This module provides API endpoints for managing the backup system:
- Create backups
- List backups
- Restore backups
- Backup statistics
- Backup verification
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v2.exceptions import (APIErrorCodes, BadRequestError,
                                       InternalServerError, NotFoundError,
                                       UnprocessableEntityError)
from backend.core.backup_manager import backup_manager
from backend.infrastructure.database.database import get_db

router = APIRouter(prefix="/backup", tags=["Backup Management"])
logger = logging.getLogger(__name__)


@router.post("/create", response_model=None)
async def create_backup(
    backup_name: Optional[str] = Query(None, description="Custom backup name"),
    verify: bool = Query(True, description="Verify backup integrity after creation"),
):
    """
    Create a full system backup following the 3-2-1 rule
    """
    try:
        # Set verification flag
        backup_manager.verify_backups = verify

        # Create backup
        result = await backup_manager.create_full_backup(backup_name)

        if "error" in result:
            raise UnprocessableEntityError(
                message="Backup creation failed", details={"error": result["error"]}
            )

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Backup created successfully",
                "data": result,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to create backup",
                "details": {"error": str(e)},
            },
        )


@router.get("/list", response_model=None)
async def list_backups() -> None:
    """
    List all available backups
    """
    try:
        backups = await backup_manager.list_backups()

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Backups retrieved successfully",
                "data": {"backups": backups, "total_count": len(backups)},
            },
        )

    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to list backups",
                "details": {"error": str(e)},
            },
        )


@router.post("/restore/{backup_name}", response_model=None)
async def restore_backup(
    backup_name: str,
    components: Optional[str] = Query(
        None, description="Comma-separated list of components to restore"
    ),
):
    """
    Restore system from a specific backup
    """
    try:
        # Parse components
        components_list = None
        if components:
            components_list = [comp.strip() for comp in components.split(",")]

        # Validate backup exists
        backups = await backup_manager.list_backups()
        backup_exists = any(backup["name"] == backup_name for backup in backups)

        if not backup_exists:
            raise BadRequestError(
                message="Backup not found", details={"backup_name": backup_name}
            )

        # Restore backup
        result = await backup_manager.restore_backup(backup_name, components_list)

        if result["status"] == "failed":
            raise UnprocessableEntityError(
                message="Backup restoration failed",
                details={"errors": result["errors"]},
            )

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Backup restored successfully",
                "data": result,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to restore backup",
                "details": {"error": str(e)},
            },
        )


@router.get("/stats", response_model=None)
async def get_backup_stats() -> None:
    """
    Get backup system statistics
    """
    try:
        stats = await backup_manager.get_backup_stats()

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Backup statistics retrieved successfully",
                "data": stats,
            },
        )

    except Exception as e:
        logger.error(f"Error getting backup stats: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get backup statistics",
                "details": {"error": str(e)},
            },
        )


@router.post("/verify/{backup_name}", response_model=None)
async def verify_backup(backup_name: str) -> None:
    """
    Verify backup integrity
    """
    try:
        # Validate backup exists
        backups = await backup_manager.list_backups()
        backup_exists = any(backup["name"] == backup_name for backup in backups)

        if not backup_exists:
            raise BadRequestError(
                message="Backup not found", details={"backup_name": backup_name}
            )

        # Verify backup
        verification_result = await backup_manager._verify_backup_integrity(backup_name)

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Backup verification completed",
                "data": verification_result,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying backup: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to verify backup",
                "details": {"error": str(e)},
            },
        )


@router.delete("/cleanup", response_model=None)
async def cleanup_old_backups() -> None:
    """
    Clean up old backups based on retention policy
    """
    try:
        await backup_manager._cleanup_old_backups()

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Old backups cleaned up successfully",
            },
        )

    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to cleanup old backups",
                "details": {"error": str(e)},
            },
        )


@router.get("/health", response_model=None)
async def backup_health_check() -> None:
    """
    Health check for backup system
    """
    try:
        # Check if backup directory exists and is writable
        backup_dir = backup_manager.backup_dir

        if not backup_dir.exists():
            return JSONResponse(
                status_code=503,
                content={
                    "status_code": 503,
                    "error_code": "BACKUP_SYSTEM_ERROR",
                    "message": "Backup directory not found",
                    "details": {"backup_dir": str(backup_dir)},
                },
            )

        # Check if we can write to backup directory
        test_file = backup_dir / "health_check.tmp"
        try:
            test_file.write_text("health_check")
            test_file.unlink()
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={
                    "status_code": 503,
                    "error_code": "BACKUP_SYSTEM_ERROR",
                    "message": "Backup directory not writable",
                    "details": {"error": str(e)},
                },
            )

        # Get basic stats
        stats = await backup_manager.get_backup_stats()

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Backup system is healthy",
                "data": {
                    "status": "healthy",
                    "backup_directory": str(backup_dir),
                    "total_backups": stats["total_backups"],
                    "total_size_mb": stats["total_size_mb"],
                },
            },
        )

    except Exception as e:
        logger.error(f"Backup health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status_code": 503,
                "error_code": "BACKUP_SYSTEM_ERROR",
                "message": "Backup system health check failed",
                "details": {"error": str(e)},
            },
        )
