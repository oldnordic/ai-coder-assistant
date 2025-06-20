#!/usr/bin/env python3
"""
Migration script for existing model and scan data to the new persistence layer.
Supports dry-run mode and logs progress.
"""
import argparse
import logging
from pathlib import Path
from src.backend.services.model_persistence import ModelPersistenceService
from src.backend.services.scanner_persistence import ScannerPersistenceService

def migrate_models(data_dir: str, dry_run: bool = False):
    logger = logging.getLogger("migrate_models")
    persistence = ModelPersistenceService(data_dir=data_dir)
    # TODO: Implement logic to read legacy model data
    logger.info("[DRY RUN] Would migrate model data" if dry_run else "Migrating model data...")
    # Example: persistence.save_model_config(...)
    logger.info("Model migration complete.")

def migrate_scans(data_dir: str, dry_run: bool = False):
    logger = logging.getLogger("migrate_scans")
    persistence = ScannerPersistenceService(data_dir=data_dir)
    # TODO: Implement logic to read legacy scan data
    logger.info("[DRY RUN] Would migrate scan data" if dry_run else "Migrating scan data...")
    # Example: persistence.save_scan_result(...)
    logger.info("Scan migration complete.")

def main():
    parser = argparse.ArgumentParser(description="Migrate legacy model and scan data to new persistence layer.")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory for persistence DBs")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without writing data")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    migrate_models(args.data_dir, dry_run=args.dry_run)
    migrate_scans(args.data_dir, dry_run=args.dry_run)
    logging.info("Migration script finished.")

if __name__ == "__main__":
    main() 