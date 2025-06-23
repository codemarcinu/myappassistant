"""
Backup Manager for FoodSave AI

Implements comprehensive backup strategy following the 3-2-1 rule:
- 3 copies of data
- 2 different storage types
- 1 off-site backup

Based on industry best practices from SimpleBackups and ConnectWise.
"""

import hashlib
import json
import logging
import os
import shutil
import sys
import tarfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, TypedDict

import aiofiles
from sqlalchemy import text

from backend.config import settings
from backend.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class BackupComponentResult(TypedDict, total=False):
    status: str
    path: Optional[str]
    size: int
    checksum: Optional[str]
    error: str


class BackupVerificationResult(TypedDict, total=False):
    database: str
    files: str
    configuration: str
    vector_store: str
    overall: str
    error: str


class BackupResults(TypedDict, total=False):
    backup_name: str
    timestamp: str
    components: Dict[str, BackupComponentResult]
    verification: BackupVerificationResult
    storage_locations: List[Dict[str, str]]
    total_size: int
    manifest: Dict[str, Any]
    error: str


class BackupManager:
    """
    Comprehensive backup manager implementing industry best practices
    """

    def __init__(self) -> None:
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
    ) -> BackupResults:
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

        backup_results: BackupResults = {
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
                comp.get("size", 0)
                for comp in backup_results["components"].values()
                if comp
            )
            backup_results["total_size"] = total_size

            logger.info(f"Full backup completed successfully: {backup_name}")
            logger.info(f"Total backup size: {total_size / (1024*1024):.2f} MB")

            return backup_results

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            backup_results["error"] = str(e)
            return backup_results

    async def _backup_database(self, backup_name: str) -> BackupComponentResult:
        """Create database backup with integrity checks"""
        logger.info("Creating database backup...")

        backup_file = self.db_backup_dir / f"{backup_name}_database.sql"
        backup_zip = self.db_backup_dir / f"{backup_name}_database.zip"

        try:
            # Create SQL dump
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                tables = [row[0] for row in result.fetchall()]

                backup_sql_parts = ["-- FoodSave AI Database Backup"]
                for table in tables:
                    if table == "sqlite_sequence":
                        continue
                    rows_result = await db.execute(text(f"SELECT * FROM {table}"))
                    rows = rows_result.fetchall()
                    if rows:
                        for row in rows:
                            backup_sql_parts.append(
                                f"INSERT INTO {table} VALUES({', '.join(map(repr, row))});"
                            )

            async with aiofiles.open(backup_file, "w", encoding="utf-8") as f:
                await f.write("\n".join(backup_sql_parts))

            with zipfile.ZipFile(backup_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_file, backup_file.name)

            checksum = await self._calculate_file_checksum(backup_zip)
            backup_file.unlink()
            size = backup_zip.stat().st_size

            logger.info(f"Database backup created: {backup_zip} ({size / 1024:.2f} KB)")
            return {"status": "success", "path": str(backup_zip), "size": size, "checksum": checksum}

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _backup_files(self, backup_name: str) -> BackupComponentResult:
        """Backup user-uploaded files using tar for efficient compression."""
        logger.info("Creating files backup...")
        backup_file = self.files_backup_dir / f"{backup_name}_files.tar.gz"
        important_dirs = ["uploads", "documents"]

        try:
            with tarfile.open(backup_file, "w:gz") as tar:
                for dir_name in important_dirs:
                    path = Path(dir_name)
                    if path.exists():
                        tar.add(path, arcname=path.name)

            size = backup_file.stat().st_size
            checksum = await self._calculate_file_checksum(backup_file)
            logger.info(f"Files backup created: {backup_file} ({size / 1024:.2f} KB)")
            return {"status": "success", "path": str(backup_file), "size": size, "checksum": checksum}

        except Exception as e:
            logger.error(f"File backup failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _backup_configuration(self, backup_name: str) -> BackupComponentResult:
        """Backup critical configuration files."""
        logger.info("Creating configuration backup...")
        backup_file = self.config_backup_dir / f"{backup_name}_config.json"
        
        try:
            # Manually select non-sensitive settings to back up
            safe_config_data = {
                "APP_NAME": settings.APP_NAME,
                "ENVIRONMENT": settings.ENVIRONMENT,
                "LOG_LEVEL": settings.LOG_LEVEL,
                # Add other non-sensitive keys here
            }

            async with aiofiles.open(backup_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(safe_config_data, indent=2))
            
            size = backup_file.stat().st_size
            checksum = await self._calculate_file_checksum(backup_file)
            logger.info(f"Configuration backup created: {backup_file} ({size / 1024:.2f} KB)")
            return {"status": "success", "path": str(backup_file), "size": size, "checksum": checksum}
        
        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _backup_vector_store(self, backup_name: str) -> BackupComponentResult:
        """Backup the vector store data."""
        logger.info("Creating vector store backup...")
        backup_file = self.vector_backup_dir / f"{backup_name}_vector_store.json"
        
        try:
            # Assuming vector store has an export method
            if hasattr(settings, "VECTOR_STORE_PATH") and os.path.exists(settings.VECTOR_STORE_PATH):
                # This is a placeholder for actual vector store backup logic
                shutil.copytree(settings.VECTOR_STORE_PATH, str(backup_file.with_suffix('')))
                with tarfile.open(str(backup_file.with_suffix('.tar.gz')), "w:gz") as tar:
                    tar.add(str(backup_file.with_suffix('')), arcname=backup_name)
                
                final_backup_file = backup_file.with_suffix('.tar.gz')
                size = final_backup_file.stat().st_size
                checksum = await self._calculate_file_checksum(final_backup_file)
                logger.info(f"Vector store backup created: {final_backup_file} ({size / 1024:.2f} KB)")
                return {"status": "success", "path": str(final_backup_file), "size": size, "checksum": checksum}
            else:
                logger.info("Vector store is empty or not configured, skipping backup")
                return {"status": "skipped", "size": 0}

        except Exception as e:
            logger.error(f"Vector store backup failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _create_backup_manifest(
        self, backup_name: str, backup_results: BackupResults
    ) -> Dict[str, Any]:
        """Create a manifest file for the backup"""
        manifest_path = self.backup_dir / f"{backup_name}_manifest.json"
        manifest_data = {
            "backup_name": backup_name,
            "timestamp": backup_results["timestamp"],
            "version": "1.0",
            "components": backup_results["components"],
        }
        async with aiofiles.open(manifest_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(manifest_data, indent=2))
        return manifest_data

    async def _apply_321_rule(self, backup_name: str) -> List[Dict[str, str]]:
        """Apply 3-2-1 backup rule (local, external, cloud)"""
        storage_locations = [{"type": "local", "location": str(self.backup_dir)}]
        
        external_drive = await self._find_external_drive()
        if external_drive:
            await self._copy_to_external_drive(backup_name, external_drive)
            storage_locations.append({"type": "external_drive", "location": external_drive})

        if settings.CLOUD_BACKUP_ENABLED:
            cloud_result = await self._upload_to_cloud(backup_name)
            if cloud_result.get("success"):
                storage_locations.append({"type": "cloud", "location": cloud_result.get("url", "")})

        logger.info(f"3-2-1 rule applied: {len(storage_locations)} storage locations")
        return storage_locations

    async def _verify_backup_integrity(self, backup_name: str) -> BackupVerificationResult:
        """Verify backup integrity using checksums from the manifest."""
        logger.info(f"Verifying integrity of backup: {backup_name}")
        verification_results: BackupVerificationResult = {"overall": "passed"}

        manifest_path = self.backup_dir / f"{backup_name}_manifest.json"
        if not manifest_path.exists():
            logger.error(f"Manifest file not found for backup {backup_name}")
            verification_results["overall"] = "failed"
            verification_results["error"] = "Manifest not found"
            return verification_results

        try:
            async with aiofiles.open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.loads(await f.read())

            component_results: Dict[str, str] = {}
            for component_name, component_data in manifest.get("components", {}).items():
                if component_data.get("status") == "success" and component_data.get("path"):
                    file_path = Path(component_data["path"])
                    if file_path.exists():
                        stored_checksum = component_data.get("checksum")
                        current_checksum = await self._calculate_file_checksum(file_path)

                        if current_checksum == stored_checksum:
                            component_results[component_name] = "verified"
                        else:
                            component_results[component_name] = "failed"
                            verification_results["overall"] = "failed"
                            logger.warning(
                                f"Checksum mismatch for {component_name} in backup {backup_name}"
                            )
                    else:
                        component_results[component_name] = "failed"
                        verification_results["overall"] = "failed"
                        logger.warning(f"Backup file not found for {component_name}: {file_path}")
            
            verification_results.update(component_results) # type: ignore

            if verification_results["overall"] == "passed":
                 logger.info(f"Backup integrity verification passed for {backup_name}")
            else:
                 logger.warning(f"Backup integrity verification failed for {backup_name}")

        except Exception as e:
            logger.error(f"Error during backup verification for {backup_name}: {e}")
            verification_results["overall"] = "failed"
            verification_results["error"] = str(e)

        return verification_results

    async def _cleanup_old_backups(self) -> None:
        """Clean up old backups based on retention policy"""
        logger.info("Cleaning up old backups...")
        now = datetime.now()
        retention_periods = {
            "daily": timedelta(days=self.daily_retention_days),
            "weekly": timedelta(weeks=self.weekly_retention_weeks),
            "monthly": timedelta(days=self.monthly_retention_months * 30),
        }
        # This logic needs to be more sophisticated to properly implement daily/weekly/monthly
        # For now, we just delete anything older than the longest retention.
        cutoff = now - retention_periods["monthly"]
        deleted_count = await self._delete_backups_older_than(cutoff, "monthly")
        logger.info(f"Cleanup completed: {deleted_count} old backups deleted")

    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        async with aiofiles.open(file_path, "rb") as f:
            while chunk := await f.read(8192):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    async def _find_external_drive(self) -> Optional[str]:
        """Find external drive for backup (simplified)."""
        if sys.platform == "win32":
            import wmi
            c = wmi.WMI()
            for drive in c.Win32_LogicalDisk():
                if drive.DriveType == 2: # Removable drive
                    return drive.DeviceID + "\\"
        else: # Linux/macOS
            mount_points = ["/media", "/mnt", "/Volumes"]
            for mount in mount_points:
                if os.path.exists(mount):
                    for item in os.listdir(mount):
                        # Simple heuristic, not guaranteed to be external
                        return os.path.join(mount, item)
        return None

    async def _copy_to_external_drive(self, backup_name: str, external_drive: str) -> None:
        """Copy backup to external drive"""
        try:
            dest_dir = Path(external_drive) / "FoodSaveBackups"
            dest_dir.mkdir(exist_ok=True)
            for file in self.backup_dir.glob(f"{backup_name}*"):
                shutil.copy(file, dest_dir / file.name)
            logger.info(f"Backup copied to external drive: {dest_dir}")
        except Exception as e:
            logger.error(f"Failed to copy to external drive: {e}")

    async def _upload_to_cloud(self, backup_name: str) -> Dict[str, Any]:
        """Upload backup to cloud storage (placeholder)."""
        logger.info("Cloud backup upload not implemented yet")
        return {"success": False, "error": "Cloud backup not configured"}

    async def _delete_backups_older_than(
        self, cutoff_date: datetime, backup_type: str
    ) -> int:
        """Delete backups older than specified date."""
        deleted_count = 0
        for item in self.backup_dir.glob(f"*{backup_type}*"):
            file_time = datetime.fromtimestamp(item.stat().st_mtime)
            if file_time < cutoff_date:
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                    deleted_count += 1
                    logger.debug(f"Deleted old backup: {item}")
                except Exception as e:
                    logger.error(f"Failed to delete old backup {item}: {e}")
        return deleted_count

    async def restore_backup(
        self, backup_name: str, components: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Restore system from a specific backup"""
        logger.info(f"Starting restore from backup: {backup_name}")
        manifest_path = self.backup_dir / f"{backup_name}_manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

        async with aiofiles.open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.loads(await f.read())

        results: Dict[str, Any] = {"status": "pending", "details": {}}
        components_to_restore = components or list(manifest["components"].keys())

        for component in components_to_restore:
            if component in manifest["components"]:
                component_data = manifest["components"][component]
                try:
                    restore_result = await self._restore_component(
                        component, component_data, backup_name
                    )
                    results["details"][component] = restore_result
                except Exception as e:
                    results["details"][component] = {"status": "failed", "error": str(e)}

        all_successful = all(
            res["status"] == "success" for res in results["details"].values()
        )
        results["status"] = "success" if all_successful else "partial_failure"
        logger.info(f"Restore finished with status: {results['status']}")
        return results

    async def _restore_component(
        self, component: str, component_data: Dict[str, Any], backup_name: str
    ) -> Dict[str, Any]:
        """Restore a single component."""
        restore_map = {
            "database": self._restore_database,
            "files": self._restore_files,
            "configuration": self._restore_configuration,
            "vector_store": self._restore_vector_store,
        }
        if component in restore_map:
            return await restore_map[component](component_data, backup_name)
        return {"status": "skipped", "error": f"Unknown component: {component}"}

    async def _restore_database(
        self, component_data: Dict[str, Any], backup_name: str
    ) -> Dict[str, Any]:
        """Restore database from backup."""
        logger.info("Restoring database...")
        backup_path = Path(component_data["path"])
        if not backup_path.exists():
            return {"status": "failed", "error": "Backup file not found"}

        # Simplified restore: drop tables and execute script
        try:
            async with AsyncSessionLocal() as session:
                async with aiofiles.open(backup_path, 'r', encoding='utf-8') as f:
                    sql_script = await f.read()
                
                # This is not ideal for async, but a pragmatic choice for sqlite
                # For a production DB like Postgres, would use pg_restore
                await session.execute(text("PRAGMA writable_schema = 1;"))
                await session.execute(text("DELETE FROM sqlite_master WHERE type IN ('table', 'index', 'trigger');"))
                await session.execute(text("PRAGMA writable_schema = 0;"))
                await session.execute(text("VACUUM;"))
                
                # Cannot run executescript in async, so we split and run
                for statement in sql_script.split(';'):
                    if statement.strip():
                        await session.execute(text(statement))
                
                await session.commit()
            logger.info("Database restored successfully")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _restore_files(
        self, component_data: Dict[str, Any], backup_name: str
    ) -> Dict[str, Any]:
        """Restore files from backup."""
        logger.info("Restoring files...")
        backup_path = Path(component_data["path"])
        if not backup_path.exists():
            return {"status": "failed", "error": "Backup file not found"}
        
        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=".")
            logger.info("Files restored successfully.")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"File restore failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _restore_configuration(
        self, component_data: Dict[str, Any], backup_name: str
    ) -> Dict[str, Any]:
        """Restore configuration from backup."""
        logger.info("Restoring configuration...")
        # For security, this should be a carefully managed process.
        # We don't want to overwrite sensitive live configs with old ones.
        # This implementation simply logs what would be restored.
        backup_path = Path(component_data["path"])
        if not backup_path.exists():
            return {"status": "failed", "error": "Backup file not found"}
        
        async with aiofiles.open(backup_path, "r", encoding="utf-8") as f:
            backed_up_config = json.loads(await f.read())
        
        logger.info(f"Configuration to restore: {backed_up_config}")
        # In a real scenario, you'd apply these settings to your config management system.
        logger.warning("Configuration restore is a manual process for safety.")
        return {"status": "success", "info": "Manual review required"}

    async def _restore_vector_store(
        self, component_data: Dict[str, Any], backup_name: str
    ) -> Dict[str, Any]:
        """Restore vector store from backup."""
        logger.info("Restoring vector store...")
        backup_path = Path(component_data["path"])
        if not backup_path.exists():
            return {"status": "failed", "error": "Backup file not found"}

        try:
            if hasattr(settings, "VECTOR_STORE_PATH"):
                restore_path = Path(settings.VECTOR_STORE_PATH)
                if restore_path.exists():
                    shutil.rmtree(restore_path)
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(path=restore_path.parent)
                logger.info("Vector store restored successfully.")
                return {"status": "success"}
            return {"status": "skipped", "error": "Vector store path not configured"}
        except Exception as e:
            logger.error(f"Vector store restore failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        backups: List[Dict[str, Any]] = []
        for manifest_file in self.backup_dir.glob("*_manifest.json"):
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                    total_size = sum(c.get('size', 0) for c in manifest_data.get('components', {}).values())
                    backups.append({
                        "name": manifest_data["backup_name"],
                        "timestamp": manifest_data["timestamp"],
                        "size_mb": total_size / (1024*1024),
                        "components": list(manifest_data.get('components', {}).keys()),
                    })
            except Exception as e:
                logger.error(f"Could not read manifest {manifest_file}: {e}")
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)

    async def get_backup_stats(self) -> Dict[str, Any]:
        """Get statistics about backups."""
        backups = await self.list_backups()
        total_size = sum(b['size_mb'] for b in backups) * 1024 * 1024
        
        return {
            "total_backups": len(backups),
            "total_size_mb": total_size / (1024 * 1024),
            "last_backup_timestamp": backups[0]["timestamp"] if backups else None,
        }