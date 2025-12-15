"""
===============================================================================
CACHE STATE MANAGEMENT
===============================================================================

File: backend/cache/state.py
Created: 2024-12-15
Purpose: In-memory cache for dashboard data with persistence support

WHY THIS FILE EXISTS:
---------------------
Instead of re-fetching all data from Cosmos DB on every API request,
we cache the data in memory. This provides:

  1. FAST RESPONSES: API calls return instantly from memory
  2. REDUCED COSTS: Fewer Cosmos DB queries = lower RU consumption
  3. INCREMENTAL UPDATES: We track the last sync timestamp to only fetch new data
  4. PERSISTENCE: Cache state survives restarts via JSON file backup

DATA FLOW:
----------
    Cosmos DB  ──(sync)──▶  CacheState (memory)  ──(API)──▶  React Dashboard
                                 │
                                 ▼
                         cache_state.json (persistence)

HOW INCREMENTAL SYNC WORKS:
---------------------------
Traditional approach (SLOW):
    1. Query: SELECT * FROM c  (fetches ALL records)
    2. Process all records
    3. Calculate all metrics

Our approach (FAST):
    1. Store last_sync_timestamp (e.g., 1702648800)
    2. Query: SELECT * FROM c WHERE c._ts > 1702648800  (only NEW records)
    3. MERGE new records with existing cache
    4. Recalculate metrics incrementally
    5. Update last_sync_timestamp

===============================================================================
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Path to the persistence file (stores cache state between restarts)
CACHE_FILE_PATH = os.path.join(os.path.dirname(__file__), "cache_state.json")


@dataclass
class CacheState:
    """
    In-memory cache for all dashboard data.
    
    ATTRIBUTES:
    -----------
    last_sync_timestamp : datetime
        When data was last synced from Cosmos DB.
        Used for incremental sync queries: WHERE c._ts > {timestamp}
    
    last_sync_ts_unix : int
        Unix timestamp version of last_sync_timestamp.
        Cosmos DB stores _ts as Unix timestamp, so we use this for queries.
    
    rewriter_data : List[Dict]
        Raw query rewriter documents from Cosmos DB (staging).
        Contains query_rewrite_telemetry for each processed query.
    
    adoption_data : List[Dict]
        Raw conversation documents from Cosmos DB (production).
        Used to calculate WAU, MAU, stickiness, etc.
    
    feedback_data : List[Dict]
        Raw feedback documents from Cosmos DB (production).
        Contains thumbsUp/thumbsDown and categorized comments.
    
    sync_errors : List[str]
        Recent sync errors for debugging.
        Last 10 errors are kept.
    
    METHODS:
    --------
    add_rewriter_records(records) : Merge new records into cache
    add_adoption_records(records) : Merge new records into cache
    add_feedback_records(records) : Merge new records into cache
    update_sync_timestamp()       : Mark sync complete, update timestamp
    save_to_disk()                : Persist cache to JSON file
    load_from_disk()              : Restore cache from JSON file
    clear()                       : Reset all cached data
    """
    
    # Timestamps for incremental sync
    last_sync_timestamp: Optional[datetime] = None
    last_sync_ts_unix: int = 0
    
    # Raw data from Cosmos DB
    rewriter_data: List[Dict[str, Any]] = field(default_factory=list)
    adoption_data: List[Dict[str, Any]] = field(default_factory=list)
    feedback_data: List[Dict[str, Any]] = field(default_factory=list)
    
    # Error tracking
    sync_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """
        Called after dataclass initialization.
        Attempts to load persisted cache from disk.
        
        WHY: If the server restarts, we don't want to lose all cached data
        and force a full re-sync. Loading from disk provides continuity.
        """
        self.load_from_disk()
    
    # =========================================================================
    # RECORD MANAGEMENT
    # =========================================================================
    
    def add_rewriter_records(self, new_records: List[Dict]) -> int:
        """
        Add new query rewriter records to the cache.
        
        WHY MERGE BY ID:
        ----------------
        Cosmos DB documents have unique IDs. When doing incremental sync,
        we might get updates to existing documents (not just new ones).
        Merging by ID ensures we have the latest version of each document.
        
        PARAMETERS:
            new_records: List of documents from Cosmos DB query
        
        RETURNS:
            Number of NEW records added (not updates)
        """
        if not new_records:
            return 0
        
        # Build a lookup of existing records by ID
        existing_ids = {doc.get("id") for doc in self.rewriter_data}
        
        added_count = 0
        for record in new_records:
            record_id = record.get("id")
            if record_id not in existing_ids:
                # New record - add to cache
                self.rewriter_data.append(record)
                existing_ids.add(record_id)
                added_count += 1
            else:
                # Existing record - update in place
                for i, existing in enumerate(self.rewriter_data):
                    if existing.get("id") == record_id:
                        self.rewriter_data[i] = record
                        break
        
        return added_count
    
    def add_adoption_records(self, new_records: List[Dict]) -> int:
        """
        Add new adoption/conversation records to the cache.
        Same merge-by-ID logic as add_rewriter_records.
        """
        if not new_records:
            return 0
        
        existing_ids = {doc.get("id") or doc.get("conversation_id") for doc in self.adoption_data}
        
        added_count = 0
        for record in new_records:
            record_id = record.get("id") or record.get("conversation_id")
            if record_id not in existing_ids:
                self.adoption_data.append(record)
                existing_ids.add(record_id)
                added_count += 1
            else:
                for i, existing in enumerate(self.adoption_data):
                    existing_id = existing.get("id") or existing.get("conversation_id")
                    if existing_id == record_id:
                        self.adoption_data[i] = record
                        break
        
        return added_count
    
    def add_feedback_records(self, new_records: List[Dict]) -> int:
        """
        Add new feedback records to the cache.
        Same merge-by-ID logic as add_rewriter_records.
        """
        if not new_records:
            return 0
        
        existing_ids = {doc.get("id") for doc in self.feedback_data}
        
        added_count = 0
        for record in new_records:
            record_id = record.get("id")
            if record_id not in existing_ids:
                self.feedback_data.append(record)
                existing_ids.add(record_id)
                added_count += 1
            else:
                for i, existing in enumerate(self.feedback_data):
                    if existing.get("id") == record_id:
                        self.feedback_data[i] = record
                        break
        
        return added_count
    
    # =========================================================================
    # TIMESTAMP MANAGEMENT
    # =========================================================================
    
    def update_sync_timestamp(self):
        """
        Update the last sync timestamp to NOW.
        
        WHY: After a successful sync, we update the timestamp so the next
        incremental sync only fetches records newer than this time.
        
        IMPORTANT: We use UTC timezone to avoid issues with server timezone.
        Cosmos DB _ts is always in UTC.
        """
        self.last_sync_timestamp = datetime.now(timezone.utc)
        self.last_sync_ts_unix = int(self.last_sync_timestamp.timestamp())
        
        # Persist to disk after updating
        self.save_to_disk()
    
    def get_sync_timestamp_for_query(self) -> int:
        """
        Get the Unix timestamp to use in incremental sync queries.
        
        RETURNS:
            Unix timestamp (int) for use in: WHERE c._ts > {timestamp}
            Returns 0 if no previous sync (will fetch all data)
        """
        return self.last_sync_ts_unix
    
    # =========================================================================
    # ERROR TRACKING
    # =========================================================================
    
    def add_error(self, error_message: str):
        """
        Log a sync error.
        Keeps only the last 10 errors to avoid memory bloat.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        self.sync_errors.append(f"[{timestamp}] {error_message}")
        
        # Keep only last 10 errors
        if len(self.sync_errors) > 10:
            self.sync_errors = self.sync_errors[-10:]
    
    # =========================================================================
    # PERSISTENCE
    # =========================================================================
    
    def save_to_disk(self):
        """
        Persist cache state to a JSON file.
        
        WHY: If the server restarts (deploy, crash, etc.), we don't want
        to lose the last_sync_timestamp and have to do a full re-sync.
        
        NOTE: We only persist timestamps and record counts, not the actual
        data. The data would be too large and stale anyway. On restart,
        we'll do a full sync but can skip records we've already processed.
        """
        try:
            state = {
                "last_sync_timestamp": self.last_sync_timestamp.isoformat() if self.last_sync_timestamp else None,
                "last_sync_ts_unix": self.last_sync_ts_unix,
                "record_counts": {
                    "rewriter": len(self.rewriter_data),
                    "adoption": len(self.adoption_data),
                    "feedback": len(self.feedback_data),
                },
                "sync_errors": self.sync_errors,
            }
            
            with open(CACHE_FILE_PATH, "w") as f:
                json.dump(state, f, indent=2)
            
        except Exception as e:
            print(f"[CACHE] Warning: Could not save cache state: {e}")
    
    def load_from_disk(self):
        """
        Restore cache state from JSON file.
        
        WHY: On server startup, check if we have a previous sync state.
        If so, we can use the timestamp for incremental sync instead of
        fetching everything from scratch.
        """
        try:
            if os.path.exists(CACHE_FILE_PATH):
                with open(CACHE_FILE_PATH, "r") as f:
                    state = json.load(f)
                
                if state.get("last_sync_timestamp"):
                    self.last_sync_timestamp = datetime.fromisoformat(state["last_sync_timestamp"])
                    self.last_sync_ts_unix = state.get("last_sync_ts_unix", 0)
                
                self.sync_errors = state.get("sync_errors", [])
                
                print(f"[CACHE] Loaded previous state. Last sync: {self.last_sync_timestamp}")
            else:
                print("[CACHE] No previous state found. Will do full sync.")
                
        except Exception as e:
            print(f"[CACHE] Warning: Could not load cache state: {e}")
    
    def clear(self):
        """
        Reset all cached data.
        
        WHY: Useful for forcing a complete refresh or debugging.
        """
        self.last_sync_timestamp = None
        self.last_sync_ts_unix = 0
        self.rewriter_data = []
        self.adoption_data = []
        self.feedback_data = []
        self.sync_errors = []
        
        # Remove persisted state file
        try:
            if os.path.exists(CACHE_FILE_PATH):
                os.remove(CACHE_FILE_PATH)
        except Exception:
            pass






