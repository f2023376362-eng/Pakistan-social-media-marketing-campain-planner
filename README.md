# YouTube Social Media Data Collection & Preprocessing Pipeline

A modular, reproducible data engineering and analytics pipeline engineered in Python and Streamlit. This project serves as the reusable data collection, cleaning, and preprocessing foundation for **Project 3: Pakistan Social Audience & Campaign Intelligence Engine**.

---

## 1. Project Purpose & Scope

Modern social intelligence platforms require robust, schema-compliant, and noise-free data ingestion before advanced machine learning (clustering, audience segmentation, and predictive campaign intelligence) can be performed.

This pipeline transitions from music-specific scraping to a **domain-agnostic, multi-industry YouTube social media intelligence framework**. It provides:
1. **Dynamic Video Discovery & Metadata Harvesting**: Query-based video discovery across any industry, extracting complete video metadata via YouTube Data API v3.
2. **Comment Telemetry Collection**: Automated pagination for extracting user comments, engagement statistics, and timestamps.
3. **Data Cleaning & Standardization**: Schema enforcement, whitespace trimming, duplicate resolution, non-negative integer clipping, and ISO 8601 UTC timestamp normalization.
4. **Descriptive & Distributional Analytics**: Calculation of engagement moments and the Gini coefficient ($G$) to quantify attention inequality across content.
5. **Temporal Pacing & Lexical Analysis**: Analysis of publishing and commenting velocity across years, days of the week, and UTC hours, along with token frequency analysis.
6. **Supporting Qualitative Sentiment Module**: An optional, rule-based lexicon scoring engine providing exploratory sentiment indicators without making unverified machine learning claims.
7. **Performance Benchmarking**: Systematic latency and memory stress-testing across 1x, 10x, and 100x synthetic workloads using `tracemalloc`.

---

## 2. Standardized Data Schemas

The pipeline standardizes all ingested data into two relational schemas, supporting both YouTube-specific attributes and cross-platform Brand Social Media specifications for Project 3.

### 2.1 Video / Post Metadata Schema (`data/*/videos/*.csv`, `data/brand/*.csv`)
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `platform` | `VARCHAR(32)` | Social platform (e.g., YouTube, Instagram, Facebook, TikTok) |
| `brand_name` | `VARCHAR(100)` | Target brand entity (e.g., Audionic, Zero Lifestyle, Khaadi, Jazz) |
| `video_id` / `post_id` | `VARCHAR(64)` | Canonical post/video identifier (Primary Key) |
| `video_title` | `VARCHAR(255)` | Full sanitized video title or post caption |
| `video_description` | `TEXT` | Raw post/video text description |
| `channel_name` / `account_name` | `VARCHAR(255)` | Channel or account display name |
| `published_at` | `DATETIME (ISO 8601)` | Upload timestamp in UTC (`YYYY-MM-DDTHH:MM:SSZ`) |
| `source_url` / `video_url` | `VARCHAR(255)` | Canonical post URL |
| `views` / `view_count` | `BIGINT (Nullable)` | Cumulative view count at collection time (preserved nulls) |
| `likes` / `like_count` | `BIGINT (Nullable)` | Cumulative like count at collection time (preserved nulls) |
| `comments_count` / `comment_count` | `BIGINT (Nullable)` | Total number of published comments (preserved nulls) |
| `collected_at` | `DATETIME (ISO 8601)` | System UTC timestamp when metadata was harvested |

### 2.2 Comment Telemetry Schema (`data/*/comments/*.csv`, `data/brand/*.csv`)
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `platform` | `VARCHAR(32)` | Social platform (e.g., YouTube) |
| `brand_name` | `VARCHAR(100)` | Target brand entity (e.g., Audionic, Zero Lifestyle) |
| `video_id` / `post_id` | `VARCHAR(64)` | Foreign key referencing parent post or video ID |
| `comment_id` | `VARCHAR(64)` | Canonical comment identifier (Primary Key) |
| `author` | `VARCHAR(255)` | Author display name or user handle (sanitized) |
| `comment_text` | `TEXT` | Normalized comment text (HTML tags and URLs stripped) |
| `likes` | `BIGINT (Nullable)` | Non-negative count of comment upvotes (preserved nulls) |
| `reply_count` | `BIGINT (Nullable)` | Non-negative count of direct nested replies (preserved nulls) |
| `published_at` | `DATETIME (ISO 8601)` | Comment publication timestamp in UTC |
| `collected_at` | `DATETIME (ISO 8601)` | System UTC timestamp when comment was harvested |

---

## 3. Architecture & Modular Structure

```text
YouTube_Comment_Scrapper_clean/
├── app.py                                # Streamlit multi-page web application entrypoint
├── conftest.py                           # Pytest configuration and root path resolution
├── pytest.ini                            # Pytest test discovery rules and path exclusions
├── requirements.txt                      # Project dependency specification
├── README.md                             # Documentation and usage guide
├── .env.example                          # Environment template for API keys
├── .gitignore                            # Security exclusions for secrets and artifacts
│
├── src/                                  # Core data engineering & analytics modules
│   ├── youtube_scraper.py                # YouTube Data API v3 search, metadata & comment scraper
│   ├── cleaner.py                        # Schema standardization, deduplication & normalization
│   ├── loader.py                         # Dataset discovery and CSV/Excel loader
│   ├── dataset_manager.py                # In-memory session state management & schema validation
│   ├── inspection.py                     # Schema, null, and duplicate audit inspector
│   ├── statistics.py                     # Engagement statistics & Gini coefficient calculation
│   ├── text_temporal.py                  # Temporal velocity, lexical tokens & keyword tracking
│   ├── sentiment_engine.py               # Optional rule-based sentiment classification
│   ├── benchmark.py                      # Scalability stress-testing via tracemalloc (1x, 10x, 100x)
│   ├── visualizer.py                     # Matplotlib chart generation utilities
│   ├── report_gen.py                     # Markdown and JSON audit report generation
│   └── ui/                               # Modular Streamlit page renderers (6 pages)
│       ├── page_01_overview.py           # 1. Overview & System Architecture
│       ├── page_02_collection.py         # 2. YouTube Data Collection (Keyword Search & URL Harvester)
│       ├── page_03_cleaning.py           # 3. Data Cleaning & Preprocessing Audit
│       ├── page_04_engagement.py         # 4. Engagement & Statistical Analytics
│       ├── page_05_sentiment.py          # 5. Sentiment Analysis (Optional Supporting Module)
│       └── page_06_exports.py            # 6. Data Export & Report Generation
│
├── data/                                 # Active standardized datasets (Clean & Ready for Brand Ingestion)
│   ├── brand/                            # Uploaded and live brand social datasets (.gitkeep)
│   ├── raw/
│   │   ├── videos/                       # Raw video/post metadata files (.gitkeep)
│   │   └── comments/                     # Raw comment telemetry files (.gitkeep)
│   └── processed/
│       ├── videos/                       # Cleaned, standardized video datasets (.gitkeep)
│       └── comments/                     # Cleaned, standardized comment datasets (.gitkeep)
│
├── tests/                                # Automated verification suite (38 passing tests)
│   ├── test_scraper.py                   # URL extraction, API status & mocked API requests
│   ├── test_cleaner.py                   # Schema enforcement, deduplication & type bounds
│   ├── test_analytics.py                 # Gini coefficient, statistics, temporal & text analysis
│   ├── test_dataset_manager.py           # File buffering, Excel ingestion & session state
│   ├── test_pipeline_integration.py      # End-to-end pipeline execution & report generation
│   ├── test_app_integration.py           # Streamlit 6-page navigation & renderer imports
│   └── test_youtube.py                   # Legacy schema verification and compatibility tests
│
├── outputs/                              # Pipeline artifacts and evaluation reports
│   ├── summary_metrics.json              # Structured numerical metrics
│   ├── benchmark_results.json            # Scalability performance results
│   ├── benchmark_results.csv             # Tabular benchmark timings
│   ├── pipeline_audit_report.md          # Compiled Markdown audit report
│   └── charts/                           # Generated analytical charts
│
├── archive/                              # Preserved historical assets & legacy prototypes
│   ├── datasets/                         # Original music video datasets & advertising CSVs
│   ├── advertising_project/              # Archived digital advertising optimizer modules & tests
│   └── reports/                          # Previous milestone analytical reports
│
├── run_cleaning.py                       # CLI script: Standalone data cleaning
├── run_pipeline.py                       # CLI script: Full end-to-end preprocessing pipeline
└── run_benchmark.py                      # CLI script: Synthetic scalability stress-test
```

---

## 4. Installation & Environment Setup

### 4.1 Prerequisites
- **Python**: Version 3.10 to 3.12 (Python 3.12 verified)
- **Git**: Installed locally

### 4.2 Clone & Install Dependencies
```bash
# Navigate to project workspace
cd YouTube_Comment_Scrapper_clean

# Create and activate virtual environment (optional but recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 4.3 Configure YouTube API Key
1. Obtain an API key from the [Google Cloud Console](https://console.cloud.google.com/) with the **YouTube Data API v3** enabled.
2. Create a `.env` file in the project root directory:
```bash
# Copy example configuration
copy .env.example .env
```
3. Update `.env` with your valid key:
```env
YOUTUBE_API_KEY=AIzaSyYourActualYouTubeDataApiKeyHere
```
> **Offline / Bundled Mode:** If no API key is provided, the pipeline functions with the bundled verified datasets in `data/raw/` and `data/processed/`.

---

## 5. Execution Workflows & CLI Commands

### 5.1 Launch Web Interface (Streamlit)
```bash
streamlit run app.py
```
Access the application at `http://localhost:8501`. Use the sidebar navigation to move between the 6 modular stages:
1. **Overview & Architecture**: System summary, directory structure, and active session telemetry.
2. **YouTube Data Collection**: Keyword search across any domain or direct single-video URL scraping.
3. **Data Cleaning & Preprocessing**: Clean raw video/comment datasets with live before/after diff audit metrics.
4. **Engagement Analytics**: Descriptive statistics, Gini attention concentration, and temporal distributions.
5. **Sentiment Analysis (Optional)**: Lexicon-based polarity distribution and top positive/negative comments.
6. **Data Export & Reports**: Download cleaned datasets (CSV/Excel) and compiled Markdown reports.

### 5.2 Standalone Data Cleaning CLI
Cleans raw comments and videos from `data/raw/` and exports standardized files to `data/processed/`:
```bash
python run_cleaning.py
```

### 5.3 Full End-to-End Pipeline CLI
Executes the full 7-step pipeline (loading $\rightarrow$ inspection $\rightarrow$ cleaning $\rightarrow$ statistics $\rightarrow$ temporal/text $\rightarrow$ benchmarking $\rightarrow$ report generation):
```bash
python run_pipeline.py
```

### 5.4 Scalability Stress-Testing CLI
Executes scalability benchmarks across 1x, 10x, and 100x synthetic workloads:
```bash
python run_benchmark.py
```

### 5.5 Automated Test Suite
Run the test suite verifying all modules:
```bash
pytest -v
```
*Current test suite status: **38 passed, 0 failed**.*

---

## 6. Academic Transparency & Methodological Guardrails

1. **Gini Coefficient ($G$) for Attention Concentration**:
   The Gini coefficient is computed on comment likes and reply distributions:
   $$G = \frac{\sum_{i=1}^n \sum_{j=1}^n |x_i - x_j|}{2n^2 \bar{x}}$$
   A high Gini value ($G > 0.70$) highlights that social media engagement exhibits extreme Pareto skew, where a fraction of top comments garner the majority of user attention.

2. **Sentiment Analysis as an Exploratory Signal**:
   The sentiment classification engine relies on a transparent lexicon model with negation inversion heuristics:
   $$\text{polarity} = \tanh\left(\frac{\text{score}}{2.5}\right) \in [-1.0, 1.0]$$
   It serves as a supporting heuristic indicator. It does **not** make false claims of complex contextual deep learning, BERT embeddings, or fine-tuned transformers.

3. **Downstream Separation (Project 3 Boundary)**:
   This repository is strictly the **data collection and preprocessing foundation**. Complex machine learning tasks—such as K-Means clustering, demographic audience segmentation, automated anomaly detection, and algorithmic budget recommendations—are left for downstream implementation in **Project 3: Pakistan Social Audience & Campaign Intelligence Engine**.
