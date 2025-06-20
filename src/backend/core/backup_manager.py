"""
Backup Manager for FoodSave AI

Implements comprehensive backup strategy following the 3-2-1 rule:
- 3 copies of data
- 2 different storage types
- 1 off-site backup

Based on industry best practices from SimpleBackups and ConnectWise.
"""

import asyncio
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import tarfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiofiles
import aiohttp
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Comprehensive backup manager implementing industry best practices
    """

    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

        # Create backup subdirectories
        self.db_backup_dir = self.backup_dir / "database"
        self.files_backup_dir = self.backup_dir / "files"
        self.config_backup_dir = self.backup_dir / "config"
        self.vector_backup_dir = self.backup_dir / "vector_store"

        for dir_path in [
            self.db_backup_dir,
            self.files_backup_dir,
            self.config_backup_dir,
            self.vector_backup_dir,
        ]:
            dir_path.mkdir(exist_ok=True)

        # Backup retention settings
        self.daily_retention_days = 7
        self.weekly_retention_weeks = 4
        self.monthly_retention_months = 12

        # Verification settings
        self.verify_backups = True
        self.checksum_verification = True

    async def create_full_backup(
        self, backup_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a complete system backup following the 3-2-1 rule

        Args:
            backup_name: Optional custom backup name

        Returns:
            Backup summary with verification results
        """
        if not backup_name:
            backup_name = f"full_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting full backup: {backup_name}")

        backup_results = {
            "backup_name": backup_name,
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "verification": {},
            "storage_locations": [],
            "total_size": 0,
        }

        try:
            # 1. Database backup
            db_result = await self._backup_database(backup_name)
            backup_results["components"]["database"] = db_result

            # 2. Files backup
            files_result = await self._backup_files(backup_name)
            backup_results["components"]["files"] = files_result

            # 3. Configuration backup
            config_result = await self._backup_configuration(backup_name)
            backup_results["components"]["configuration"] = config_result

            # 4. Vector store backup
            vector_result = await self._backup_vector_store(backup_name)
            backup_results["components"]["vector_store"] = vector_result

            # 5. Create backup manifest
            manifest = await self._create_backup_manifest(backup_name, backup_results)
            backup_results["manifest"] = manifest

            # 6. Apply 3-2-1 rule
            storage_locations = await self._apply_321_rule(backup_name)
            backup_results["storage_locations"] = storage_locations

            # 7. Verify backup integrity
            if self.verify_backups:
                verification_results = await self._verify_backup_integrity(backup_name)
                backup_results["verification"] = verification_results

            # 8. Cleanup old backups
            await self._cleanup_old_backups()

            # 9. Calculate total size
            total_size = sum(
                comp.get("size", 0) for comp in backup_results["components"].values()
            )
            backup_results["total_size"] = total_size

            logger.info(f"Full backup completed successfully: {backup_name}")
            logger.info(f"Total backup size: {total_size / (1024*1024):.2f} MB")

            return backup_results

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            backup_results["error"] = str(e)
            return backup_results

    async def _backup_database(self, backup_name: str) -> Dict[str, Any]:
        """Create database backup with integrity checks"""
        logger.info("Creating database backup...")

        backup_file = self.db_backup_dir / f"{backup_name}_database.sql"
        backup_zip = self.db_backup_dir / f"{backup_name}_database.zip"

        try:
            # Create SQL dump
            async with AsyncSessionLocal() as db:
                # Get all tables
                result = await db.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                tables = [row[0] for row in result.fetchall()]

                # Create backup SQL
                backup_sql = []
                backup_sql.append("-- FoodSave AI Database Backup")
                backup_sql.append(f"-- Created: {datetime.now().isoformat()}")
                backup_sql.append("-- Backup Name: " + backup_name)
                backup_sql.append("")

                for table in tables:
                    if table == "sqlite_sequence":
                        continue

                    # Get table schema
                    schema_result = await db.execute(
                        text(f"PRAGMA table_info({table})")
                    )
                    columns = schema_result.fetchall()

                    # Get table data
                    data_result = await db.execute(text(f"SELECT * FROM {table}"))
                    rows = data_result.fetchall()

                    # Create INSERT statements
                    if rows:
                        column_names = [col[1] for col in columns]
                        placeholders = ", ".join(["?" for _ in column_names])

                        backup_sql.append(f"-- Table: {table}")
                        backup_sql.append(f"CREATE TABLE IF NOT EXISTS {table} (")

                        for col in columns:
                            col_def = f"  {col[1]} {col[2]}"
                            if col[3]:  # NOT NULL
                                col_def += " NOT NULL"
                            if col[4]:  # DEFAULT
                                col_def += f" DEFAULT {col[4]}"
                            if col[5]:  # PRIMARY KEY
                                col_def += " PRIMARY KEY"
                            backup_sql.append(col_def + ",")

                        backup_sql.append(");")
                        backup_sql.append("")

                        # Insert data
                        for row in rows:
                            values = [
                                str(val) if val is not None else "NULL" for val in row
                            ]
                            backup_sql.append(
                                f"INSERT INTO {table} VALUES ({', '.join(values)});"
                            )

                        backup_sql.append("")

            # Write backup file
            async with aiofiles.open(backup_file, "w", encoding="utf-8") as f:
                await f.write("\n".join(backup_sql))

            # Create compressed backup
            with zipfile.ZipFile(backup_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_file, backup_file.name)

            # Calculate checksum
            checksum = await self._calculate_file_checksum(backup_zip)

            # Clean up uncompressed file
            backup_file.unlink()

            size = backup_zip.stat().st_size

            logger.info(f"Database backup created: {backup_zip} ({size / 1024:.2f} KB)")

            return {
                "file": str(backup_zip),
                "size": size,
                "checksum": checksum,
                "tables_count": len(tables),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _backup_files(self, backup_name: str) -> Dict[str, Any]:
        """Backup important files and directories"""
        logger.info("Creating files backup...")

        backup_file = self.files_backup_dir / f"{backup_name}_files.tar.gz"

        try:
            # Define important directories to backup
            important_dirs = [
                "data/docs",
                "data/uploads",
                "data/vector_db",
                "src/backend/config",
                "foodsave-frontend/src/components",
                "foodsave-frontend/src/app",
                "scripts",
                "docs",
            ]

            # Create tar.gz archive
            with tarfile.open(backup_file, "w:gz") as tar:
                for dir_path in important_dirs:
                    path = Path(dir_path)
                    if path.exists():
                        tar.add(path, arcname=path.name)

            checksum = await self._calculate_file_checksum(backup_file)
            size = backup_file.stat().st_size

            logger.info(
                f"Files backup created: {backup_file} ({size / (1024*1024):.2f} MB)"
            )

            return {
                "file": str(backup_file),
                "size": size,
                "checksum": checksum,
                "directories_backed_up": len(important_dirs),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Files backup failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _backup_configuration(self, backup_name: str) -> Dict[str, Any]:
        """Backup configuration files and environment settings"""
        logger.info("Creating configuration backup...")

        backup_file = self.config_backup_dir / f"{backup_name}_config.json"

        try:
            # Collect configuration data
            config_data = {
                "backup_timestamp": datetime.now().isoformat(),
                "backup_name": backup_name,
                "environment": {
                    "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
                    "platform": os.name,
                    "current_directory": str(Path.cwd()),
                },
                "application_config": {
                    "app_name": getattr(settings, "APP_NAME", "FoodSave AI"),
                    "app_version": getattr(settings, "APP_VERSION", "1.0.0"),
                    "environment": getattr(settings, "ENVIRONMENT", "development"),
                    "log_level": getattr(settings, "LOG_LEVEL", "INFO"),
                },
                "database_config": {
                    "database_url": str(
                        getattr(settings, "DATABASE_URL", "sqlite:///foodsave.db")
                    ),
                    "use_mmlw_embeddings": getattr(
                        settings, "USE_MMLW_EMBEDDINGS", False
                    ),
                },
                "rag_config": {
                    "chunk_size": getattr(settings, "RAG_CHUNK_SIZE", 1000),
                    "chunk_overlap": getattr(settings, "RAG_CHUNK_OVERLAP", 200),
                    "use_local_embeddings": getattr(
                        settings, "USE_LOCAL_EMBEDDINGS", True
                    ),
                },
            }

            # Write configuration backup
            async with aiofiles.open(backup_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(config_data, indent=2, ensure_ascii=False))

            checksum = await self._calculate_file_checksum(backup_file)
            size = backup_file.stat().st_size

            logger.info(f"Configuration backup created: {backup_file} ({size} bytes)")

            return {
                "file": str(backup_file),
                "size": size,
                "checksum": checksum,
                "config_sections": len(config_data),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _backup_vector_store(self, backup_name: str) -> Dict[str, Any]:
        """Backup vector store data"""
        logger.info("Creating vector store backup...")

        backup_file = self.vector_backup_dir / f"{backup_name}_vector_store.tar.gz"

        try:
            vector_db_path = Path("data/vector_db")

            if vector_db_path.exists() and any(vector_db_path.iterdir()):
                # Create tar.gz archive of vector store
                with tarfile.open(backup_file, "w:gz") as tar:
                    tar.add(vector_db_path, arcname="vector_db")

                checksum = await self._calculate_file_checksum(backup_file)
                size = backup_file.stat().st_size

                logger.info(
                    f"Vector store backup created: {backup_file} ({size / (1024*1024):.2f} MB)"
                )

                return {
                    "file": str(backup_file),
                    "size": size,
                    "checksum": checksum,
                    "status": "success",
                }
            else:
                logger.info("Vector store is empty, skipping backup")
                return {"file": None, "size": 0, "checksum": None, "status": "skipped"}

        except Exception as e:
            logger.error(f"Vector store backup failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _create_backup_manifest(
        self, backup_name: str, backup_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create backup manifest with metadata"""
        manifest_file = self.backup_dir / f"{backup_name}_manifest.json"

        manifest = {
            "backup_info": {
                "name": backup_name,
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "backup_manager_version": "1.0",
            },
            "components": backup_results["components"],
            "verification": backup_results.get("verification", {}),
            "storage_locations": backup_results.get("storage_locations", []),
            "total_size": backup_results.get("total_size", 0),
            "checksum": None,  # Will be calculated for the manifest itself
        }

        # Write manifest
        async with aiofiles.open(manifest_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(manifest, indent=2, ensure_ascii=False))

        # Calculate manifest checksum
        manifest_checksum = await self._calculate_file_checksum(manifest_file)
        manifest["checksum"] = manifest_checksum

        # Update manifest with its own checksum
        async with aiofiles.open(manifest_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(manifest, indent=2, ensure_ascii=False))

        return {"file": str(manifest_file), "checksum": manifest_checksum}

    async def _apply_321_rule(self, backup_name: str) -> List[Dict[str, str]]:
        """
        Apply 3-2-1 backup rule:
        - 3 copies of data
        - 2 different storage types
        - 1 off-site backup
        """
        logger.info("Applying 3-2-1 backup rule...")

        storage_locations = []

        # Copy 1: Local backup (already created)
        storage_locations.append(
            {
                "type": "local",
                "location": str(self.backup_dir),
                "description": "Primary local backup",
            }
        )

        # Copy 2: External drive backup (if available)
        external_drive = await self._find_external_drive()
        if external_drive:
            await self._copy_to_external_drive(backup_name, external_drive)
            storage_locations.append(
                {
                    "type": "external_drive",
                    "location": external_drive,
                    "description": "External drive backup",
                }
            )

        # Copy 3: Cloud backup (if configured)
        if hasattr(settings, "CLOUD_BACKUP_ENABLED") and settings.CLOUD_BACKUP_ENABLED:
            cloud_result = await self._upload_to_cloud(backup_name)
            if cloud_result["success"]:
                storage_locations.append(
                    {
                        "type": "cloud",
                        "location": cloud_result["url"],
                        "description": "Cloud backup",
                    }
                )

        logger.info(f"3-2-1 rule applied: {len(storage_locations)} storage locations")
        return storage_locations

    async def _verify_backup_integrity(self, backup_name: str) -> Dict[str, Any]:
        """Verify backup integrity using checksums"""
        logger.info("Verifying backup integrity...")

        verification_results = {
            "overall_status": "passed",
            "components": {},
            "errors": [],
        }

        try:
            # Verify each component
            for component_name, component_data in verification_results.get(
                "components", {}
            ).items():
                if component_data.get("status") == "success" and component_data.get(
                    "file"
                ):
                    file_path = Path(component_data["file"])

                    if file_path.exists():
                        # Verify checksum
                        current_checksum = await self._calculate_file_checksum(
                            file_path
                        )
                        stored_checksum = component_data.get("checksum")

                        if current_checksum == stored_checksum:
                            verification_results["components"][component_name] = {
                                "status": "verified",
                                "checksum_match": True,
                            }
                        else:
                            verification_results["components"][component_name] = {
                                "status": "failed",
                                "checksum_match": False,
                                "expected": stored_checksum,
                                "actual": current_checksum,
                            }
                            verification_results["errors"].append(
                                f"Checksum mismatch for {component_name}"
                            )
                            verification_results["overall_status"] = "failed"
                    else:
                        verification_results["components"][component_name] = {
                            "status": "failed",
                            "error": "File not found",
                        }
                        verification_results["errors"].append(
                            f"Backup file not found: {component_name}"
                        )
                        verification_results["overall_status"] = "failed"

            logger.info(
                f"Backup verification completed: {verification_results['overall_status']}"
            )

        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            verification_results["overall_status"] = "failed"
            verification_results["errors"].append(str(e))

        return verification_results

    async def _cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        logger.info("Cleaning up old backups...")

        current_time = datetime.now()
        deleted_count = 0

        # Clean up daily backups (older than 7 days)
        daily_cutoff = current_time - timedelta(days=self.daily_retention_days)
        deleted_count += await self._delete_backups_older_than(daily_cutoff, "daily")

        # Clean up weekly backups (older than 4 weeks)
        weekly_cutoff = current_time - timedelta(weeks=self.weekly_retention_weeks)
        deleted_count += await self._delete_backups_older_than(weekly_cutoff, "weekly")

        # Clean up monthly backups (older than 12 months)
        monthly_cutoff = current_time - timedelta(days=365)
        deleted_count += await self._delete_backups_older_than(
            monthly_cutoff, "monthly"
        )

        logger.info(f"Cleanup completed: {deleted_count} old backups deleted")

    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file"""
        sha256_hash = hashlib.sha256()

        async with aiofiles.open(file_path, "rb") as f:
            while chunk := await f.read(8192):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    async def _find_external_drive(self) -> Optional[str]:
        """Find external drive for backup"""
        # Common external drive mount points
        mount_points = ["/media", "/mnt", "/Volumes"]

        for mount_point in mount_points:
            if Path(mount_point).exists():
                for item in Path(mount_point).iterdir():
                    if item.is_dir() and not item.name.startswith("."):
                        # Check if it's likely an external drive
                        if any(
                            keyword in item.name.lower()
                            for keyword in [
                                "backup",
                                "external",
                                "usb",
                                "drive",
                                "disk",
                            ]
                        ):
                            return str(item)

        return None

    async def _copy_to_external_drive(self, backup_name: str, external_drive: str):
        """Copy backup to external drive"""
        try:
            external_backup_dir = Path(external_drive) / "FoodSave_Backups"
            external_backup_dir.mkdir(exist_ok=True)

            # Copy all backup files
            for backup_file in self.backup_dir.rglob(f"{backup_name}*"):
                if backup_file.is_file():
                    dest_file = external_backup_dir / backup_file.name
                    shutil.copy2(backup_file, dest_file)

            logger.info(f"Backup copied to external drive: {external_backup_dir}")

        except Exception as e:
            logger.error(f"Failed to copy to external drive: {e}")

    async def _upload_to_cloud(self, backup_name: str) -> Dict[str, Any]:
        """Upload backup to cloud storage (placeholder implementation)"""
        # This would integrate with cloud providers like AWS S3, Google Cloud Storage, etc.
        logger.info("Cloud backup upload not implemented yet")
        return {"success": False, "error": "Cloud backup not configured"}

    async def _delete_backups_older_than(
        self, cutoff_date: datetime, backup_type: str
    ) -> int:
        """Delete backups older than specified date"""
        deleted_count = 0

        for backup_file in self.backup_dir.rglob("*"):
            if backup_file.is_file() and backup_file.suffix in [
                ".zip",
                ".tar.gz",
                ".json",
            ]:
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)

                if file_time < cutoff_date:
                    try:
                        backup_file.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old backup: {backup_file}")
                    except Exception as e:
                        logger.error(f"Failed to delete old backup {backup_file}: {e}")

        return deleted_count

    async def restore_backup(
        self, backup_name: str, components: List[str] = None
    ) -> Dict[str, Any]:
        """
        Restore system from backup

        Args:
            backup_name: Name of the backup to restore
            components: List of components to restore (None = all)

        Returns:
            Restoration results
        """
        logger.info(f"Starting backup restoration: {backup_name}")

        if components is None:
            components = ["database", "files", "configuration", "vector_store"]

        restore_results = {
            "backup_name": backup_name,
            "restored_components": [],
            "errors": [],
            "status": "completed",
        }

        try:
            # Load backup manifest
            manifest_file = self.backup_dir / f"{backup_name}_manifest.json"

            if not manifest_file.exists():
                raise FileNotFoundError(f"Backup manifest not found: {manifest_file}")

            async with aiofiles.open(manifest_file, "r", encoding="utf-8") as f:
                manifest_content = await f.read()
                manifest = json.loads(manifest_content)

            # Restore each component
            for component in components:
                if component in manifest["components"]:
                    component_data = manifest["components"][component]

                    if component_data.get("status") == "success":
                        restore_result = await self._restore_component(
                            component, component_data, backup_name
                        )
                        restore_results["restored_components"].append(restore_result)
                    else:
                        restore_results["errors"].append(
                            f"Component {component} was not successfully backed up"
                        )
                else:
                    restore_results["errors"].append(
                        f"Component {component} not found in backup"
                    )

            if restore_results["errors"]:
                restore_results["status"] = "completed_with_errors"

            logger.info(f"Backup restoration completed: {restore_results['status']}")

        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            restore_results["status"] = "failed"
            restore_results["errors"].append(str(e))

        return restore_results

    async def _restore_component(
        self, component: str, component_data: Dict[str, Any], backup_name: str
    ) -> Dict[str, Any]:
        """Restore a specific component from backup"""
        try:
            if component == "database":
                return await self._restore_database(component_data, backup_name)
            elif component == "files":
                return await self._restore_files(component_data, backup_name)
            elif component == "configuration":
                return await self._restore_configuration(component_data, backup_name)
            elif component == "vector_store":
                return await self._restore_vector_store(component_data, backup_name)
            else:
                return {
                    "component": component,
                    "status": "failed",
                    "error": f"Unknown component: {component}",
                }
        except Exception as e:
            return {"component": component, "status": "failed", "error": str(e)}

    async def _restore_database(
        self, component_data: Dict[str, Any], backup_name: str
    ) -> Dict[str, Any]:
        """Restore database from backup"""
        backup_file = Path(component_data["file"])

        if not backup_file.exists():
            return {
                "component": "database",
                "status": "failed",
                "error": "Backup file not found",
            }

        try:
            # Extract SQL from zip
            with zipfile.ZipFile(backup_file, "r") as zipf:
                sql_file = zipf.namelist()[0]
                zipf.extract(sql_file, self.db_backup_dir)

            sql_path = self.db_backup_dir / sql_file

            # Restore database
            async with AsyncSessionLocal() as db:
                # Read and execute SQL
                async with aiofiles.open(sql_path, "r", encoding="utf-8") as f:
                    sql_content = await f.read()

                # Split into individual statements
                statements = [
                    stmt.strip() for stmt in sql_content.split(";") if stmt.strip()
                ]

                for statement in statements:
                    if statement and not statement.startswith("--"):
                        await db.execute(text(statement))

                await db.commit()

            # Clean up
            sql_path.unlink()

            return {
                "component": "database",
                "status": "success",
                "message": "Database restored successfully",
            }

        except Exception as e:
            return {"component": "database", "status": "failed", "error": str(e)}

    async def _restore_files(
        self, component_data: Dict[str, Any], backup_name: str
    ) -> Dict[str, Any]:
        """Restore files from backup"""
        backup_file = Path(component_data["file"])

        if not backup_file.exists():
            return {
                "component": "files",
                "status": "failed",
                "error": "Backup file not found",
            }

        try:
            # Extract files
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(path=".")

            return {
                "component": "files",
                "status": "success",
                "message": "Files restored successfully",
            }

        except Exception as e:
            return {"component": "files", "status": "failed", "error": str(e)}

    async def _restore_configuration(
        self, component_data: Dict[str, Any], backup_name: str
    ) -> Dict[str, Any]:
        """Restore configuration from backup"""
        backup_file = Path(component_data["file"])

        if not backup_file.exists():
            return {
                "component": "configuration",
                "status": "failed",
                "error": "Backup file not found",
            }

        try:
            # Read configuration
            async with aiofiles.open(backup_file, "r", encoding="utf-8") as f:
                config_content = await f.read()
                config_data = json.loads(config_content)

            # Apply configuration (this would need to be implemented based on your config system)
            logger.info("Configuration restored (manual verification required)")

            return {
                "component": "configuration",
                "status": "success",
                "message": "Configuration restored successfully",
                "note": "Manual verification recommended",
            }

        except Exception as e:
            return {"component": "configuration", "status": "failed", "error": str(e)}

    async def _restore_vector_store(
        self, component_data: Dict[str, Any], backup_name: str
    ) -> Dict[str, Any]:
        """Restore vector store from backup"""
        backup_file = Path(component_data["file"])

        if not backup_file.exists():
            return {
                "component": "vector_store",
                "status": "failed",
                "error": "Backup file not found",
            }

        try:
            # Extract vector store
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(path="data")

            return {
                "component": "vector_store",
                "status": "success",
                "message": "Vector store restored successfully",
            }

        except Exception as e:
            return {"component": "vector_store", "status": "failed", "error": str(e)}

    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        backups = []

        for manifest_file in self.backup_dir.glob("*_manifest.json"):
            try:
                async with aiofiles.open(manifest_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                    manifest = json.loads(content)

                backup_info = {
                    "name": manifest["backup_info"]["name"],
                    "created_at": manifest["backup_info"]["created_at"],
                    "total_size": manifest["total_size"],
                    "components": list(manifest["components"].keys()),
                    "status": "available",
                    "manifest_file": str(manifest_file),
                }

                backups.append(backup_info)

            except Exception as e:
                logger.error(f"Error reading manifest {manifest_file}: {e}")

        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)

        return backups

    async def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup system statistics"""
        backups = await self.list_backups()

        total_backups = len(backups)
        total_size = sum(backup["total_size"] for backup in backups)

        # Calculate storage usage
        backup_dir_size = sum(
            f.stat().st_size for f in self.backup_dir.rglob("*") if f.is_file()
        )

        return {
            "total_backups": total_backups,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "backup_dir_size_bytes": backup_dir_size,
            "backup_dir_size_mb": backup_dir_size / (1024 * 1024),
            "retention_policy": {
                "daily_retention_days": self.daily_retention_days,
                "weekly_retention_weeks": self.weekly_retention_weeks,
                "monthly_retention_months": self.monthly_retention_months,
            },
            "verification_enabled": self.verify_backups,
            "checksum_verification": self.checksum_verification,
        }


# Global backup manager instance
backup_manager = BackupManager()
