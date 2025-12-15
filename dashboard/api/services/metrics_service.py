"""
===============================================================================
METRICS SERVICE
===============================================================================

File: backend/services/metrics_service.py
Created: 2024-12-15
Purpose: Calculates dashboard metrics from cached Cosmos DB data

WHY THIS FILE EXISTS:
---------------------
The React dashboard needs aggregated metrics, not raw Cosmos documents.
This service transforms raw data into the exact JSON structure the
dashboard components expect.

METRICS CALCULATED:
-------------------
  REWRITER METRICS:
    - Total queries, rewritten count, pass-through count
    - Rewrite rate, average expansion count
    - Zero-result rates (rewritten vs pass-through)
    - Latency statistics (min, max, avg, p95)
    - Quality scores (relevance, groundedness, completeness)
    - Top matched entities

  ADOPTION METRICS:
    - WAU (Weekly Active Users)
    - MAU (Monthly Active Users)
    - Stickiness (WAU/MAU ratio)
    - Query trends over time
    - Response time statistics
    - Top users

  FEEDBACK METRICS:
    - Total feedback count
    - Thumbs up/down breakdown
    - Positive rate percentage
    - Category distribution
    - Trend over time

===============================================================================
"""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any

from cache.state import CacheState


class MetricsService:
    """
    Calculates aggregated metrics from cached data.
    
    USAGE:
    ------
        cache = CacheState()
        metrics = MetricsService(cache)
        
        rewriter_data = metrics.calculate_rewriter_metrics()
        adoption_data = metrics.calculate_adoption_metrics()
        feedback_data = metrics.calculate_feedback_metrics()
    """
    
    def __init__(self, cache: CacheState):
        """
        Initialize metrics service with a cache reference.
        
        PARAMETERS:
            cache: The CacheState instance containing raw data
        """
        self.cache = cache
    
    # =========================================================================
    # REWRITER METRICS
    # =========================================================================
    
    def calculate_rewriter_metrics(self) -> Dict[str, Any]:
        """
        Calculate query rewriter effectiveness metrics.
        
        RETURNS:
            {
                "summary": {...},
                "effectiveness": {...},
                "latencyStats": {...},
                "qualityScores": {...},
                "topEntities": [...],
                "rewrittenQueries": [...],
                "zeroResultQueries": [...]
            }
        """
        raw_data = self.cache.rewriter_data
        total = len(raw_data)
        
        if total == 0:
            return self._empty_rewriter_metrics()
        
        # Separate rewritten vs pass-through
        rewritten = []
        passthrough = []
        
        for doc in raw_data:
            telemetry = doc.get('query_rewrite_telemetry', {})
            expansion_count = telemetry.get('expansion_count', 0)
            
            if expansion_count > 0:
                rewritten.append(doc)
            else:
                passthrough.append(doc)
        
        # Calculate rates
        rewrite_rate = round(len(rewritten) / total * 100, 1) if total > 0 else 0
        
        # Zero-result rates
        rewritten_zeros = sum(1 for d in rewritten if d.get('resultCount', 0) == 0)
        passthrough_zeros = sum(1 for d in passthrough if d.get('resultCount', 0) == 0)
        
        rewritten_zero_rate = round(rewritten_zeros / len(rewritten) * 100, 1) if rewritten else 0
        passthrough_zero_rate = round(passthrough_zeros / len(passthrough) * 100, 1) if passthrough else 0
        
        # Average results
        rewritten_avg = round(sum(d.get('resultCount', 0) for d in rewritten) / len(rewritten), 1) if rewritten else 0
        passthrough_avg = round(sum(d.get('resultCount', 0) for d in passthrough) / len(passthrough), 1) if passthrough else 0
        
        # Latency stats
        latencies = []
        for d in rewritten:
            lat = d.get('query_rewrite_telemetry', {}).get('rewrite_time_ms', 0)
            if lat > 0:
                latencies.append(lat)
        
        # Average expansion count
        expansion_counts = [d.get('query_rewrite_telemetry', {}).get('expansion_count', 0) for d in rewritten]
        avg_expansion = round(sum(expansion_counts) / len(expansion_counts), 1) if expansion_counts else 0
        
        # Entity match frequency
        entity_counts = defaultdict(int)
        for d in rewritten:
            for entity in d.get('query_rewrite_telemetry', {}).get('matched_entities', []):
                entity_counts[entity] += 1
        
        top_entities = [
            {"entity": k, "count": v} 
            for k, v in sorted(entity_counts.items(), key=lambda x: -x[1])[:10]
        ]
        
        # Build rewritten queries list
        rewritten_queries = []
        for d in rewritten[:50]:  # Limit to 50 for UI
            telemetry = d.get('query_rewrite_telemetry', {})
            scores = d.get('evaluation_scores', {})
            rewritten_queries.append({
                "id": str(d.get('conversation_id', d.get('id', '')))[:8],
                "query": d.get('conversation', ''),
                "matchedEntities": telemetry.get('matched_entities', []),
                "expansionCount": telemetry.get('expansion_count', 0),
                "expandedQuery": telemetry.get('expanded_query', ''),
                "rewriteTimeMs": round(telemetry.get('rewrite_time_ms', 0), 2),
                "resultCount": d.get('resultCount', 0),
                "scores": {
                    "relevance": scores.get('relevance', 0),
                    "groundedness": scores.get('groundedness', 0),
                    "completeness": scores.get('completeness', 0)
                }
            })
        
        # Zero result queries (content gaps)
        zero_result_queries = []
        for d in raw_data:
            if d.get('resultCount', 0) == 0:
                zero_result_queries.append({
                    "id": str(d.get('conversation_id', d.get('id', '')))[:8],
                    "query": d.get('conversation', ''),
                    "matchedEntities": d.get('query_rewrite_telemetry', {}).get('matched_entities', []),
                    "wasRewritten": d.get('query_rewrite_telemetry', {}).get('expansion_count', 0) > 0,
                    "timestamp": d.get('timestamp', '')
                })
        
        return {
            "summary": {
                "totalQueries": total,
                "rewrittenCount": len(rewritten),
                "passthroughCount": len(passthrough),
                "rewriteRate": rewrite_rate,
                "avgExpansionCount": avg_expansion
            },
            "effectiveness": {
                "rewrittenZeroRate": rewritten_zero_rate,
                "passthroughZeroRate": passthrough_zero_rate,
                "rewrittenAvgResults": rewritten_avg,
                "passthroughAvgResults": passthrough_avg
            },
            "latencyStats": {
                "min": round(min(latencies), 2) if latencies else 0,
                "max": round(max(latencies), 2) if latencies else 0,
                "avg": round(sum(latencies) / len(latencies), 2) if latencies else 0,
                "p95": self._percentile(latencies, 95),
                "target": 40
            },
            "qualityScores": {
                "rewritten": self._avg_scores(rewritten),
                "passthrough": self._avg_scores(passthrough)
            },
            "topEntities": top_entities,
            "rewrittenQueries": rewritten_queries,
            "zeroResultQueries": zero_result_queries[:30]
        }
    
    def _empty_rewriter_metrics(self) -> Dict[str, Any]:
        """Return empty rewriter metrics structure."""
        return {
            "summary": {
                "totalQueries": 0, "rewrittenCount": 0, "passthroughCount": 0,
                "rewriteRate": 0, "avgExpansionCount": 0
            },
            "effectiveness": {
                "rewrittenZeroRate": 0, "passthroughZeroRate": 0,
                "rewrittenAvgResults": 0, "passthroughAvgResults": 0
            },
            "latencyStats": {"min": 0, "max": 0, "avg": 0, "p95": 0, "target": 40},
            "qualityScores": {
                "rewritten": {"relevance": 0, "groundedness": 0, "completeness": 0},
                "passthrough": {"relevance": 0, "groundedness": 0, "completeness": 0}
            },
            "topEntities": [],
            "rewrittenQueries": [],
            "zeroResultQueries": []
        }
    
    # =========================================================================
    # ADOPTION METRICS
    # =========================================================================
    
    def calculate_adoption_metrics(self) -> Dict[str, Any]:
        """
        Calculate user adoption metrics (WAU, MAU, stickiness, etc.)
        
        RETURNS:
            {
                "wau": 45,
                "mau": 120,
                "stickiness": 37.5,
                "totalQueries": 5000,
                "totalUsers": 200,
                "queriesPerUser": 25.0,
                "avgResponseTimeMs": 3500,
                "peakHour": 14,
                "queryTrend": [...],
                "topUsers": [...]
            }
        """
        raw_data = self.cache.adoption_data
        now = datetime.now()
        
        # Extract user IDs and timestamps
        user_queries = []
        for doc in raw_data:
            user_id = doc.get('user_id') or doc.get('user_name') or 'anonymous'
            ts = doc.get('_ts', 0)
            query_time = datetime.fromtimestamp(ts) if ts else None
            
            if query_time:
                user_queries.append({
                    'user_id': user_id,
                    'timestamp': query_time,
                    'response_time': (doc.get('llm_telemetry') or {}).get('response_time_ms', 0)
                })
        
        if not user_queries:
            return self._empty_adoption_metrics()
        
        # --- WAU / MAU ---
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        wau_users = set(q['user_id'] for q in user_queries if q['timestamp'] >= week_ago)
        mau_users = set(q['user_id'] for q in user_queries if q['timestamp'] >= month_ago)
        
        wau = len(wau_users)
        mau = len(mau_users)
        stickiness = round((wau / mau * 100), 1) if mau > 0 else 0
        
        # --- Daily Query Volume (last 30 days) ---
        daily_counts = defaultdict(int)
        for q in user_queries:
            if q['timestamp'] >= month_ago:
                day_key = q['timestamp'].strftime('%Y-%m-%d')
                daily_counts[day_key] += 1
        
        sorted_days = sorted(daily_counts.items())
        query_trend = [{"date": d, "count": c} for d, c in sorted_days]
        
        # --- Queries per User ---
        user_query_counts = defaultdict(int)
        for q in user_queries:
            user_query_counts[q['user_id']] += 1
        
        total_users = len(set(q['user_id'] for q in user_queries))
        queries_per_user = round(len(user_queries) / total_users, 1) if total_users > 0 else 0
        
        # --- Response Time Stats ---
        response_times = [q['response_time'] for q in user_queries if q['response_time'] and q['response_time'] > 0]
        avg_response_time = round(sum(response_times) / len(response_times), 0) if response_times else 0
        
        # --- Peak Hours ---
        hour_counts = defaultdict(int)
        for q in user_queries:
            hour_counts[q['timestamp'].hour] += 1
        peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else 0
        
        # --- Top Users (anonymized) ---
        top_users = []
        for user_id, count in sorted(user_query_counts.items(), key=lambda x: -x[1])[:10]:
            display_name = str(user_id)[:8] + "..." if len(str(user_id)) > 8 else str(user_id)
            top_users.append({"user": display_name, "queries": count})
        
        return {
            "wau": wau,
            "mau": mau,
            "stickiness": stickiness,
            "totalQueries": len(user_queries),
            "totalUsers": total_users,
            "queriesPerUser": queries_per_user,
            "avgResponseTimeMs": avg_response_time,
            "peakHour": peak_hour,
            "queryTrend": query_trend,
            "topUsers": top_users
        }
    
    def _empty_adoption_metrics(self) -> Dict[str, Any]:
        """Return empty adoption metrics structure."""
        return {
            "wau": 0, "mau": 0, "stickiness": 0, "totalQueries": 0,
            "totalUsers": 0, "queriesPerUser": 0, "avgResponseTimeMs": 0,
            "peakHour": 0, "queryTrend": [], "topUsers": []
        }
    
    # =========================================================================
    # FEEDBACK METRICS
    # =========================================================================
    
    def calculate_feedback_metrics(self) -> Dict[str, Any]:
        """
        Calculate feedback analysis metrics.
        
        RETURNS:
            {
                "summary": {
                    "total": 100,
                    "thumbsUp": 70,
                    "thumbsDown": 30,
                    "positiveRate": 70.0
                },
                "trend": [...],
                "categoryBreakdown": [...],
                "feedbackItems": [...]
            }
        """
        feedback_data = self.cache.feedback_data
        
        if not feedback_data:
            return self._empty_feedback_metrics()
        
        total = len(feedback_data)
        
        # Count by type
        thumbs_up = [f for f in feedback_data if f.get('feedbackType') == 'thumbsUp']
        thumbs_down = [f for f in feedback_data if f.get('feedbackType') == 'thumbsDown']
        
        # Feedback over time (last 30 days)
        now = datetime.now()
        month_ago = now - timedelta(days=30)
        
        daily_feedback = defaultdict(lambda: {"positive": 0, "negative": 0})
        for f in feedback_data:
            ts = f.get('_ts', 0)
            if ts:
                feedback_time = datetime.fromtimestamp(ts)
                if feedback_time >= month_ago:
                    day_key = feedback_time.strftime('%Y-%m-%d')
                    if f.get('feedbackType') == 'thumbsUp':
                        daily_feedback[day_key]['positive'] += 1
                    else:
                        daily_feedback[day_key]['negative'] += 1
        
        feedback_trend = [
            {"date": d, "positive": v['positive'], "negative": v['negative']} 
            for d, v in sorted(daily_feedback.items())
        ]
        
        # Category breakdown
        category_counts = defaultdict(int)
        for f in feedback_data:
            cat = f.get('category', 'Uncategorized')
            category_counts[cat] += 1
        
        category_breakdown = [
            {"category": k, "count": v} 
            for k, v in sorted(category_counts.items(), key=lambda x: -x[1])
        ]
        
        # Build feedback items list
        feedback_items = []
        for f in feedback_data[:100]:  # Limit to 100 for UI
            feedback_items.append({
                "id": str(f.get('id', ''))[:12],
                "timestamp": f.get('timestamp', ''),
                "userName": f.get('userName', 'Anonymous'),
                "feedbackType": f.get('feedbackType', 'unknown'),
                "comment": f.get('comment', ''),
                "category": f.get('category', 'Uncategorized'),
                "conversationId": str(f.get('conversationId', ''))[:12]
            })
        
        # Sort by timestamp descending
        feedback_items.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "summary": {
                "total": total,
                "thumbsUp": len(thumbs_up),
                "thumbsDown": len(thumbs_down),
                "positiveRate": round(len(thumbs_up) / total * 100, 1) if total > 0 else 0
            },
            "trend": feedback_trend,
            "categoryBreakdown": category_breakdown,
            "feedbackItems": feedback_items
        }
    
    def _empty_feedback_metrics(self) -> Dict[str, Any]:
        """Return empty feedback metrics structure."""
        return {
            "summary": {"total": 0, "thumbsUp": 0, "thumbsDown": 0, "positiveRate": 0},
            "trend": [],
            "categoryBreakdown": [],
            "feedbackItems": []
        }
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _avg_scores(self, docs: List[Dict]) -> Dict[str, float]:
        """Calculate average evaluation scores for a list of documents."""
        if not docs:
            return {"relevance": 0, "groundedness": 0, "completeness": 0}
        
        scores_list = [d.get('evaluation_scores', {}) for d in docs if d.get('evaluation_scores')]
        if not scores_list:
            return {"relevance": 0, "groundedness": 0, "completeness": 0}
        
        r = sum(s.get('relevance', 0) for s in scores_list) / len(scores_list)
        g = sum(s.get('groundedness', 0) for s in scores_list) / len(scores_list)
        c = sum(s.get('completeness', 0) for s in scores_list) / len(scores_list)
        
        return {"relevance": round(r, 2), "groundedness": round(g, 2), "completeness": round(c, 2)}
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a list."""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        index = min(index, len(sorted_data) - 1)
        
        return round(sorted_data[index], 2)

