<<<<<<< HEAD
# newsapi

## Getting started

### Installing dependencies

**Option 1: uv**

Ensure [`uv`](https://docs.astral.sh/uv/) is installed following their [official documentation](https://docs.astral.sh/uv/getting-started/installation/).

Create a virtual environment, and install the required dependencies using _sync_:

```bash
uv sync
```

Then, activate the virtual environment:

| OS | Command |
| --- | --- |
| MacOS | ```source .venv/bin/activate``` |
| Windows | ```.venv\Scripts\activate``` |

**Option 2: pip**

Install the python dependencies with [pip](https://pypi.org/project/pip/):

```bash
python3 -m venv .venv
```

Then activate the virtual environment:

| OS | Command |
| --- | --- |
| MacOS | ```source .venv/bin/activate``` |
| Windows | ```.venv\Scripts\activate``` |

Install the required dependencies:

```bash
pip install -e ".[dev]"
```

### Running Dagster

Start the Dagster UI web server:

```bash
dg dev
```

Open http://localhost:3000 in your browser to see the project.

## Learn more

To learn more about this template and Dagster in general:

- [Dagster Documentation](https://docs.dagster.io/)
- [Dagster University](https://courses.dagster.io/)
- [Dagster Slack Community](https://dagster.io/slack)
=======
# AI & Marketing News Pipeline

An automated data engineering pipeline that fetches, processes, and stores news articles about **Artificial Intelligence** and **Marketing** using Dagster orchestration and EventRegistry API.

## 📋 Project Overview

This project implements a production-ready ETL pipeline that:

- 🔄 **Automatically fetches** news articles combining AI and Marketing topics every 6 hours
- 🧹 **Processes and cleans** data through multi-stage filtering and deduplication
- 💾 **Stores** data in scalable databases (DuckDB for dev, PostgreSQL for production)
- 📊 **Monitors** pipeline health with automated failure alerts
- ☁️ **Deploys** to Azure with containerized services

Built for the **Dentsu data engineering case study**, this project demonstrates modern data engineering practices including orchestration, testing, security, and cloud deployment.

---

## 🏗️ Architecture

The pipeline consists of three main stages:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Raw News       │────▶│  Processed News  │────▶│  Filtered News   │
│  (Extraction)    │     │  (Deduplication) │     │  (Validation)    │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
    Every 6h                  Every 6h15              Every 6h15
  (Schedules)               (Schedules)             (Schedules)
```

### Key Components

- **[assets.py](src/newsapi_dentsu/defs/assets.py)**: ETL pipeline logic (fetch, process, filter)
- **[schedules.py](src/newsapi_dentsu/defs/schedules.py)**: Automated cron schedules for execution
- **[sensors.py](src/newsapi_dentsu/defs/sensors.py)**: Failure detection and alerting system
- **[resources.py](src/newsapi_dentsu/defs/resources.py)**: Database configuration (DuckDB/PostgreSQL)

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Orchestration** | Dagster 1.12.6 | Asset-based pipeline management |
| **Data Processing** | Pandas | DataFrame transformations |
| **Local Database** | DuckDB | Development storage (file-based) |
| **Production Database** | PostgreSQL | Scalable cloud storage (Azure Database) |
| **Data Source** | EventRegistry API | News article provider |
| **Testing** | pytest | Unit and integration tests |
| **Containerization** | Docker | Deployment packaging |
| **Cloud Platform** | Azure | Container Apps, Azure Database, Monitor, Blob Storage |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10-3.13
- EventRegistry API key ([sign up here](https://newsapi.ai/))
- (Optional) PostgreSQL for production mode

### Installation

#### Option 1: Using `uv` (recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/newsapi-dentsu.git
cd newsapi-dentsu

# Install dependencies with uv
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

#### Option 2: Using `pip`

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -e ".[dev]"
```

### Configuration

1. **Copy environment template**:

   ```bash
   cp .env.example .env
   ```

2. **Add your API key** to `.env`:

   ```bash
   NEWSAPI_KEY=your_eventregistry_api_key_here
   USE_POSTGRES=false  # Use DuckDB for local development
   ```

3. **Verify configuration**:

   ```bash
   # Check that .env is not tracked by git
   git status  # Should not show .env file
   ```

---

## 💻 Running the Pipeline

### Start Dagster UI

```bash
dagster dev
```

Open <http://localhost:3000> to access the Dagster web interface.

### Manual Execution

In the Dagster UI:

1. Navigate to **Assets** tab
2. Select assets to materialize:
   - `raw/ai_marketing_news_raw` - Fetch news from API
   - `processed/processed_news` - Deduplicate articles
   - `final/filtered_news` - Filter and clean data
3. Click **Materialize** to run

### Scheduled Execution

The pipeline runs automatically:

- **Raw data fetch**: Every 6 hours (00:00, 06:00, 12:00, 18:00)
- **Processing & filtering**: 15 minutes after raw fetch

View schedules in the **Schedules** tab.

### Monitoring

- **Pipeline Sensors**: Check hourly for failures and send alerts
- **Logs**: View real-time execution logs in the Dagster UI
- **Metadata**: See article counts, duplicates removed, date ranges per run

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Files

```bash
# Test asset functions
pytest tests/test_assets.py -v

# Test with coverage report
pytest tests/ --cov=newsapi_dentsu --cov-report=html
```

### Test Structure

- **`tests/conftest.py`**: Pytest fixtures (mock data, Dagster context)
- **`tests/test_assets.py`**: Unit tests for filtering, deduplication, date parsing
- **`tests/fixtures/sample_news.json`**: Test data with valid/invalid articles

---

## 🗄️ Database Configuration

### Local Development (DuckDB)

**Default setup** - no configuration needed:

```bash
# .env
USE_POSTGRES=false
```

Data stored in `data/news.duckdb` (automatically created).

### Production (PostgreSQL)

1. **Set up PostgreSQL** (Azure Database, local instance, or Docker):

   ```bash
   # Using docker-compose (see docker-compose.yml)
   docker-compose up -d postgres
   ```

2. **Configure environment**:

   ```bash
   # .env
   USE_POSTGRES=true
   POSTGRES_HOST=your-server.postgres.database.azure.com
   POSTGRES_PORT=5432
   POSTGRES_DB=newsapi_db
   POSTGRES_USER=dagster_user
   POSTGRES_PASSWORD=your_secure_password
   ```

3. **Run pipeline** - Dagster automatically creates schemas and tables

---

## 📦 Deployment

### Docker

Build and run with Docker:

```bash
# Build image
docker build -t newsapi-dagster:latest .

# Run webserver
docker run -p 3000:3000 \
  --env-file .env \
  newsapi-dagster:latest \
  dagster-webserver -h 0.0.0.0 -p 3000

# Run daemon (separate container)
docker run \
  --env-file .env \
  newsapi-dagster:latest \
  dagster-daemon run
```

### Docker Compose

```bash
# Start all services (Dagster + PostgreSQL)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Azure Production Deployment

- Container Apps environment setup
- Azure Database for PostgreSQL configuration
- Azure Monitor monitoring and alerting
- VNet networking and Network Security Groups
- Cost estimation (~$335/month)
- CI/CD pipeline with GitHub Actions

Quick deploy:

```bash
# 1. Build and push to ACR
az acr login --name <ACR_NAME>
docker build -t newsapi-dagster:latest .
docker tag newsapi-dagster:latest <ACR_NAME>.azurecr.io/newsapi-dagster:latest
docker push <ACR_NAME>.azurecr.io/newsapi-dagster:latest

# 2. Update Container App
az containerapp update \
  --name dagster-webserver \
  --resource-group newsapi-rg \
  --image <ACR_NAME>.azurecr.io/newsapi-dagster:latest
```

---

## 📊 Data Flow

### 1. Raw News Extraction

**Asset**: `raw/ai_marketing_news_raw`  
**Source**: EventRegistry API (newsapi.ai)  
**Logic**:

- Queries articles with BOTH AI and Marketing categories
- Incremental loading (fetches only new articles since last run)
- English language only
- Max 100 articles per run

**Output Schema**:

```
- title: Article headline
- url: Article URL (unique identifier)
- body: Full article content
- dateTime: Publication timestamp
- source: Source name and URI
- fetched_at: Pipeline execution timestamp
```

### 2. Processed News (Deduplication)

**Asset**: `processed/processed_news`  
**Logic**:

- Removes duplicate articles by URL
- Keeps first occurrence
- Logs duplicate count

**Metadata**:

- `total_articles`: Count after deduplication
- `duplicates_removed`: Number of duplicates found
- `date_range`: Min and max publication dates

### 3. Filtered News (Validation)

**Asset**: `final/filtered_news`  
**Logic**:

- Removes articles without title or body
- Filters out `[Removed]` content
- Validates and parses publication dates
- Sorts by publication date (newest first)

**Metadata**:

- `total_articles`: Final article count
- `removed_articles`: Articles filtered out
- `preview`: Top 10 articles with titles and dates

---

## 🚨 Monitoring and Alerts

### Dagster Sensors

Two sensors run every hour to detect failures:

1. **`pipeline_failure_alert_sensor`**:
   - Monitors all pipeline runs for failures
   - Batches failures within 1-hour window
   - Sends notifications via email/Slack (see pseudocode in [sensors.py](src/newsapi_dentsu/defs/sensors.py))

2. **`asset_materialization_failure_sensor`**:
   - Monitors specific assets: `raw_news`, `processed_news`, `final_news`
   - Provides granular failure tracking
   - Logs asset-specific metrics

### Alert Configuration

Edit `.env` to configure alert notifications:

```bash
# Email alerts (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@example.com
EMAIL_PASSWORD=your_app_password
ALERT_EMAIL_TO=team@yourcompany.com

# Or Slack webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 📁 Project Structure

```
newsapi-dentsu/
├── src/
│   └── newsapi_dentsu/
│       ├── __init__.py
│       ├── definitions.py          # Main Dagster definitions
│       └── defs/
│           ├── assets.py           # ETL pipeline assets
│           ├── resources.py        # Database configuration
│           ├── schedules.py        # Cron schedules
│           └── sensors.py          # Failure monitoring
├── tests/
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_assets.py              # Asset unit tests
│   └── fixtures/
│       └── sample_news.json        # Test data
├── data/
│   └── news.duckdb                 # Local database
├── notebooks/
│   ├── inspect.ipynb               # Analyze data in db
│   └── test.ipynb                  # Exploratory analysis
├── .env.example                    # Environment template
├── .gitignore                      # Git exclusions
├── pyproject.toml                  # Dependencies
├── Dockerfile                      # Container image
├── docker-compose.yml              # Local multi-service setup
└── README.md                       # This file
```

---

## 🔧 Development

### Adding New Assets

1. Define asset in `src/newsapi_dentsu/defs/assets.py`:

   ```python
   @dg.asset(group_name="my_group", key_prefix=["schema"])
   def my_new_asset(context: dg.AssetExecutionContext) -> pd.DataFrame:
       # Your logic here
       return df
   ```

2. Add tests in `tests/test_assets.py`

3. Update schedules if needed in `schedules.py`

### Database Schema

The I/O manager automatically creates schemas based on `key_prefix`:

- `raw.*` → `raw` schema
- `raw.*` → `processed` schema
- `raw.*` → `final` schema

View schemas:

```bash
# DuckDB
duckdb data/news.duckdb "SHOW TABLES;"

# PostgreSQL
psql -h localhost -U dagster_user -d newsapi_db -c "\dt raw.*"
```
>>>>>>> master
