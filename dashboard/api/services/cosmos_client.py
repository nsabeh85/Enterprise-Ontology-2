"""
===============================================================================
COSMOS DB CLIENT SERVICE
===============================================================================

File: backend/services/cosmos_client.py
Created: 2024-12-15
Purpose: Manages connections to Azure Cosmos DB instances

WHY THIS FILE EXISTS:
---------------------
The dashboard needs data from TWO Cosmos DB instances:

  1. STAGING (query rewriter data)
     - Database: "history"
     - Container: "conversation"
     - Contains: query_rewrite_telemetry, expansion metrics
     
  2. PRODUCTION (adoption + feedback data)
     - Database: "history"
     - Containers: "conversation" (adoption), "feedback" (user feedback)
     - Contains: User queries, response times, thumbs up/down

This service:
  - Manages connections to both instances
  - Provides query methods with incremental sync support
  - Handles connection errors gracefully

ENVIRONMENT VARIABLES REQUIRED:
-------------------------------
For Staging:
  - COSMOS_ENDPOINT: https://your-staging.documents.azure.com:443/
  - COSMOS_KEY: your-staging-key

For Production:
  - COSMOS_PROD_ENDPOINT: https://your-prod.documents.azure.com:443/
  - COSMOS_PROD_KEY: your-prod-key

===============================================================================
"""

import os
from typing import List, Dict, Any, Optional
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class CosmosClientService:
    """
    Manages Cosmos DB connections for the dashboard.
    
    USAGE:
    ------
        client = CosmosClientService()
        
        # Fetch rewriter data (with incremental sync)
        new_records = client.fetch_rewriter_queries(since_ts=1702648800)
        
        # Fetch adoption data
        adoption_records = client.fetch_adoption_queries()
        
        # Fetch feedback
        feedback_records = client.fetch_feedback()
    """
    
    def __init__(self):
        """
        Initialize Cosmos DB connections.
        
        WHY LAZY INITIALIZATION:
        We don't connect immediately - connections are created when first needed.
        This prevents errors if one database is unavailable but we only need the other.
        """
        self._staging_client = None
        self._staging_container = None
        
        self._prod_client = None
        self._prod_conversation_container = None
        self._prod_feedback_container = None
        
        # Track connection status for debugging
        self.staging_connected = False
        self.prod_connected = False
    
    # =========================================================================
    # STAGING CONNECTION (Query Rewriter Data)
    # =========================================================================
    
    def _get_staging_container(self):
        """
        Get or create the staging conversation container client.
        
        WHY LAZY CONNECTION:
        Connect only when first needed. This allows the server to start
        even if Cosmos is temporarily unavailable.
        """
        if self._staging_container is None:
            endpoint = os.getenv("COSMOS_ENDPOINT")
            key = os.getenv("COSMOS_KEY")
            
            if not endpoint or not key:
                raise ValueError(
                    "Missing COSMOS_ENDPOINT or COSMOS_KEY environment variables. "
                    "Please set them in your .env file."
                )
            
            try:
                self._staging_client = CosmosClient(endpoint, credential=key)
                database = self._staging_client.get_database_client("history")
                self._staging_container = database.get_container_client("conversation")
                self.staging_connected = True
                print("[COSMOS] Connected to Staging database")
            except Exception as e:
                print(f"[COSMOS] Failed to connect to Staging: {e}")
                raise
        
        return self._staging_container
    
    # =========================================================================
    # PRODUCTION CONNECTION (Adoption + Feedback Data)
    # =========================================================================
    
    def _get_prod_conversation_container(self):
        """Get or create the production conversation container client."""
        if self._prod_conversation_container is None:
            endpoint = os.getenv("COSMOS_PROD_ENDPOINT")
            key = os.getenv("COSMOS_PROD_KEY")
            
            if not endpoint or not key:
                raise ValueError(
                    "Missing COSMOS_PROD_ENDPOINT or COSMOS_PROD_KEY environment variables. "
                    "Please set them in your .env file."
                )
            
            try:
                self._prod_client = CosmosClient(endpoint, credential=key)
                database = self._prod_client.get_database_client("history")
                self._prod_conversation_container = database.get_container_client("conversation")
                self.prod_connected = True
                print("[COSMOS] Connected to Production database")
            except Exception as e:
                print(f"[COSMOS] Failed to connect to Production: {e}")
                raise
        
        return self._prod_conversation_container
    
    def _get_prod_feedback_container(self):
        """Get or create the production feedback container client."""
        if self._prod_feedback_container is None:
            # Ensure we have the prod client first
            self._get_prod_conversation_container()
            
            database = self._prod_client.get_database_client("history")
            self._prod_feedback_container = database.get_container_client("feedback")
        
        return self._prod_feedback_container
    
    # =========================================================================
    # QUERY METHODS
    # =========================================================================
    
    def fetch_rewriter_queries(self, since_ts: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch query rewriter data from Staging.
        
        WHY INCREMENTAL SYNC:
        ---------------------
        Instead of SELECT * FROM c (slow, expensive), we do:
        SELECT * FROM c WHERE c._ts > {since_ts}
        
        This only returns records created/updated AFTER the given timestamp.
        For a system with 10,000 records but only 50 new since last sync,
        we fetch 50 instead of 10,000. HUGE performance improvement.
        
        PARAMETERS:
            since_ts: Unix timestamp. Only fetch records with _ts > this value.
                      Pass 0 to fetch all records (full sync).
            limit: Optional limit on number of records (for testing).
        
        RETURNS:
            List of documents with query_rewrite_telemetry.
        """
        container = self._get_staging_container()
        
        # Build query with incremental support
        if since_ts > 0:
            # Incremental sync: only new/updated records
            query = f"""
            SELECT * FROM c 
            WHERE IS_DEFINED(c.query_rewrite_telemetry) 
              AND c._ts > {since_ts}
            ORDER BY c._ts DESC
            """
            print(f"[COSMOS] Incremental rewriter query (since_ts={since_ts})")
        else:
            # Full sync: all records
            query = """
            SELECT * FROM c 
            WHERE IS_DEFINED(c.query_rewrite_telemetry)
            ORDER BY c._ts DESC
            """
            print("[COSMOS] Full rewriter query")
        
        try:
            results = list(container.query_items(
                query=query,
                enable_cross_partition_query=True,
            ))
            
            if limit:
                results = results[:limit]
            
            print(f"[COSMOS] Fetched {len(results)} rewriter records")
            return results
            
        except exceptions.CosmosHttpResponseError as e:
            print(f"[COSMOS] Query error: {e}")
            raise
    
    def fetch_adoption_queries(self, since_ts: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch adoption/conversation data from Production.
        
        WHY THESE FIELDS:
        -----------------
        We select specific fields instead of SELECT * to reduce payload size:
        - user_id/user_name: For unique user counting (WAU, MAU)
        - timestamp/_ts: For time-based analysis
        - conversation_id: For tracking unique conversations
        - llm_telemetry: For response time metrics
        
        PARAMETERS:
            since_ts: Unix timestamp for incremental sync.
            limit: Optional limit on number of records.
        
        RETURNS:
            List of conversation documents.
        """
        container = self._get_prod_conversation_container()
        
        if since_ts > 0:
            query = f"""
            SELECT 
                c.id,
                c.user_id,
                c.user_name,
                c.timestamp,
                c._ts,
                c.conversation_id,
                c.conversation,
                c.llm_telemetry
            FROM c 
            WHERE c._ts > {since_ts}
            ORDER BY c._ts DESC
            """
            print(f"[COSMOS] Incremental adoption query (since_ts={since_ts})")
        else:
            query = """
            SELECT 
                c.id,
                c.user_id,
                c.user_name,
                c.timestamp,
                c._ts,
                c.conversation_id,
                c.conversation,
                c.llm_telemetry
            FROM c 
            ORDER BY c._ts DESC
            """
            print("[COSMOS] Full adoption query")
        
        try:
            results = list(container.query_items(
                query=query,
                enable_cross_partition_query=True,
            ))
            
            if limit:
                results = results[:limit]
            
            print(f"[COSMOS] Fetched {len(results)} adoption records")
            return results
            
        except exceptions.CosmosHttpResponseError as e:
            print(f"[COSMOS] Query error: {e}")
            raise
    
    def fetch_feedback(self, since_ts: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch feedback data from Production.
        
        PARAMETERS:
            since_ts: Unix timestamp for incremental sync.
            limit: Optional limit on number of records.
        
        RETURNS:
            List of feedback documents (thumbsUp/thumbsDown with comments).
        """
        container = self._get_prod_feedback_container()
        
        if since_ts > 0:
            query = f"""
            SELECT * FROM c 
            WHERE c._ts > {since_ts}
            ORDER BY c._ts DESC
            """
            print(f"[COSMOS] Incremental feedback query (since_ts={since_ts})")
        else:
            query = """
            SELECT * FROM c 
            ORDER BY c._ts DESC
            """
            print("[COSMOS] Full feedback query")
        
        try:
            results = list(container.query_items(
                query=query,
                enable_cross_partition_query=True,
            ))
            
            if limit:
                results = results[:limit]
            
            print(f"[COSMOS] Fetched {len(results)} feedback records")
            return results
            
        except exceptions.CosmosHttpResponseError as e:
            print(f"[COSMOS] Query error: {e}")
            raise
    
    # =========================================================================
    # HEALTH CHECK
    # =========================================================================
    
    def check_connections(self) -> Dict[str, bool]:
        """
        Test connections to both Cosmos DB instances.
        
        RETURNS:
            {"staging": True/False, "production": True/False}
        """
        results = {"staging": False, "production": False}
        
        try:
            self._get_staging_container()
            results["staging"] = True
        except Exception:
            pass
        
        try:
            self._get_prod_conversation_container()
            results["production"] = True
        except Exception:
            pass
        
        return results






