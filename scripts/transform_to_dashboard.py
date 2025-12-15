import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# ANSWER SCORER (embedded to avoid import issues)
# =============================================================================

def score_answer(query: str, answer: str, result_count: int) -> dict:
    """
    Score an answer using LLM-as-judge (reference-free).
    Returns relevance, groundedness, completeness scores (1-5).
    """
    from openai import AzureOpenAI
    
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version="2024-10-21"
    )
    
    prompt = f"""You are an expert evaluator for a data center AI assistant.

Score this response on three dimensions (1-5 scale):

QUERY: {query}
ANSWER: {answer}
DOCUMENTS RETRIEVED: {result_count}

Score each dimension:
1. RELEVANCE: Does the answer address what was asked? (1=off-topic, 5=perfectly relevant)
2. GROUNDEDNESS: Does the answer seem based on retrieved documents, not hallucinated? (1=made up, 5=well-grounded)
3. COMPLETENESS: Is the answer thorough enough? (1=too brief, 5=comprehensive)

Respond in this exact JSON format only:
{{"relevance": X, "groundedness": X, "completeness": X, "reasoning": "brief explanation"}}
"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        print(f"Scoring error: {e}")
        return {"relevance": 0, "groundedness": 0, "completeness": 0, "reasoning": f"Error: {e}"}


# =============================================================================
# AI FEEDBACK CATEGORIZER
# =============================================================================

def categorize_feedback_with_ai(feedback_items: list) -> list:
    """
    Use GPT to categorize feedback comments into themes.
    Categories: ServiceFabric, Capacity, Connectivity, General Info, Out-of-Scope, Other
    """
    from openai import AzureOpenAI
    
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version="2024-10-21"
    )
    
    categorized = []
    
    for item in feedback_items:
        comment = item.get('comment', '')
        
        if not comment or len(comment) < 3:
            item['category'] = 'Other'
            categorized.append(item)
            continue
        
        prompt = f"""Categorize this data center chatbot query into ONE category:

QUERY: {comment}

Categories:
- ServiceFabric: Questions about ServiceFabric/SF product
- Capacity: Questions about power, space, MW, kW, availability
- Connectivity: Questions about network, Metro Connect, NSPs, cloud
- Facilities: Questions about specific sites, locations, data centers
- General Info: General questions about Digital Realty
- Out-of-Scope: Not related to data centers (HR, jokes, document creation)
- Other: Doesn't fit above categories

Respond with ONLY the category name, nothing else."""

        try:
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=20
            )
            
            category = response.choices[0].message.content.strip()
            # Validate category
            valid_categories = ['ServiceFabric', 'Capacity', 'Connectivity', 'Facilities', 'General Info', 'Out-of-Scope', 'Other']
            if category not in valid_categories:
                category = 'Other'
            
            item['category'] = category
            
        except Exception as e:
            print(f"Categorization error: {e}")
            item['category'] = 'Other'
        
        categorized.append(item)
    
    return categorized


# =============================================================================
# COSMOS DB CONNECTIONS
# =============================================================================

def connect_to_cosmos_staging():
    """Connect to Cosmos DB (Staging) for query rewriter data."""
    client = CosmosClient(
        os.getenv("COSMOS_ENDPOINT"),
        credential=os.getenv("COSMOS_KEY")
    )
    database = client.get_database_client("history")
    container = database.get_container_client("conversation")
    return container


def connect_to_cosmos_prod():
    """Connect to Production Cosmos DB for adoption metrics."""
    client = CosmosClient(
        os.getenv("COSMOS_PROD_ENDPOINT"),
        credential=os.getenv("COSMOS_PROD_KEY")
    )
    database = client.get_database_client("history")
    container = database.get_container_client("conversation")
    return container


def connect_to_cosmos_prod_feedback():
    """Connect to Production Cosmos DB feedback container."""
    client = CosmosClient(
        os.getenv("COSMOS_PROD_ENDPOINT"),
        credential=os.getenv("COSMOS_PROD_KEY")
    )
    database = client.get_database_client("history")
    container = database.get_container_client("feedback")
    return container


# =============================================================================
# DATA FETCHING
# =============================================================================

def fetch_rewriter_queries(container):
    """Fetch all queries that have query rewrite telemetry."""
    query = """
    SELECT * FROM c 
    WHERE IS_DEFINED(c.query_rewrite_telemetry)
    ORDER BY c._ts DESC
    """
    results = list(container.query_items(query, enable_cross_partition_query=True))
    print(f"Fetched {len(results)} queries with rewrite telemetry")
    return results


def fetch_all_queries_for_adoption(container, days=None):
    """Fetch all queries from production for adoption metrics."""
    
    if days:
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_ts = int(cutoff.timestamp())
        query = f"""
        SELECT 
            c.user_id,
            c.user_name,
            c.timestamp,
            c._ts,
            c.conversation_id,
            c.conversation,
            c.llm_telemetry
        FROM c 
        WHERE c._ts >= {cutoff_ts}
        ORDER BY c._ts DESC
        """
    else:
        query = """
        SELECT 
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
    
    results = list(container.query_items(query, enable_cross_partition_query=True))
    print(f"Fetched {len(results)} total queries for adoption")
    return results


def fetch_feedback(container, days=None):
    """Fetch feedback from production feedback container."""
    
    if days:
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_ts = int(cutoff.timestamp())
        query = f"""
        SELECT * FROM c 
        WHERE c._ts >= {cutoff_ts}
        ORDER BY c._ts DESC
        """
    else:
        query = """
        SELECT * FROM c 
        ORDER BY c._ts DESC
        """
    
    results = list(container.query_items(query, enable_cross_partition_query=True))
    print(f"Fetched {len(results)} feedback items")
    return results


# =============================================================================
# SCORING
# =============================================================================

def score_unscored_queries(raw_data, container):
    """Score queries that don't have evaluation scores yet."""
    scored_count = 0
    
    for doc in raw_data:
        if doc.get('evaluation_scores'):
            continue
        
        query = doc.get('conversation', '')
        answer = doc.get('llm_response', '')
        result_count = doc.get('resultCount', 0)
        
        if not query or not answer:
            continue
        
        scores = score_answer(query, answer, result_count)
        
        doc['evaluation_scores'] = scores
        
        try:
            container.upsert_item(doc)
            scored_count += 1
        except Exception as e:
            print(f"Failed to update doc: {e}")
    
    return scored_count


# =============================================================================
# ADOPTION METRICS CALCULATION
# =============================================================================

def calculate_adoption_metrics(raw_data):
    """Calculate WAU, MAU, retention, and usage trends."""
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
        return {
            "wau": 0, "mau": 0, "stickiness": 0, "totalQueries": 0,
            "queriesPerUser": 0, "avgResponseTimeMs": 0,
            "peakHour": 0, "queryTrend": [], "topUsers": [], "totalUsers": 0
        }
    
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
        display_name = user_id[:8] + "..." if len(str(user_id)) > 8 else str(user_id)
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
        "topUsers": top_users,
        "metadata": {
            "generatedAt": datetime.now().isoformat(),
            "dataSource": "production"
        }
    }


# =============================================================================
# QUERY REWRITER METRICS (replaces A/B test)
# =============================================================================

def calculate_rewriter_metrics(raw_data):
    """Calculate query rewriter effectiveness metrics."""
    
    total = len(raw_data)
    if total == 0:
        return {"error": "No data"}
    
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
    rewritten_avg_results = round(sum(d.get('resultCount', 0) for d in rewritten) / len(rewritten), 1) if rewritten else 0
    passthrough_avg_results = round(sum(d.get('resultCount', 0) for d in passthrough) / len(passthrough), 1) if passthrough else 0
    
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
    
    top_entities = [{"entity": k, "count": v} for k, v in sorted(entity_counts.items(), key=lambda x: -x[1])[:10]]
    
    # Build rewritten queries list
    rewritten_queries = []
    for d in rewritten:
        telemetry = d.get('query_rewrite_telemetry', {})
        scores = d.get('evaluation_scores', {})
        rewritten_queries.append({
            "id": d.get('conversation_id', d.get('id', ''))[:8],
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
                "id": d.get('conversation_id', d.get('id', ''))[:8],
                "query": d.get('conversation', ''),
                "matchedEntities": d.get('query_rewrite_telemetry', {}).get('matched_entities', []),
                "wasRewritten": d.get('query_rewrite_telemetry', {}).get('expansion_count', 0) > 0,
                "timestamp": d.get('timestamp', '')
            })
    
    # Calculate average scores
    def avg_scores(docs):
        if not docs:
            return {"relevance": 0, "groundedness": 0, "completeness": 0}
        scores_list = [d.get('evaluation_scores', {}) for d in docs if d.get('evaluation_scores')]
        if not scores_list:
            return {"relevance": 0, "groundedness": 0, "completeness": 0}
        r = sum(s.get('relevance', 0) for s in scores_list) / len(scores_list)
        g = sum(s.get('groundedness', 0) for s in scores_list) / len(scores_list)
        c = sum(s.get('completeness', 0) for s in scores_list) / len(scores_list)
        return {"relevance": round(r, 2), "groundedness": round(g, 2), "completeness": round(c, 2)}
    
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
            "rewrittenAvgResults": rewritten_avg_results,
            "passthroughAvgResults": passthrough_avg_results
        },
        "latencyStats": {
            "min": round(min(latencies), 2) if latencies else 0,
            "max": round(max(latencies), 2) if latencies else 0,
            "avg": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "p95": round(sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else (latencies[0] if latencies else 0), 2),
            "target": 40
        },
        "qualityScores": {
            "rewritten": avg_scores(rewritten),
            "passthrough": avg_scores(passthrough)
        },
        "topEntities": top_entities,
        "rewrittenQueries": rewritten_queries[:50],  # Limit to 50 for UI
        "zeroResultQueries": zero_result_queries[:30],  # Limit to 30
        "metadata": {
            "generatedAt": datetime.now().isoformat(),
            "dataSource": "staging"
        }
    }


# =============================================================================
# FEEDBACK METRICS
# =============================================================================

def calculate_feedback_metrics(feedback_data, categorize=True):
    """Calculate feedback metrics and optionally categorize with AI."""
    
    if not feedback_data:
        return {"error": "No feedback data"}
    
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
    
    # Categorize feedback with AI (optional - can be slow)
    if categorize:
        print("Categorizing feedback with AI (this may take a moment)...")
        feedback_data = categorize_feedback_with_ai(feedback_data)
    
    # Category breakdown
    category_counts = defaultdict(int)
    for f in feedback_data:
        cat = f.get('category', 'Uncategorized')
        category_counts[cat] += 1
    
    category_breakdown = [{"category": k, "count": v} for k, v in sorted(category_counts.items(), key=lambda x: -x[1])]
    
    # Build feedback items list
    feedback_items = []
    for f in feedback_data:
        feedback_items.append({
            "id": f.get('id', '')[:12],
            "timestamp": f.get('timestamp', ''),
            "userName": f.get('userName', 'Anonymous'),
            "feedbackType": f.get('feedbackType', 'unknown'),
            "comment": f.get('comment', ''),
            "category": f.get('category', 'Uncategorized'),
            "conversationId": f.get('conversationId', '')[:12]
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
        "feedbackItems": feedback_items[:100],  # Limit to 100 for UI
        "metadata": {
            "generatedAt": datetime.now().isoformat(),
            "dataSource": "production",
            "aiCategorized": categorize
        }
    }


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("NEXUS DASHBOARD DATA PIPELINE")
    print("=" * 60)
    
    # Determine output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(script_dir, 'src')
    
    # Create src directory if it doesn't exist
    if not os.path.exists(src_dir):
        os.makedirs(src_dir)
    
    # -------------------------------------------------------------------------
    # 1. QUERY REWRITER METRICS (from Staging)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 40)
    print("1. QUERY REWRITER METRICS (Staging)")
    print("-" * 40)
    
    try:
        container_staging = connect_to_cosmos_staging()
        raw_rewriter_data = fetch_rewriter_queries(container_staging)
        
        # Score unscored queries
        scored = score_unscored_queries(raw_rewriter_data, container_staging)
        if scored > 0:
            print(f"Scored {scored} new queries")
            raw_rewriter_data = fetch_rewriter_queries(container_staging)
        
        # Calculate metrics
        rewriter_metrics = calculate_rewriter_metrics(raw_rewriter_data)
        
        # Save to src/data.json
        output_path = os.path.join(src_dir, 'data.json')
        with open(output_path, 'w') as f:
            json.dump(rewriter_metrics, f, indent=2)
        print(f"✓ Saved rewriter metrics to {output_path}")
        
    except Exception as e:
        print(f"✗ Error fetching rewriter data: {e}")
        rewriter_metrics = None
    
    # -------------------------------------------------------------------------
    # 2. ADOPTION METRICS (from Production)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 40)
    print("2. ADOPTION METRICS (Production)")
    print("-" * 40)
    
    try:
        container_prod = connect_to_cosmos_prod()
        raw_adoption_data = fetch_all_queries_for_adoption(container_prod)
        
        # Calculate metrics
        adoption_metrics = calculate_adoption_metrics(raw_adoption_data)
        
        # Save to src/adoption.json
        output_path = os.path.join(src_dir, 'adoption.json')
        with open(output_path, 'w') as f:
            json.dump(adoption_metrics, f, indent=2)
        print(f"✓ Saved adoption metrics to {output_path}")
        
    except Exception as e:
        print(f"✗ Error fetching adoption data: {e}")
        adoption_metrics = None
    
    # -------------------------------------------------------------------------
    # 3. FEEDBACK METRICS (from Production)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 40)
    print("3. FEEDBACK METRICS (Production)")
    print("-" * 40)
    
    try:
        container_feedback = connect_to_cosmos_prod_feedback()
        raw_feedback_data = fetch_feedback(container_feedback)
        
        # Calculate metrics (set categorize=False for faster runs)
        feedback_metrics = calculate_feedback_metrics(raw_feedback_data, categorize=True)
        
        # Save to src/feedback.json
        output_path = os.path.join(src_dir, 'feedback.json')
        with open(output_path, 'w') as f:
            json.dump(feedback_metrics, f, indent=2)
        print(f"✓ Saved feedback metrics to {output_path}")
        
    except Exception as e:
        print(f"✗ Error fetching feedback data: {e}")
        feedback_metrics = None
    
    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    
    # if rewriter_metrics:
    #     print(f"\nQuery Rewriter (src/data.json):")
    #     print(f"  Total Queries: {rewriter_metrics['summary']['totalQueries']}")
    #     print(f"  Rewritten: {rewriter_metrics['summary']['rewrittenCount']} ({rewriter_metrics['summary']['rewriteRate']}%)")
    #     print(f"  Pass-through: {rewriter_metrics['summary']['passthroughCount']}")
    #     print(f"  Avg Expansion: {rewriter_metrics['summary']['avgExpansionCount']} terms")
    
    # if adoption_metrics:
    #     print(f"\nAdoption (src/adoption.json):")
    #     print(f"  WAU: {adoption_metrics['wau']}")
    #     print(f"  MAU: {adoption_metrics['mau']}")
    #     print(f"  Stickiness: {adoption_metrics['stickiness']}%")
    #     print(f"  Total Users: {adoption_metrics['totalUsers']}")
    
    # if feedback_metrics:
    #     print(f"\nFeedback (src/feedback.json):")
    #     print(f"  Total: {feedback_metrics['summary']['total']}")
    #     print(f"  Thumbs Up: {feedback_metrics['summary']['thumbsUp']} ({feedback_metrics['summary']['positiveRate']}%)")
    #     print(f"  Thumbs Down: {feedback_metrics['summary']['thumbsDown']}")


if __name__ == "__main__":
    main()