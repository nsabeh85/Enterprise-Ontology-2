# 🔮 Nexus Ontology

**Intelligent Query Expansion & Analytics for Data Center RAG Systems**

A unified platform for ontology-aware query rewriting and real-time performance analytics.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Components](#components)
- [Configuration](#configuration)
- [Development](#development)
- [Architecture](#architecture)

---

## 🎯 Overview

The Nexus Ontology project solves a critical problem in RAG (Retrieval Augmented Generation) systems: **users use informal terminology that search engines don't understand**.

### The Problem

```
User: "Is SF available at DFW10?"
Search: ❌ No results (doesn't know SF = ServiceFabric, DFW10 = Dallas data center)
```

### The Solution

```
User: "Is SF available at DFW10?"
       ↓ Ontology Engine
Expanded: "ServiceFabric^1.0 OR DFW10^1.0 OR availability^1.0 OR SF^0.8..."
Search: ✅ 45 relevant documents found
```

---

## 📁 Project Structure

```
nexus-ontology/
├── README.md                    # This file
├── ARCHITECTURE.md              # System architecture documentation
├── CHANGELOG.md                 # Version history
├── requirements.txt             # Python dependencies
├── env.example                  # Environment variables template
├── .gitignore
│
├── engine/                      # 🔮 Query Rewriter Engine
│   ├── src/
│   │   ├── query_rewriter_v2_enhanced.py  # Main rewriter
│   │   ├── disambiguation_rules.py        # Ambiguity resolution
│   │   ├── performance_monitor.py         # Latency tracking
│   │   ├── telemetry_logger.py            # Query logging
│   │   └── build_runtime_artifact.py      # Lexicon compiler
│   ├── data/
│   │   ├── lexicon_v01_final.yaml         # Domain ontology
│   │   └── ontology_runtime.json          # Compiled runtime
│   ├── archive/                            # Legacy code
│   └── requirements.txt
│
├── dashboard/                   # 📊 Analytics Dashboard
│   ├── api/                     # FastAPI Backend
│   │   ├── main.py              # API entry point
│   │   ├── services/
│   │   │   ├── cosmos_client.py    # Database connections
│   │   │   ├── sync_service.py     # Data synchronization
│   │   │   └── metrics_service.py  # Aggregation logic
│   │   └── cache/
│   │       └── state.py            # In-memory cache
│   │
│   └── web/                     # React Frontend
│       ├── src/
│       │   ├── App.jsx
│       │   ├── components/
│       │   └── pages/
│       ├── package.json
│       ├── vite.config.js
│       └── tailwind.config.js
│
└── scripts/                     # 🛠️ Utility Scripts
    └── transform_to_dashboard.py   # Static data generator
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Azure Cosmos DB account
- Azure OpenAI resource (optional, for scoring)

### 1. Clone and Setup

```bash
cd nexus-ontology

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd dashboard/web
npm install
cd ../..

# Configure environment
cp env.example .env
# Edit .env with your Azure credentials
```

### 2. Run the Dashboard

**Terminal 1 - Start API:**
```bash
cd dashboard/api
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
cd dashboard/web
npm run dev
```

**Access:**
- 🌐 Dashboard: http://localhost:5173
- 📡 API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs

### 3. Test the Query Rewriter

```bash
cd engine/src
python query_rewriter_v2_enhanced.py
```

---

## 🧩 Components

### 🔮 Engine - Query Rewriter

The core query expansion module:

| Feature | Description |
|---------|-------------|
| **Entity Detection** | Matches terms from the domain ontology |
| **Query Expansion** | Adds synonyms (0.8 weight) and related terms (0.6 weight) |
| **Disambiguation** | Resolves ambiguous terms using context |
| **Performance** | < 5ms average, < 40ms p95 latency |
| **Telemetry** | Privacy-safe logging with hashed user IDs |

**Usage:**
```python
from query_rewriter_v2_enhanced import load_lexicon, rewrite_query

lexicon = load_lexicon('data/ontology_runtime.json')
result = rewrite_query("Is SF available at DFW10?", lexicon)

print(result['matched_entities'])  # ['ServiceFabric', 'DFW10', 'availability']
print(result['expansion_count'])   # 8
```

### 📊 Dashboard - Analytics

Real-time visibility into system performance:

| Page | Metrics |
|------|---------|
| **Overview** | High-level KPIs, summary stats |
| **Query Rewriter** | Entity matches, expansion rates, latency |
| **Adoption** | WAU, MAU, stickiness, query trends |
| **Feedback** | Thumbs up/down, categorized comments |
| **Content Health** | Zero-result queries, content gaps |

**API Endpoints:**
| Endpoint | Description |
|----------|-------------|
| `GET /api/rewriter` | Query rewriter metrics |
| `GET /api/adoption` | User adoption metrics |
| `GET /api/feedback` | Feedback analysis |
| `GET /api/status` | Sync status and health |
| `POST /api/sync` | Trigger data sync |

---

## ⚙️ Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

```env
# Cosmos DB - Staging (Query Rewriter Data)
COSMOS_ENDPOINT=https://your-staging.documents.azure.com:443/
COSMOS_KEY=your-staging-key

# Cosmos DB - Production (Adoption & Feedback)
COSMOS_PROD_ENDPOINT=https://your-prod.documents.azure.com:443/
COSMOS_PROD_KEY=your-prod-key

# Azure OpenAI (for scoring)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
```

### Lexicon Configuration

Edit `engine/data/lexicon_v01_final.yaml` to add/modify entities:

```yaml
products:
  - canonical: ServiceFabric
    synonyms: [SF, Service Fabric]
    related_terms: [Metro Connect, Megaport]
    
facilities:
  - canonical: DFW10
    market: Dallas
    synonyms: [Dallas site, 2323 Bryan Street]
```

Then rebuild the runtime:
```bash
cd engine/src
python build_runtime_artifact.py
```

---

## 🔧 Development

### Running Tests

```bash
# Test query rewriter
cd engine/src
python query_rewriter_v2_enhanced.py

# Test API
cd dashboard/api
uvicorn main:app --reload --port 8000
curl http://localhost:8000/api/status
```

### Building for Production

```bash
# Build frontend
cd dashboard/web
npm run build
# Output in dashboard/web/dist/
```

### Generating Static Data

If you need to run the dashboard without the API:

```bash
cd scripts
python transform_to_dashboard.py
# Generates JSON files in dashboard/web/src/
```

---

## 🏗️ Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system documentation including:

- Component diagrams
- Data flow diagrams
- Database schema
- API contracts
- Deployment architecture
- Security considerations

---

## 📊 Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Query rewrite latency (p95) | < 40ms | ~5ms ✅ |
| Dashboard API response | < 200ms | ~50ms ✅ |
| Rewrite rate | > 50% | 56.4% ✅ |
| Zero-result rate (rewritten) | < 10% | 8.8% ✅ |

---

## 📄 License

Internal use only - Digital Realty Trust, Inc.

---

## 🤝 Contributing

1. Create a feature branch
2. Make changes
3. Test thoroughly
4. Submit for code review

See [CHANGELOG.md](./CHANGELOG.md) for version history.

