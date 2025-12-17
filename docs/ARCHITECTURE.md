# Production Architecture Design

This document outlines the production deployment architecture for the AI & Marketing News Pipeline, designed for scalability, reliability, and maintainability on Azure.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Component Details](#component-details)
- [Database Migration Strategy](#database-migration-strategy)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Scalability and Performance](#scalability-and-performance)
- [Cost Estimation](#cost-estimation)
- [Deployment Process](#deployment-process)

---

## System Overview

The News Pipeline is built on **Dagster** for orchestration, **PostgreSQL** for data storage, and **Azure** for cloud infrastructure. The system fetches news articles about AI and Marketing from the EventRegistry API, processes them through a multi-stage ETL pipeline, and stores cleaned data for consumption by downstream applications.

### Key Features

- **Automated Data Collection**: Scheduled fetching every 6 hours
- **Incremental Loading**: Only fetches new articles since last run
- **Data Quality**: Multi-stage filtering and deduplication
- **Monitoring**: Hourly failure alerts via email/Slack
- **Scalability**: Horizontally scalable on Azure Container Apps
- **Reliability**: Automatic retries and error handling

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AZURE CLOUD (VNet)                                │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         PUBLIC SUBNET                                  │ │
│  │                                                                        │ │
│  │  ┌─────────────────── ───┐         ┌─────────────────────┐             │ │
│  │  │  Application Gateway  │         │   Bastion Host      │             │ │
│  │  │  or Front Door        │         │   (SSH Access)      │             │ │
│  │  │  :443 (HTTPS)         │         └─────────────────────┘             │ │
│  │  └──────────┬────────────┘                                             │ │
│  └─────────────┼──────────────────────────────────────────────────────────┘ │
│                │                                                            │
│  ┌─────────────┼──────────────────────────────────────────────────────────┐ │
│  │             │              PRIVATE SUBNET (App Tier)                   │ │
│  │             ↓                                                          │ │
│  │  ┌──────────────────────┐         ┌─────────────────────┐              │ │
│  │  │  Container Apps Env  │         │   Container Apps    │              │ │
│  │  │  ┌─────────────────┐ │         │  ┌────────────────┐ │              │ │
│  │  │  │ Dagster Web     │ │         │  │ Dagster Daemon │ │              │ │
│  │  │  │ Server          │ │         │  │ (Run Launcher) │ │              │ │
│  │  │  │ Port: 3000      │ │         │  │                │ │              │ │
│  │  │  │ Replicas: 2-4   │ │         │  │ Replicas: 1-2  │ │              │ │
│  │  │  └─────────────────┘ │         │  └────────────────┘ │              │ │
│  │  └──────────┬───────────┘         └──────────┬──────────┘              │ │
│  └─────────────┼────────────────────────────────┼─────────────────────────┘ │
│                │                                │                           │
│  ┌─────────────┼────────────────────────────────┼─────────────────────────┐ │
│  │             │     PRIVATE SUBNET (Data Tier) │                         │ │
│  │             ↓                                ↓                         │ │
│  │  ┌──────────────────────────────────────────────────────────────┐      │ │
│  │  │  Azure Database for PostgreSQL (Zone-Redundant)             │      │ │
│  │  │  ┌────────────────────┐    ┌────────────────────┐            │      │ │
│  │  │  │  Primary Instance  │    │  Standby Replica   │            │      │ │
│  │  │  │  General Purpose   │───▶│  (Failover)        │            │      │ │
│  │  │  │  2 vCore, 8GB RAM  │    │                    │            │      │ │
│  │  │  │  Storage: 128 GB   │    │                    │            │      │ │
│  │  │  └────────────────────┘    └────────────────────┘            │      │ │
│  │  └──────────────────────────────────────────────────────────────┘      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────── ─────────────┐  │
│  │                    AZURE SERVICES (External)                          │  │
│  │                                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │  │
│  │  │ Azure Monitor│  │ Key Vault    │  │ Blob Storage │                 │  │
│  │  │ Logs & Metrics│ │ (Secrets)    │  │ (Backups)    │                 │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                 │  │
│  │                                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │  │
│  │  │ Event Grid   │  │ Container    │  │ Azure Monitor│                 │  │
│  │  │ (Alerts)     │  │ Registry     │  │ Alerts       │                 │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
                     ┌──────────────────────────────┐
                     │  External API                │
                     │  newsapi.ai (EventRegistry)  │
                     │  Port: 443 (HTTPS)           │
                     └──────────────────────────────┘
```

---

## Component Details

### 1. Application Layer (Azure Container Apps)

#### Dagster Web Server

- **Purpose**: Provides UI for pipeline monitoring, debugging, and manual runs
- **Container Image**: Custom Docker image with Dagster + pipeline code
- **Resource**: 1 vCPU, 2 GB RAM per replica
- **Scaling**: 2-4 replicas behind Application Gateway for high availability
- **Port**: 3000 (internal), exposed via Application Gateway on 443 (HTTPS)
- **Health Check**: `/server_info` endpoint

#### Dagster Daemon

- **Purpose**: Executes scheduled runs, manages run queue, sensor evaluations
- **Container Image**: Same as web server
- **Resource**: 2 vCPU, 4 GB RAM per replica
- **Scaling**: 1-2 replicas (active-standby for reliability)
- **Components**:
  - Schedule launcher (runs cron schedules)
  - Sensor evaluator (monitors failures)
  - Run coordinator (manages concurrency)

### 2. Database Layer (Azure Database for PostgreSQL)

#### PostgreSQL Configuration

- **SKU**: General Purpose, 2 vCores, 8 GB RAM
- **Storage**: 128 GB Premium SSD
- **Zone-Redundant HA**: Enabled for automatic failover
- **Backup**:
  - Automated daily backups (7-day retention)
  - Manual snapshots before major changes
- **Schemas**:
  - `raw`: Raw articles from API
  - `processed`: Deduplicated articles
  - `final`: Filtered and cleaned articles
  - `dagster`: Dagster metadata (runs, assets, logs)

#### Database Migration from DuckDB

See [Database Migration Strategy](#database-migration-strategy) section below.

### 3. Networking

#### Virtual Network (VNet) Configuration

- **Address Space**: 10.0.0.0/16
- **Subnets**:
  - Public Subnet (10.0.1.0/24, 10.0.2.0/24): Application Gateway, Bastion
  - Private Subnet (10.0.10.0/24, 10.0.11.0/24): Container Apps
  - Private Subnet (10.0.20.0/24, 10.0.21.0/24): Database
- **NAT Gateway**: For private subnet internet access (API calls)
- **Virtual Network Gateway**: For VPN access

#### Network Security Groups (NSGs)

- **Application Gateway NSG**: Inbound 443 from 0.0.0.0/0
- **Container Apps NSG**: Inbound 3000 from Application Gateway subnet
- **Database NSG**: Inbound 5432 from Container Apps subnet
- **Bastion NSG**: Inbound 22 from company IP ranges

### 4. Storage and Backups

#### Azure Blob Storage

- **Purpose**:
  - Database exports/backups
  - Logs archival
  - Asset metadata (optional)
- **Lifecycle**: Transition to Cool tier after 30 days, Archive tier after 90 days
- **Encryption**: AES-256 (Microsoft-managed keys)

#### Azure Monitor Logs

- **Retention**: 30 days for application logs
- **Log Analytics Workspaces**:
  - `containerapp-dagster-webserver`
  - `containerapp-dagster-daemon`
  - `postgresql-newsapi-db`

### 5. Secrets Management

#### Azure Key Vault

- **Secrets Stored**:
  - `newsapi-api-key`: EventRegistry API key
  - `newsapi-postgres-credentials`: DB username/password
  - `newsapi-email-credentials`: SMTP credentials for alerts
- **Rotation**: API keys rotated every 90 days
- **Access**: Granted via Managed Identity to Container Apps only

### 6. Monitoring and Alerting

#### Azure Monitor Metrics

- **Container Apps Metrics**:
  - CPU Utilization (alert if >80% for 5 min)
  - Memory Utilization (alert if >85% for 5 min)
  - Replica Count (alert if <1 for daemon)
- **PostgreSQL Metrics**:
  - Active Connections (alert if >80% of max)
  - CPU Percent (alert if >80%)
  - Storage Percent (alert if >90%)

#### Azure Monitor Alerts → Event Grid

- **Critical Alerts**: PagerDuty integration
- **Warning Alerts**: Email to team via Action Groups
- **Info Alerts**: Slack channel via Logic Apps

#### Application-Level Alerts (Dagster Sensors)

- **Pipeline Failure Sensor**: Runs every hour
- **Notification Channels**: Email (SMTP) or Slack webhook
- **Alert Content**: Run ID, failure count, timestamp, error preview

---

## Database Migration Strategy

### DuckDB to PostgreSQL Migration

#### Why Migrate?

- **DuckDB** (current): File-based, great for local development
- **PostgreSQL** (production): Client-server, supports concurrent access, better for cloud

#### Migration Approach

##### Option 1: CSV Export/Import (Simplest)

```bash
# 1. Export data from DuckDB to CSV
duckdb data/news.duckdb << EOF
COPY (SELECT * FROM raw.ai_marketing_news_raw) TO 'export_raw.csv' (HEADER, DELIMITER ',');
COPY (SELECT * FROM processed.processed_news) TO 'export_processed.csv' (HEADER, DELIMITER ',');
COPY (SELECT * FROM final.filtered_news) TO 'export_final.csv' (HEADER, DELIMITER ',');
EOF

# 2. Create schemas in Azure PostgreSQL
psql "host=<SERVER>.postgres.database.azure.com port=5432 dbname=newsapi_db user=dagster_user password=<PASSWORD> sslmode=require" << EOF
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS processed;
CREATE SCHEMA IF NOT EXISTS final;
EOF

# 3. Import into PostgreSQL using Dagster I/O manager
# Set USE_POSTGRES=true in .env and run a manual materialization
# Or use psql COPY command:
psql "host=<SERVER>.postgres.database.azure.com port=5432 dbname=newsapi_db user=dagster_user password=<PASSWORD> sslmode=require" << EOF
\COPY raw.ai_marketing_news_raw FROM 'export_raw.csv' CSV HEADER;
\COPY processed.processed_news FROM 'export_processed.csv' CSV HEADER;
\COPY final.filtered_news FROM 'export_final.csv' CSV HEADER;
EOF
```

##### Option 2: Direct Python Migration Script

```python
# migration_script.py (pseudocode)
import duckdb
import psycopg2
import pandas as pd

# Connect to DuckDB
duckdb_conn = duckdb.connect('data/news.duckdb')

# Connect to PostgreSQL
pg_conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD')
)

# Tables to migrate
tables = [
    ('raw', 'ai_marketing_news_raw'),
    ('processed', 'processed_news'),
    ('final', 'filtered_news')
]

for schema, table in tables:
    print(f"Migrating {schema}.{table}...")
    
    # Read from DuckDB
    df = duckdb_conn.execute(f"SELECT * FROM {schema}.{table}").fetchdf()
    
    # Write to PostgreSQL
    df.to_sql(
        name=table,
        schema=schema,
        con=pg_conn,
        if_exists='replace',
        index=False,
        method='multi',  # Batch insert for performance
        chunksize=1000
    )
    
    print(f"Migrated {len(df)} rows")

print("Migration complete!")
```

##### Option 3: Start Fresh (Recommended for MVP)

Since the pipeline supports incremental loading:

1. **Deploy to production** with PostgreSQL configured
2. **Run initial load** with a 30-day lookback window
3. **Let scheduled runs** handle ongoing data collection
4. **No data loss** since API provides historical data

```bash
# Set environment for production
export USE_POSTGRES=true
export POSTGRES_HOST=your-server.postgres.database.azure.com
export POSTGRES_DB=newsapi_db
export POSTGRES_USER=dagster_user
export POSTGRES_PASSWORD=<from_key_vault>

# Launch Dagster and trigger initial load
dagster asset materialize -m newsapi_dentsu.definitions --select "raw/*"
```

#### Schema Compatibility

Both DuckDB and PostgreSQL use similar SQL dialects. The Dagster I/O Manager handles schema creation automatically:

- **Column Types**: Mapped automatically by pandas
- **Indexes**: Consider adding indexes on `url` (deduplication) and `publishedAt` (sorting)
- **Constraints**: Add UNIQUE constraint on `url` for data integrity

```sql
-- Recommended indexes for PostgreSQL
CREATE INDEX idx_raw_published ON raw.ai_marketing_news_raw(publishedAt);
CREATE INDEX idx_raw_url ON raw.ai_marketing_news_raw(url);
CREATE UNIQUE INDEX idx_processed_url ON processed.processed_news(url);
CREATE INDEX idx_final_published ON final.filtered_news(publishedAt DESC);
```

---

## Monitoring and Alerting

### Azure Monitor Dashboards

#### Pipeline Health Dashboard

- **Metrics**:
  - Successful runs per day
  - Failed runs per day
  - Average run duration
  - Articles fetched per run
  - Duplicates removed per run
- **Visualization**: Line charts, gauges

#### Infrastructure Health Dashboard

- **Metrics**:
  - Container Apps replica CPU/memory
  - PostgreSQL connections and queries
  - Application Gateway request count and latency
  - NAT Gateway bandwidth
- **Visualization**: Stacked area charts

### Alert Rules

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Pipeline Failure | >3 failures in 1 hour | High | Page on-call, email team |
| High Error Rate | >10% runs fail in 24h | Medium | Email team |
| Database Full | <10 GB free space | High | Page on-call, expand storage |
| High Latency | API response >5s avg | Medium | Email team |
| No Data Fetched | 0 articles in last 3 runs | Medium | Investigate API |
| ECS Task Down | Daemon task count <1 | Critical | Page on-call |

### Log Aggregation

- **Centralized Logging**: All Container Apps logs → Azure Monitor Logs
- **Structured Logging**: JSON format for easy parsing
- **Log Queries**: Kusto Query Language (KQL) for debugging
- **Retention**: 30 days hot, archive to Blob Storage for compliance

---

## Scalability and Performance

### Horizontal Scaling

#### Auto-Scaling Rules

**Dagster Web Server**:

- Scale out when CPU >70% for 3 minutes
- Scale in when CPU <30% for 10 minutes
- Min replicas: 2, Max replicas: 4

**Dagster Daemon**:

- Fixed 1 replica (no auto-scaling)
- Manual scaling if run queue grows

#### Database Scaling

**Vertical Scaling** (if needed):

- General Purpose 2 vCore → 4 vCore (8 GB → 16 GB RAM)
- Zero downtime with Zone-Redundant HA

**Read Replicas** (future):

- Create read replica for analytics queries
- Route BI tools to replica

### Performance Optimization

1. **Batch Processing**: Fetch up to 100 articles per run (API limit)
2. **Incremental Loading**: Only fetch new articles since last run
3. **Efficient Deduplication**: Use pandas drop_duplicates (fast)
4. **Database Indexes**: On frequently queried columns
5. **Connection Pooling**: Dagster manages PostgreSQL connections

### Data Volume Projections

Assuming 50 new AI+Marketing articles per day:

- **Daily**: 50 articles × 5 KB avg = 250 KB
- **Monthly**: 1,500 articles = 7.5 MB
- **Yearly**: 18,000 articles = 90 MB
- **5 Years**: 90,000 articles = 450 MB

**Conclusion**: Storage is not a bottleneck. Azure Database 128 GB provides ample room.

---

## Cost Estimation

### Monthly Azure Costs (East US Region)

| Service | Configuration | Monthly Cost |
|---------|---------------|-------------|
| **Azure Container Apps** | 3 replicas × 1 vCPU × 2 GB × 730h | $75 |
| **Azure Database for PostgreSQL** | General Purpose 2vCore Zone-Redundant | $135 |
| **PostgreSQL Storage** | 128 GB Premium SSD | $26 |
| **Application Gateway** | Standard v2 + 100 GB data | $35 |
| **NAT Gateway** | 1 NAT + 10 GB data | $35 |
| **Azure Monitor** | Logs (10 GB) + Metrics | $18 |
| **Key Vault** | 3 secrets + transactions | $0.15 |
| **Blob Storage** | 50 GB LRS + requests | $2 |
| **Data Transfer** | 100 GB outbound | $9 |
| **Total** | | **~$335/month** |

### Cost Optimization Strategies

1. **Reserved Capacity**: Save 30-40% on Database and Container Apps with 1-year commitment
2. **Spot Containers**: Not recommended for daemon (needs reliability)
3. **Right-Sizing**: Start with smaller instances, monitor and adjust
4. **Blob Storage Lifecycle**: Move old backups to Archive tier ($0.99/TB/month)
5. **Azure Monitor Insights**: Only enable for debugging (pay per query)

---

## Deployment Process

### CI/CD Pipeline (GitHub Actions with Azure)

```yaml
# .github/workflows/deploy.yml (simplified)

name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest tests/ -v

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      - name: Build and push Docker image
        run: |
          docker build -t newsapi-dagster:${{ github.sha }} .
          az acr login --name <ACR_NAME>
          docker tag newsapi-dagster:${{ github.sha }} <ACR_NAME>.azurecr.io/newsapi-dagster:latest
          docker push <ACR_NAME>.azurecr.io/newsapi-dagster:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Update Container Apps
        run: |
          az containerapp update \
            --name dagster-webserver \
            --resource-group newsapi-rg \
            --image <ACR_NAME>.azurecr.io/newsapi-dagster:latest
          az containerapp update \
            --name dagster-daemon \
            --resource-group newsapi-rg \
            --image <ACR_NAME>.azurecr.io/newsapi-dagster:latest
```

### Manual Deployment Steps

1. **Build Docker Image**: `docker build -t newsapi-dagster:latest .`
2. **Push to ACR**: `docker push <ACR_NAME>.azurecr.io/newsapi-dagster:latest`
3. **Update Container App Revision**: Increment revision number
4. **Update Container App**: Force new deployment
5. **Monitor Deployment**: Check Azure Monitor logs for errors
6. **Verify**: Access Dagster UI via Application Gateway DNS

### Rollback Procedure

If deployment fails:

1. **Identify Last Good Revision**: Check Container App revision history
2. **Revert Container App**: `az containerapp revision activate --revision <revision-name>`
3. **Monitor**: Ensure old version runs successfully
4. **Post-Mortem**: Review logs and fix issue

---

## Security Best Practices

1. **Least Privilege Access**: Container Apps use Managed Identity for required resources only
2. **Encryption**:
   - Azure Database encrypted at rest (Microsoft-managed keys)
   - Application Gateway with TLS 1.2+ only
   - Blob Storage encryption enabled
3. **Network Isolation**: Private subnets for app and database
4. **Secrets Rotation**: Automate with Azure Key Vault
5. **Vulnerability Scanning**: ACR scans Docker images on push
6. **Audit Logging**: Activity Log for all Azure API calls

---

## Disaster Recovery

### RTO and RPO

- **RTO** (Recovery Time Objective): <1 hour
- **RPO** (Recovery Point Objective): <6 hours (time between runs)

### Backup Strategy

1. **Automated Database Backups**: Daily snapshots, 7-day retention
2. **Manual Snapshots**: Before major changes
3. **Blob Storage Backups**: Export final data weekly to Blob Storage
4. **Code Repository**: GitHub (version controlled)

### Recovery Procedure

**Scenario 1: Database Corruption**

1. Identify latest healthy snapshot
2. Restore Azure Database from snapshot (15-30 min)
3. Update Container Apps with new DB endpoint
4. Resume pipeline operations

**Scenario 2: Region Failure**

1. Restore database snapshot in secondary region (West US 2)
2. Deploy Docker image from ACR (geo-replicated)
3. Update DNS to point to new Application Gateway
4. Resume operations in new region

---

## Future Enhancements

1. **Multi-Region Deployment**: Active-passive for disaster recovery
2. **Read Replicas**: Separate analytics workloads
3. **Caching Layer**: Azure Cache for Redis for frequently accessed data
4. **GraphQL API**: Expose data to frontend applications
5. **Data Lake**: Archive raw data to Blob Storage for long-term analytics
6. **Machine Learning**: Add sentiment analysis pipeline using Azure ML

---

## Conclusion

This architecture provides a **production-ready, scalable, and cost-effective** solution for the AI & Marketing News Pipeline. It leverages Azure managed services to minimize operational overhead while maintaining high availability and reliability.

**Key Strengths**:

- ✅ Scalable: Auto-scaling for variable workloads
- ✅ Reliable: Zone-Redundant database, automatic failovers
- ✅ Secure: Encrypted data, private subnets, least-privilege access
- ✅ Observable: Comprehensive monitoring and alerting
- ✅ Cost-Effective: ~$335/month for production deployment

For questions or clarifications, please refer to [SECURITY.md](SECURITY.md) and [README.md](README.md).
