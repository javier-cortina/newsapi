# 20-Minute Presentation Script

## AI & Marketing News Pipeline - Dentsu Case Study Presentation

**Total Time**: 20 minutes presentation + 10 minutes Q&A  
**Presenter**: [Your Name]  
**Date**: December 16, 2025

---

## Presentation Outline

| Section | Duration | Content |
|---------|----------|---------|
| **1. Introduction & Problem Statement** | 2 min | Assignment overview, business context |
| **2. Technical Implementation** | 8 min | Pipeline walkthrough, code demo |
| **3. Testing & Quality** | 2 min | Test strategy, results |
| **4. Deployment Architecture** | 5 min | AWS design, scalability |
| **5. Monitoring & Security** | 2 min | Alerting, best practices |
| **6. Conclusion & Next Steps** | 1 min | Summary, future enhancements |
| **7. Q&A** | 10 min | Questions and answers |

---

## Detailed Script

### [0:00 - 2:00] Introduction & Problem Statement

**Slide 1: Title**

> "Good morning/afternoon. Today I'll present the AI & Marketing News Pipeline, developed as part of Dentsu's data engineering case study. This project demonstrates a production-ready ETL pipeline for aggregating and processing news articles that cover both Artificial Intelligence and Marketing topics."

**Slide 2: Assignment Requirements**

> "The assignment had four main components:
>
> 1. **Data Acquisition**: Build an automated system to fetch AI and Marketing news from the News API, with periodic updates and scalable storage.
>
> 2. **Pipeline Orchestration**: Design a complete ETL workflow with automated scheduling and monitoring.
>
> 3. **Deployment Architecture**: Propose a cloud deployment strategy for production use.
>
> 4. **Optional Enhancement**: Implement logging and alerting systems.
>
> I completed all requirements, including the optional alerting system."

**Slide 3: Business Context**

> "The business need is clear: Marketing professionals need personalized news feeds combining the latest AI innovations with marketing insights. This pipeline enables that by:
>
> - Collecting relevant articles automatically every 6 hours
> - Filtering and cleaning data for quality
> - Storing in a scalable database for downstream consumption
> - Monitoring pipeline health to ensure reliability"

---

### [2:00 - 10:00] Technical Implementation

**Slide 4: Technology Stack**

> "I chose a modern data engineering stack:
>
> - **Dagster** for orchestration - it provides asset-based pipelines with excellent observability
> - **EventRegistry API** (newsapi.ai) for data sourcing - superior to standard News API because it allows complex category queries
> - **DuckDB** for local development - file-based, zero-config
> - **PostgreSQL** for production - scalable, ACID-compliant
> - **pytest** for testing
> - **Azure** for cloud deployment
>
> This stack balances developer experience with production requirements."

**Slide 5: Pipeline Architecture (Diagram)**

> "The pipeline has three main stages:
>
> [SHOW DIAGRAM]
>
> 1. **Raw Data Extraction**: Fetch articles from EventRegistry API that match BOTH AI and Marketing categories. This uses their advanced query system to ensure relevance. The pipeline supports incremental loading - it only fetches new articles since the last run.
>
> 2. **Processing/Deduplication**: Remove duplicate articles by URL, keeping the first occurrence. This stage also tracks how many duplicates were found as a quality metric.
>
> 3. **Filtering/Validation**: Remove invalid articles - those without titles or content, with '[Removed]' text, or invalid dates. Results are sorted by publication date.
>
> All three stages run automatically on schedules."

**[SWITCH TO LIVE DEMO]**

**Slide 6: Live Demo - Dagster UI**

> "Let me show you the actual system running. [Open Dagster UI at localhost:3000]
>
> Here's the Dagster web interface. On the left, we have:
>
> - Assets: Our three pipeline stages
> - Schedules: The cron-based automation
> - Sensors: Failure monitoring
>
> Let's look at the asset lineage graph. [Click Assets tab] You can see the data flow:
>
> - `raw/ai_marketing_news_raw` fetches from API
> - `processed/processed_news` deduplicates
> - `final/filtered_news` validates and cleans
>
> Each asset has metadata. [Click on an asset] Here you can see:
>
> - Number of articles processed
> - Duplicates removed
> - Date range of articles
> - Preview of the data
>
> Let's trigger a manual run. [Click Materialize] Watch the execution... [Wait ~10 seconds] And it's complete. We fetched X articles, removed Y duplicates, and ended with Z clean articles."

**Slide 7: Code Walkthrough - assets.py**

> "Now let's look at the code. [Open assets.py]
>
> This is the core ETL logic. The `ai_marketing_news_raw` asset:
>
> ```python
> @dg.asset(group_name="raw_news", key_prefix=["raw"])
> def ai_marketing_news_raw(context):
>     # Get last fetch time for incremental loading
>     from_date = get_last_fetch_timestamp(context, ...)
>     
>     # Query EventRegistry for AI AND Marketing articles
>     q = QueryArticlesIter(
>         categoryUri=QueryItems.AND([
>             "dmoz/Computers/Artificial_Intelligence",
>             "dmoz/Business/Marketing_and_Advertising",
>         ]),
>         lang="eng",
>         dateStart=from_date,
>     )
>     
>     # Process and return DataFrame
>     return pd.DataFrame(articles)
> ```
>
> Key features:
>
> - Incremental loading checks the last materialization timestamp
> - Complex category queries ensure we get BOTH AI AND Marketing content
> - Error handling returns empty DataFrame on failure instead of crashing
> - Metadata logging for observability"

**Slide 8: Scheduling**

> "The pipeline runs automatically. [Open schedules.py or show Schedules tab]
>
> - **Raw data fetch**: Every 6 hours (00:00, 06:00, 12:00, 18:00) - respecting API rate limits
> - **Processing & filtering**: 15 minutes later (00:15, 06:15, 12:15, 18:15) - ensures raw data is available
>
> Both schedules are set to RUNNING by default, so the pipeline is fully automated once deployed."

---

### [10:00 - 12:00] Testing & Quality

**Slide 9: Test Strategy**

> "Quality assurance is critical for production systems. I implemented comprehensive pytest tests:
>
> 1. **Unit Tests**: Test each pipeline function in isolation
>    - Deduplication logic
>    - Filtering rules
>    - Date parsing
>    - Empty DataFrame handling
>
> 2. **Integration Tests**: Test the full pipeline flow with mixed valid/invalid data
>
> 3. **Fixture-Based Testing**: Realistic test data loaded from JSON
>
> Let me show the test results. [Run pytest in terminal]"

**[SWITCH TO TERMINAL]**

```bash
pytest tests/ -v
```

> "As you can see, all tests pass. We have:
>
> - 12 unit tests covering different scenarios
> - Tests for edge cases like invalid dates, missing content, duplicates
> - Integration tests simulating real-world data
>
> The tests run automatically in our CI/CD pipeline before deployment."

---

### [12:00 - 17:00] Deployment Architecture

**Slide 10: Production Architecture (Azure Diagram)**

> "For production deployment, I designed a scalable Azure architecture. [SHOW ARCHITECTURE DIAGRAM]
>
> The system consists of:
>
> **Application Layer** (Azure Container Apps):
>
> - Dagster Web Server (2-4 replicas) behind an Application Gateway for high availability
> - Dagster Daemon (1-2 replicas) for executing scheduled runs and sensors
> - Both run as Docker containers on Container Apps - serverless, no VM management
>
> **Data Layer** (Azure Database for PostgreSQL):
>
> - General Purpose 2 vCore instance with Zone-Redundant HA for automatic failover
> - 128 GB storage for several years of articles
> - Encrypted at rest, SSL/TLS connections required
> - Private subnet - no public internet access
>
> **Network Layer**:
>
> - VNet with public and private subnets across multiple availability zones
> - NAT Gateway for outbound API calls from private subnets
> - Network Security Groups restricting access (only Application Gateway can reach web server, only Container Apps can reach database)
>
> **Supporting Services**:
>
> - Azure Monitor for logging and metrics
> - Azure Key Vault for API keys and database credentials
> - Event Grid for email/Slack alerts
> - Blob Storage for backups and logs
> - Azure Container Registry for Docker image storage"

**Slide 11: Database Strategy**

> "The pipeline supports two database backends:
>
> **Development** (DuckDB):
>
> - File-based, zero configuration
> - Perfect for local testing
> - No separate database server needed
>
> **Production** (PostgreSQL):
>
> - Scalable, supports concurrent access
> - ACID compliance for data integrity
> - Managed service (RDS) with automatic backups and updates
>
> The system auto-detects which to use based on the `USE_POSTGRES` environment variable. This makes local development fast while maintaining production capabilities.
>
> For migrating existing DuckDB data to PostgreSQL, I documented three approaches in ARCHITECTURE.md:
>
> 1. CSV export/import (simplest)
> 2. Python migration script (automated)
> 3. Fresh start (recommended for initial deployment - just run the pipeline)"

**Slide 12: Scalability**

> "The architecture is designed to scale:
>
> **Horizontal Scaling**:
>
> - Web server: Auto-scale from 2 to 4 replicas based on CPU (>70% triggers scale-out)
> - Daemon: Fixed 1 replica (no need to scale)
>
> **Vertical Scaling**:
>
> - Database: Can upgrade from 2 vCore to 4 vCore with zero downtime (Zone-Redundant HA)
> - Add read replicas if needed for analytics workloads
>
> **Data Volume Projections**:
>
> - Current: ~50 articles/day = 250 KB/day
> - 5 years: ~90,000 articles = 450 MB
> - Conclusion: Storage is not a bottleneck. The 128 GB database provides ample room.
>
> **Cost**: Monthly Azure costs around $335 (detailed breakdown in ARCHITECTURE.md)"

---

### [17:00 - 19:00] Monitoring & Security

**Slide 13: Monitoring & Alerting**

> "Observability is crucial for production systems. I implemented two-layer monitoring:
>
> **Application-Level** (Dagster Sensors):
>
> - `pipeline_failure_sensor`: Runs hourly, batches failures to avoid alert fatigue
> - `asset_failure_sensor`: Monitors specific assets with granular tracking
> - Pseudocode provided for email (SMTP) and Slack webhook integrations
>
> [SHOW sensors.py code]
>
> **Infrastructure-Level** (Azure Monitor):
>
> - Container Apps replica CPU/memory alerts
> - Database connection and storage alerts
> - Custom metrics for articles fetched per run
> - Azure Monitor Logs with 30-day retention
>
> Alerts are sent via Event Grid to email or PagerDuty for critical failures."

**Slide 14: Security Best Practices**

> "Security is implemented at every layer:
>
> **Secrets Management**:
>
> - No credentials in code or version control
> - `.env` file is gitignored
> - Azure Key Vault for production (with automatic rotation)
> - Managed Identity with least-privilege access
>
> **Network Security**:
>
> - Database in private subnet (no public access)
> - Network Security Groups restrict traffic flow
> - SSL/TLS enforced everywhere
> - VNet flow logs for audit
>
> **Application Security**:
>
> - Input validation and sanitization
> - SQL injection prevention via parameterized queries (SQLAlchemy/pandas)
> - No sensitive data in error messages or logs
> - Container image scanning in ACR
>
> I documented all security practices in SECURITY.md including an incident response plan."

---

### [19:00 - 20:00] Conclusion & Next Steps

**Slide 15: Assignment Coverage**

> "Let's review how this project addresses all assignment requirements:
>
> ✅ **Requirement 1 - Data Acquisition**:
>
> - EventRegistry API integration
> - Automated fetching every 6 hours
> - Incremental loading
> - Scalable storage (DuckDB/PostgreSQL)
> - Data cleaning and filtering
>
> ✅ **Requirement 2 - Pipeline Orchestration**:
>
> - Complete ETL with Dagster
> - Scheduled execution
> - Asset lineage and metadata
> - Error handling and retries
> - Optional: Comprehensive logging and alerts (sensors)
>
> ✅ **Requirement 3 - Deployment Architecture**:
>
> - Full AWS production design
> - ECS/Fargate for compute
> - RDS PostgreSQL for data
> - CloudWatch monitoring
> - Docker containerization
> - CI/CD pipeline with GitHub Actions
>
> ✅ **Requirement 4 - Presentation**:
>
> - This 20-minute presentation
> - Live demo
> - Documentation (README, ARCHITECTURE, SECURITY)
> - Q&A preparation"

**Slide 16: Future Enhancements**

> "While the current system meets all requirements, here are potential enhancements:
>
> **Short-term**:
>
> - Implement actual SMTP email sending (currently pseudocode)
> - Add data quality metrics (freshness, completeness)
> - Create user-facing API endpoint for article access
>
> **Medium-term**:
>
> - Sentiment analysis pipeline using NLP models
> - Multi-language support (currently English only)
> - Advanced filtering (custom user preferences)
>
> **Long-term**:
>
> - Multi-region deployment for global availability
> - Data lake for long-term analytics (S3 + Athena)
> - Machine learning for article recommendations
> - GraphQL API for frontend integration"

**Slide 17: Thank You**

> "Thank you for your time. To summarize:
>
> - Built a production-ready ETL pipeline with Dagster
> - Automated data collection from EventRegistry API
> - Comprehensive testing with pytest
> - Scalable AWS deployment architecture
> - Security best practices and monitoring
> - Complete documentation for operations
>
> I'm happy to answer any questions about the implementation, architecture decisions, or deployment strategy."

---

## Q&A Preparation (10 Minutes)

### Expected Questions & Answers

#### Technical Implementation

**Q: Why did you choose EventRegistry over the standard News API?**

> "EventRegistry provides more advanced query capabilities. Specifically, it allows complex Boolean queries like 'AI AND Marketing' at the category level, which ensures higher-quality results. The standard News API only supports keyword search, which would require manual filtering of results that might mention AI and Marketing in unrelated contexts."

**Q: How does incremental loading work?**

> "Each asset materialization stores a `last_fetch_timestamp` in metadata. The next run queries this timestamp and only fetches articles published after that date. This prevents duplicate fetching and reduces API calls. If it's the first run (no previous timestamp), we default to fetching the last 7 days of articles."

**Q: What happens if the API is down or rate-limited?**

> "The pipeline has error handling that catches API failures and returns an empty DataFrame instead of crashing. Dagster automatically logs the error with full context. The next scheduled run will try again. For rate limiting, I configured the pipeline to fetch max 100 articles per run, with runs every 6 hours (400 articles/day), which is well within EventRegistry's free tier (1,000 articles/day)."

**Q: How do you handle duplicate articles across runs?**

> "The deduplication happens at two levels:
>
> 1. Within each run: Remove duplicates by URL before storing
> 2. Across runs: The database doesn't prevent duplicates across runs, but since we use incremental loading (only fetch new articles), we naturally avoid re-fetching the same content. If needed, we could add a UNIQUE constraint on the URL column in PostgreSQL."

#### Architecture & Deployment

**Q: Why Azure Container Apps instead of Azure Functions?**

> "Dagster requires long-running processes for both the web server (UI) and daemon (job execution). Azure Functions' timeout limits make it unsuitable for orchestration. Container Apps provides containerized compute without VM management, perfect for this use case. Additionally, Dagster's architecture assumes persistent processes for sensors and schedule evaluations."

**Q: How do you handle database migrations in production?**

> "For schema changes, I would use database migration tools like Alembic or Dagster's built-in migration support. For data migration from DuckDB to PostgreSQL, I documented three approaches:
>
> 1. CSV export/import (manual, simple)
> 2. Python migration script (automated)
> 3. Fresh start recommended for initial deployment since the API provides historical data
>
> The I/O manager handles schema creation automatically, so adding new assets doesn't require manual migration."

**Q: What's the disaster recovery strategy?**

> "The system has multiple recovery layers:
>
> 1. **Zone-Redundant HA**: Automatic failover within minutes
> 2. **Automated Backups**: Daily snapshots with 7-day retention
> 3. **Blob Storage Exports**: Weekly full data exports to Blob Storage
> 4. **RTO/RPO**: Recovery Time Objective <1 hour, Recovery Point Objective <6 hours (one pipeline cycle)
>
> For complete region failure, we'd restore the database snapshot in a secondary region and redeploy containers from ACR."
> 4. **RTO/RPO**: Recovery Time Objective <1 hour, Recovery Point Objective <6 hours (one pipeline cycle)
>
> For complete region failure, we'd restore the RDS snapshot in a secondary region and redeploy containers from ECR."

**Q: How much does this cost to run?**

> "Approximately $335/month on Azure:
>
> - $135 Azure Database for PostgreSQL Zone-Redundant
> - $75 Container Apps
> - $35 Application Gateway
> - $35 NAT Gateway
> - $26 PostgreSQL Storage
> - $29 other services (Azure Monitor, Blob Storage, etc.)
>
> This can be optimized by 30-40% with reserved capacity for Database and Container Apps and right-sizing resources after monitoring usage patterns."

#### Testing & Quality

**Q: What's your test coverage?**

> "I have 12 unit and integration tests covering the core pipeline logic. I didn't aim for 100% coverage since Dagster's framework code is already tested. I focused on:
>
> - Business logic (filtering rules, deduplication)
> - Edge cases (empty data, invalid dates, malformed input)
> - Integration scenarios (full pipeline with mixed data)
>
> In production, I'd add data quality tests using Great Expectations to validate schemas and data freshness."

**Q: How do you ensure data quality?**

> "Multi-level validation:
>
> 1. **At extraction**: API provides structured data with known schemas
> 2. **At processing**: Remove duplicates, validate required fields
> 3. **At filtering**: Comprehensive rules (no empty content, no '[Removed]', valid dates)
> 4. **Metadata tracking**: Every run logs counts, date ranges, error rates
> 5. **Alerts**: Sensors detect anomalies (0 articles fetched = API issue)
>
> Future enhancement: Add Great Expectations for automated data quality checks."

#### Security

**Q: How do you secure API keys?**

> "Multiple layers:
>
> 1. **Development**: `.env` file (gitignored, never committed)
> 2. **Production**: Azure Key Vault with encryption at rest
> 3. **Container Apps Integration**: Apps reference secrets by Key Vault URL using Managed Identity
> 4. **Rotation**: Documented 90-day rotation schedule
> 5. **Monitoring**: Activity Log logs all secret access
>
> The API key is never hardcoded, logged, or exposed in error messages."

**Q: What about GDPR compliance for user data?**

> "Good question. This pipeline only stores publicly available news article metadata - no personal information. However, if we added user preferences for personalized feeds, we'd implement:
>
> 1. Data minimization (store only necessary user data)
> 2. Right to deletion (API endpoint to remove user data)
> 3. Consent management (explicit opt-in)
> 4. Data retention policies (archive old data after 2 years)
> 5. Access logs for audit
>
> The current system complies with data protection principles by not collecting personal data."

#### Monitoring

**Q: Why hourly sensors instead of real-time alerting?**

> "This balances responsiveness with alert fatigue. Real-time alerts for every failure would be noisy, especially during API outages that cause multiple consecutive failures. Hourly batching:
>
> 1. Groups related failures (e.g., API outage affects multiple runs)
> 2. Reduces alert volume
> 3. Still provides timely notification (failures are caught within 60 minutes)
>
> For critical failures (database down, daemon crashed), CloudWatch alarms provide real-time alerts."

**Q: How do you know if articles are stale?**

> "Two mechanisms:
>
> 1. **Asset metadata**: Each run logs the date range of articles fetched. If the most recent article is >24 hours old, it indicates:
>    - API might not have fresh content
>    - Our categories might be too narrow
> 2. **Custom sensor**: Could add a sensor that checks `final_news` materialization and alerts if `published_at` max is >24h ago
>
> This would be a quick addition to the existing sensor framework."

---

## Presentation Tips

### Visual Aids

1. **Slides**: Keep text minimal, use diagrams and screenshots
2. **Live Demo**: Practice beforehand, have backup screenshots if demo fails
3. **Code**: Use syntax highlighting, show only relevant snippets
4. **Architecture Diagrams**: Use simple, clear layouts with legends

### Delivery Tips

- **Pace**: Speak slowly and clearly, pause for questions
- **Eye Contact**: Look at audience, not just slides
- **Enthusiasm**: Show passion for the technical solution
- **Confidence**: You built this - you know it better than anyone
- **Backup Plan**: Have screenshots in case live demo fails

### Demo Checklist

Before presentation:

- [ ] Dagster UI is running (`dagster dev`)
- [ ] Recent materialization to show in history
- [ ] `.env` configured with valid API key
- [ ] Test data in database to show results
- [ ] Terminal ready for pytest demo
- [ ] Browser tabs open: Dagster UI, GitHub repo, ARCHITECTURE.md, Azure Portal
- [ ] Code editor open to key files: assets.py, sensors.py, resources.py

### Time Management

- Set phone timer for each section
- If running over, skip "Future Enhancements" slide
- Save at least 10 minutes for Q&A
- If audience is engaged, extend Q&A, shorten technical details

---

## Additional Resources to Have Ready

1. **GitHub Repository**: Have it open to show:
   - Clean commit history
   - README.md
   - Project structure

2. **Documentation Files**: Quick access to:
   - ARCHITECTURE.md (for detailed deployment questions)
   - SECURITY.md (for security-related questions)
   - Test results (pytest output)

3. **Data Samples**: Show actual articles fetched:

   ```bash
   duckdb data/news.duckdb "SELECT title, source_name, publishedAt FROM final.filtered_news LIMIT 5;"
   ```

4. **Logs**: Recent Dagster run logs showing:
   - Successful execution
   - Articles fetched
   - Processing metrics

---

## Closing Statement

> "Thank you again. I'm proud of this solution because it's not just a proof of concept - it's production-ready. The code is tested, the architecture is scalable, security is built-in from day one, and operations are automated. This pipeline could be deployed to AWS today and start delivering value immediately.
>
> I look forward to discussing how this approach aligns with Dentsu's data engineering practices and hearing your feedback."

---

**Good luck with your presentation! 🚀**
