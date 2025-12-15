"""
===============================================================================
SYNC SERVICE
===============================================================================

File: backend/services/sync_service.py
Created: 2024-12-15
Purpose: Handles data synchronization between Cosmos DB and the in-memory cache

WHY THIS FILE EXISTS:
---------------------
The dashboard needs fresh data from Cosmos DB, but we don't want to:
  1. Query Cosmos on every API request (slow, expensive)
  2. Manually run Python scripts to update JSON files

This service solves both problems by:
  1. Running background syncs on a schedule (every 5 minutes by default)
  2. Supporting incremental syncs (only fetch new data since last sync)
  3. Providing manual sync triggers for immediate updates

SYNC STRATEGIES:
----------------
  FULL SYNC:
    - Fetches ALL records from Cosmos DB
    - Replaces entire cache
    - Used on startup or when cache is corrupted
    - Slower but guaranteed consistent

  INCREMENTAL SYNC:
    - Fetches only records with _ts > last_sync_timestamp
    - Merges new records into existing cache
    - Much faster for regular updates
    - Used for scheduled background syncs

===============================================================================
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional
import threading

from services.cosmos_client import CosmosClientService
from cache.state import CacheState


class SyncService:
    """
    Manages data synchronization between Cosmos DB and the cache.
    
    USAGE:
    ------
        cache = CacheState()
        sync_service = SyncService(cache)
        
        # Initial full sync
        await sync_service.full_sync()
        
        # Start background scheduler
        sync_service.start_scheduler()
        
        # Manual incremental sync
        await sync_service.incremental_sync()
    """
    
    def __init__(self, cache: CacheState, sync_interval_minutes: int = 5):
        """
        Initialize the sync service.
        
        PARAMETERS:
            cache: The CacheState instance to sync data into
            sync_interval_minutes: How often to run background syncs (default: 5)
        """
        self.cache = cache
        self.cosmos_client = CosmosClientService()
        self.sync_interval_minutes = sync_interval_minutes
        
        # Sync state
        self.is_syncing = False
        self._scheduler_running = False
        self._scheduler_thread: Optional[threading.Thread] = None
    
    # =========================================================================
    # SYNC OPERATIONS
    # =========================================================================
    
    async def full_sync(self) -> Dict[str, int]:
        """
        Perform a full sync - fetch ALL data from Cosmos DB.
        
        WHY FULL SYNC:
        - Used on server startup
        - Used when cache is empty or corrupted
        - Guarantees complete data consistency
        
        RETURNS:
            {"rewriter": X, "adoption": Y, "feedback": Z} - record counts
        """
        if self.is_syncing:
            print("[SYNC] Sync already in progress, skipping...")
            return {"rewriter": 0, "adoption": 0, "feedback": 0}
        
        self.is_syncing = True
        print("[SYNC] Starting FULL sync...")
        
        result = {"rewriter": 0, "adoption": 0, "feedback": 0}
        
        try:
            # Clear existing cache for full sync
            self.cache.rewriter_data = []
            self.cache.adoption_data = []
            self.cache.feedback_data = []
            
            # Fetch rewriter data (staging)
            try:
                rewriter_records = self.cosmos_client.fetch_rewriter_queries(since_ts=0)
                result["rewriter"] = self.cache.add_rewriter_records(rewriter_records)
                print(f"[SYNC] Rewriter: {result['rewriter']} records")
            except Exception as e:
                error_msg = f"Rewriter sync failed: {e}"
                print(f"[SYNC] {error_msg}")
                self.cache.add_error(error_msg)
            
            # Fetch adoption data (production)
            try:
                adoption_records = self.cosmos_client.fetch_adoption_queries(since_ts=0)
                result["adoption"] = self.cache.add_adoption_records(adoption_records)
                print(f"[SYNC] Adoption: {result['adoption']} records")
            except Exception as e:
                error_msg = f"Adoption sync failed: {e}"
                print(f"[SYNC] {error_msg}")
                self.cache.add_error(error_msg)
            
            # Fetch feedback data (production)
            try:
                feedback_records = self.cosmos_client.fetch_feedback(since_ts=0)
                result["feedback"] = self.cache.add_feedback_records(feedback_records)
                print(f"[SYNC] Feedback: {result['feedback']} records")
            except Exception as e:
                error_msg = f"Feedback sync failed: {e}"
                print(f"[SYNC] {error_msg}")
                self.cache.add_error(error_msg)
            
            # Update sync timestamp
            self.cache.update_sync_timestamp()
            print(f"[SYNC] Full sync complete. Total: {sum(result.values())} records")
            
        finally:
            self.is_syncing = False
        
        return result
    
    async def incremental_sync(self) -> Dict[str, int]:
        """
        Perform an incremental sync - fetch only NEW data since last sync.
        
        WHY INCREMENTAL:
        - Much faster than full sync
        - Lower Cosmos DB RU consumption
        - Used for scheduled background syncs
        
        RETURNS:
            {"rewriter": X, "adoption": Y, "feedback": Z} - NEW record counts
        """
        if self.is_syncing:
            print("[SYNC] Sync already in progress, skipping...")
            return {"rewriter": 0, "adoption": 0, "feedback": 0}
        
        # If no previous sync, fall back to full sync
        if self.cache.last_sync_ts_unix == 0:
            print("[SYNC] No previous sync found, performing full sync...")
            return await self.full_sync()
        
        self.is_syncing = True
        since_ts = self.cache.get_sync_timestamp_for_query()
        print(f"[SYNC] Starting INCREMENTAL sync (since_ts={since_ts})...")
        
        result = {"rewriter": 0, "adoption": 0, "feedback": 0}
        
        try:
            # Fetch new rewriter records
            try:
                rewriter_records = self.cosmos_client.fetch_rewriter_queries(since_ts=since_ts)
                result["rewriter"] = self.cache.add_rewriter_records(rewriter_records)
            except Exception as e:
                self.cache.add_error(f"Rewriter incremental sync failed: {e}")
            
            # Fetch new adoption records
            try:
                adoption_records = self.cosmos_client.fetch_adoption_queries(since_ts=since_ts)
                result["adoption"] = self.cache.add_adoption_records(adoption_records)
            except Exception as e:
                self.cache.add_error(f"Adoption incremental sync failed: {e}")
            
            # Fetch new feedback records
            try:
                feedback_records = self.cosmos_client.fetch_feedback(since_ts=since_ts)
                result["feedback"] = self.cache.add_feedback_records(feedback_records)
            except Exception as e:
                self.cache.add_error(f"Feedback incremental sync failed: {e}")
            
            # Update sync timestamp
            self.cache.update_sync_timestamp()
            
            total_new = sum(result.values())
            if total_new > 0:
                print(f"[SYNC] Incremental sync complete. Added {total_new} new records")
            else:
                print("[SYNC] Incremental sync complete. No new records.")
            
        finally:
            self.is_syncing = False
        
        return result
    
    # =========================================================================
    # BACKGROUND SCHEDULER
    # =========================================================================
    
    def start_scheduler(self):
        """
        Start the background sync scheduler.
        
        WHY BACKGROUND SCHEDULER:
        - Dashboard always has fresh data
        - No manual intervention needed
        - Runs incremental syncs every N minutes
        """
        if self._scheduler_running:
            print("[SYNC] Scheduler already running")
            return
        
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        print(f"[SYNC] Background scheduler started (interval: {self.sync_interval_minutes} min)")
    
    def stop_scheduler(self):
        """Stop the background sync scheduler."""
        self._scheduler_running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        print("[SYNC] Background scheduler stopped")
    
    def _scheduler_loop(self):
        """Internal scheduler loop - runs in background thread."""
        import time
        
        interval_seconds = self.sync_interval_minutes * 60
        
        while self._scheduler_running:
            # Wait for the interval
            time.sleep(interval_seconds)
            
            if not self._scheduler_running:
                break
            
            # Run incremental sync
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.incremental_sync())
                loop.close()
            except Exception as e:
                print(f"[SYNC] Scheduler error: {e}")
                self.cache.add_error(f"Scheduled sync failed: {e}")

