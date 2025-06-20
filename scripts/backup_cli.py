#!/usr/bin/env python3
"""
Backup CLI Tool

This command-line utility provides an easy way to manage the backup system:
- Create backups
- List backups
- Restore backups
- Verify backups
- Cleanup old backups

Usage:
  python backup_cli.py create [--name backup_name]
  python backup_cli.py list
  python backup_cli.py restore backup_name [--components database,files]
  python backup_cli.py verify backup_name
  python backup_cli.py cleanup
  python backup_cli.py stats
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.backend.core.backup_manager import backup_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("backup-cli")


async def create_backup(args):
    """Create a new backup"""
    logger.info("Creating backup...")

    try:
        result = await backup_manager.create_full_backup(args.name)

        if result.get("error"):
            logger.error(f"Backup failed: {result['error']}")
            return False

        logger.info(f"Backup created successfully: {result['backup_name']}")
        logger.info(f"Total size: {result['total_size'] / (1024*1024):.2f} MB")
        logger.info(f"Components: {list(result['components'].keys())}")

        if result.get("verification"):
            verification = result["verification"]
            logger.info(f"Verification status: {verification['overall_status']}")

            if verification.get("errors"):
                logger.warning("Verification errors:")
                for error in verification["errors"]:
                    logger.warning(f"  - {error}")

        return True

    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        return False


async def list_backups(args):
    """List all available backups"""
    logger.info("Listing backups...")

    try:
        backups = await backup_manager.list_backups()

        if not backups:
            logger.info("No backups found")
            return True

        logger.info(f"Found {len(backups)} backups:")
        logger.info("-" * 80)

        for backup in backups:
            logger.info(f"Name: {backup['name']}")
            logger.info(f"Created: {backup['created_at']}")
            logger.info(f"Size: {backup['total_size'] / (1024*1024):.2f} MB")
            logger.info(f"Components: {', '.join(backup['components'])}")
            logger.info(f"Status: {backup['status']}")
            logger.info("-" * 80)

        return True

    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        return False


async def restore_backup(args):
    """Restore a backup"""
    backup_name = args.backup_name
    components = args.components.split(",") if args.components else None

    logger.info(f"Restoring backup: {backup_name}")
    if components:
        logger.info(f"Components to restore: {components}")

    try:
        result = await backup_manager.restore_backup(backup_name, components)

        if result["status"] == "failed":
            logger.error("Restore failed:")
            for error in result.get("errors", []):
                logger.error(f"  - {error}")
            return False

        logger.info(f"Restore completed: {result['status']}")
        logger.info(f"Restored components: {result['restored_components']}")

        return True

    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False


async def verify_backup(args):
    """Verify backup integrity"""
    backup_name = args.backup_name

    logger.info(f"Verifying backup: {backup_name}")

    try:
        result = await backup_manager._verify_backup_integrity(backup_name)

        logger.info(f"Verification status: {result['overall_status']}")

        if result.get("errors"):
            logger.error("Verification errors:")
            for error in result["errors"]:
                logger.error(f"  - {error}")

        for component, status in result.get("components", {}).items():
            logger.info(f"  {component}: {status.get('status', 'unknown')}")

        return result["overall_status"] == "passed"

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


async def cleanup_backups(args):
    """Clean up old backups"""
    logger.info("Cleaning up old backups...")

    try:
        await backup_manager._cleanup_old_backups()
        logger.info("Cleanup completed successfully")
        return True

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return False


async def show_stats(args):
    """Show backup system statistics"""
    logger.info("Getting backup statistics...")

    try:
        stats = await backup_manager.get_backup_stats()

        logger.info("Backup System Statistics:")
        logger.info("-" * 40)
        logger.info(f"Total backups: {stats['total_backups']}")
        logger.info(f"Total size: {stats['total_size_mb']:.2f} MB")
        logger.info(f"Backup directory size: {stats['backup_dir_size_mb']:.2f} MB")
        logger.info("-" * 40)
        logger.info("Retention Policy:")
        logger.info(
            f"  Daily: {stats['retention_policy']['daily_retention_days']} days"
        )
        logger.info(
            f"  Weekly: {stats['retention_policy']['weekly_retention_weeks']} weeks"
        )
        logger.info(
            f"  Monthly: {stats['retention_policy']['monthly_retention_months']} months"
        )
        logger.info("-" * 40)
        logger.info(f"Verification enabled: {stats['verification_enabled']}")
        logger.info(f"Checksum verification: {stats['checksum_verification']}")

        return True

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="FoodSave AI Backup Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create backup command
    create_parser = subparsers.add_parser("create", help="Create a new backup")
    create_parser.add_argument("--name", help="Custom backup name")

    # List backups command
    list_parser = subparsers.add_parser("list", help="List all backups")

    # Restore backup command
    restore_parser = subparsers.add_parser("restore", help="Restore a backup")
    restore_parser.add_argument("backup_name", help="Name of the backup to restore")
    restore_parser.add_argument(
        "--components", help="Comma-separated list of components to restore"
    )

    # Verify backup command
    verify_parser = subparsers.add_parser("verify", help="Verify backup integrity")
    verify_parser.add_argument("backup_name", help="Name of the backup to verify")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old backups")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show backup statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Run the appropriate command
    async def run_command():
        if args.command == "create":
            success = await create_backup(args)
        elif args.command == "list":
            success = await list_backups(args)
        elif args.command == "restore":
            success = await restore_backup(args)
        elif args.command == "verify":
            success = await verify_backup(args)
        elif args.command == "cleanup":
            success = await cleanup_backups(args)
        elif args.command == "stats":
            success = await show_stats(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            success = False

        return success

    # Run the async command
    success = asyncio.run(run_command())

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
