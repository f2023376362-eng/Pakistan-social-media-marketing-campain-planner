# Data Quality & Preparation Report
**Project 3: Pakistan Social Audience & Campaign Intelligence Engine (Clustering Based)**  
**Phase 1: Fashion Dataset Preparation**  
*Document Generated: 2026-11-18*

---

## 1. Executive Summary

This report documents the rigorous data extraction, cleaning, normalization, and quality profiling executed for **Phase 1: Fashion Dataset Preparation** within the *Pakistan Social Audience & Campaign Intelligence Engine*.

To support targeted machine learning workflows (clustering-based audience segmentation, campaign resonance profiling, and behavioral anomaly detection), this phase isolated and refined social media records representing Pakistani fashion brands and their audiences.

> [!IMPORTANT]
> **Data Provenance & Academic Integrity Disclaimer:**  
> The underlying records analyzed herein originate from `data/raw/pakistan_social_media_posts.csv`. This dataset consists of **simulated/synthetic social media records** created strictly for algorithmic development, architecture prototyping, and pipeline validation. It does **not** represent real-world empirical social media evidence or actual commercial brand metrics. In accordance with academic integrity guidelines, zero records have been fabricated or falsely represented as empirical user data.

---

## 2. Source Dataset Audit

The raw input file `data/raw/pakistan_social_media_posts.csv` was audited prior to applying transformations:

- **Source File Path:** `data/raw/pakistan_social_media_posts.csv`
- **File Size:** 635,129 bytes
- **SHA-256 Checksum:** `7fc6b6c5ccd04a9b03d4718c4fafd01c1b525cc2481240bcda2bbc501f928240`
- **Total Records:** 3,030 rows
- **Total Columns:** 17 columns
- **Exact Duplicate Rows in Raw Dataset:** 30 rows
- **Unique `post_id` Values:** 3,000

### Category Breakdown in Raw Dataset
The source dataset spanned seven distinct industry verticals:

| Brand Category | Raw Record Count | Percentage |
| :--- | :---: | :---: |
| **Food & Restaurants** | 479 | 15.81% |
| **Fashion & Lifestyle** *(Selected Focus)* | **444** | **14.65%** |
| **Telecom** | 432 | 14.26% |
| **Banking & Fintech** | 431 | 14.22% |
| **Beauty** | 422 | 13.93% |
| **Electronics** | 413 | 13.63% |
| **Education** | 409 | 13.50% |
| **Total** | **3,030** | **100.00%** |

---

## 3. Data Extraction & Scope Isolation

In adherence to project requirements, records were strictly filtered to retain **Pakistani fashion and lifestyle brands**:
- **Filter Criterion:** `brand_category.str.strip() == "Fashion & Lifestyle"`
- **Extracted Subset:** 444 rows (14.65% of raw population)
- **Unrelated Categories Excluded:** 2,586 rows preserved safely in `data/raw/pakistan_social_media_posts.csv` without modification.

---

## 4. Deduplication Protocol

A duplicate audit was conducted across the 444 extracted fashion records:
- **Exact Duplicate Rows Identified:** 8 rows
- **Duplicate `post_id` Count:** 8 instances
- **Duplicate Conflict Analysis:** All 8 duplicate `post_id` occurrences were 100% exact row duplicates across all 17 feature dimensions. There were zero conflicting or mutated records with duplicate IDs.
- **Action Taken:** Removed the 8 redundant duplicate rows using `drop_duplicates()`.
- **Post-Deduplication Record Count:** **436 unique fashion posts**.

---

## 5. Inconsistency Standardization & Normalization

### 5.1 Platform Normalization
The raw platform field contained minor casing variations (e.g., lowercased `tiktok`). All entries were mapped to industry-standard title casing:

| Raw Platform String | Frequency | Normalized Platform Name | Final Frequency |
| :--- | :---: | :--- | :---: |
| `Instagram` | 112 | `Instagram` | 112 |
| `TikTok` | 106 | `TikTok` | 107 |
| `tiktok` | 1 | `TikTok` | — |
| `Facebook` | 102 | `Facebook` | 102 |
| `YouTube` | 66 | `YouTube` | 66 |
| `X (Twitter)` | 49 | `X (Twitter)` | 49 |
| **Total** | **436** | | **436** |

### 5.2 Category Label Standardization
- Applied `.str.strip()` to eliminate trailing or leading whitespace.
- Canonical label established: `"Fashion & Lifestyle"`.

---

## 6. Missing Value Handling & Zero-Fabrication Policy

To uphold scientific validity, no synthetic observations, artificial follower counts, or imputed hashtags were fabricated:

| Column Name | Missing Count | Missing % | Handling Policy & Technical Rationale |
| :--- | :---: | :---: | :--- |
| `hashtags` | 7 | 1.61% | **Preserved as Null / Empty String**. In organic social media, captions without hashtags are standard behavior. Fabricating tags would distort NLP keyword vectors. |
| `followers_count` | 5 | 1.15% | **Preserved as Null / Float NaN**. Missing account metrics are left un-imputed to prevent artificial skewing of engagement rate baselines during clustering. |
| *All Other 17 Columns* | 0 | 0.00% | 100% complete (no missing values). |

---

## 7. Metadata Schema Enrichment

To ensure strict data lineage and avoid any ambiguity regarding the dataset's nature, two structural metadata attributes were appended:

1. **`data_provenance`** = `"synthetic"`  
   *Indicates that the record was generated computationally as part of development simulation.*
2. **`data_role`** = `"development"`  
   *Marks the record as intended exclusively for pipeline development, architecture testing, and cluster prototyping.*

The final processed dataset contains **19 columns** (17 original source columns + 2 metadata governance columns).

---

## 8. Statistical Profile & Multi-Dimensional Distribution

### 8.1 Content Type Distribution
- **Short Video/Reel:** 136 (31.19%)
- **Image Post:** 121 (27.75%)
- **Text Post:** 59 (13.53%)
- **Poll/Question:** 51 (11.70%)
- **Carousel:** 43 (9.86%)
- **Live Stream:** 26 (5.96%)

### 8.2 Campaign Topic Distribution
- **Sales & Offers:** 65 (14.91%)
- **Ramadan & Eid:** 63 (14.45%)
- **Cricket & PSL:** 57 (13.07%)
- **Humor & Memes:** 51 (11.70%)
- **Fashion & Weddings:** 47 (10.78%)
- **Tech & Gadgets:** 43 (9.86%)
- **Education & Career:** 43 (9.86%)
- **Food:** 36 (8.26%)
- **Independence Day:** 31 (7.11%)

### 8.3 Geographic & City Distribution
- **Karachi:** 116 (26.61%)
- **Lahore:** 108 (24.77%)
- **Islamabad:** 54 (12.39%)
- **Multan:** 45 (10.32%)
- **Peshawar:** 44 (10.09%)
- **Faisalabad:** 31 (7.11%)
- **Rawalpindi:** 29 (6.65%)
- **Quetta:** 9 (2.06%)

### 8.4 Target Audience Segments
- **Gen Z (18-24):** 114 (26.15%)
- **Young Professionals (25-34):** 102 (23.39%)
- **Students:** 100 (22.94%)
- **Parents (35-50):** 64 (14.68%)
- **Small Business Owners:** 56 (12.84%)

### 8.5 Linguistic Composition
- **Roman Urdu:** 153 (35.09%)
- **Mixed (Urdu-English):** 114 (26.15%)
- **English:** 102 (23.39%)
- **Urdu (Script):** 67 (15.37%)

### 8.6 Sentiment & Verification Breakdown
- **Sentiment:** Positive: 224 (51.38%), Neutral: 134 (30.73%), Negative: 78 (17.89%)
- **Verification Status:** Unverified (`False`): 348 (79.82%), Verified (`True`): 88 (20.18%)

### 8.7 Engagement Metrics Summary
| Metric | Count | Mean | Std Dev | Min | 25th % | Median | 75th % | Max |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Likes** | 436 | 2,183.94 | 4,877.03 | *-3,513.00* | 264.00 | 817.50 | 2,013.25 | 45,898.00 |
| **Shares** | 436 | 272.81 | 678.49 | 1.00 | 29.75 | 86.50 | 240.00 | 7,178.00 |
| **Comments** | 436 | 351.51 | 657.99 | 2.00 | 42.75 | 139.00 | 348.00 | 5,126.00 |
| **Followers Count** | 431 | 79,474.30 | 138,603.44 | 500.00 | 15,435.50 | 33,699.00 | 78,174.00 | 1,224,500.00 |

> [!NOTE]
> **Identified Synthetic Data Anomaly:**  
> The minimum value for `likes` contains a negative entry (`-3,513`). This is an artifact of synthetic data generation in the source CSV. In accordance with data preparation constraints ("Do not fabricate real comments or engagement metrics" and "Preserve all original source columns"), this value was preserved as-is. In subsequent Phase 2 feature engineering for clustering, anomaly-clipping or absolute transformation can be formally applied.

### 8.8 Temporal Window
- **Earliest Timestamp:** `2024-01-01 12:07`
- **Latest Timestamp:** `2024-12-31 11:31`
- **Unique Timestamps:** 435 (spanning full calendar year 2024)

---

## 9. Data Dictionary

| # | Column Name | Physical Type | Logical Type | Nullable | Description / Domain |
| :---: | :--- | :--- | :--- | :---: | :--- |
| 1 | `post_id` | String | Identifier | No | Unique post identifier (`PK#####`) |
| 2 | `timestamp` | String | Datetime | No | Post creation timestamp (`YYYY-MM-DD HH:MM`) |
| 3 | `platform` | String | Categorical | No | Social platform (`Instagram`, `TikTok`, `Facebook`, `YouTube`, `X (Twitter)`) |
| 4 | `brand_category` | String | Categorical | No | Vertical classification (`Fashion & Lifestyle`) |
| 5 | `content_type` | String | Categorical | No | Media format (`Short Video/Reel`, `Image Post`, `Text Post`, `Poll/Question`, `Carousel`, `Live Stream`) |
| 6 | `topic` | String | Categorical | No | Post subject/theme (`Sales & Offers`, `Ramadan & Eid`, etc.) |
| 7 | `caption` | String | Text | No | Post text caption in English, Urdu, or Roman Urdu |
| 8 | `hashtags` | String | Text | Yes | Space-separated hashtags (7 records unpopulated) |
| 9 | `language` | String | Categorical | No | Language modality (`Roman Urdu`, `Mixed`, `English`, `Urdu`) |
| 10 | `city` | String | Categorical | No | Target Pakistani city/market |
| 11 | `audience_segment` | String | Categorical | No | Demographic/behavioral target audience |
| 12 | `followers_count` | Float64 | Numeric | Yes | Account follower count (5 records unpopulated) |
| 13 | `verified` | Boolean | Boolean | No | Account verification flag (`True` / `False`) |
| 14 | `likes` | Int64 | Numeric | No | Post like engagement count |
| 15 | `shares` | Int64 | Numeric | No | Post share/repost count |
| 16 | `comments` | Int64 | Numeric | No | Post user reply count |
| 17 | `sentiment` | String | Categorical | No | Classified sentiment label (`Positive`, `Neutral`, `Negative`) |
| 18 | `data_provenance` | String | Metadata | No | Fixed governance token: `"synthetic"` |
| 19 | `data_role` | String | Metadata | No | Fixed usage boundary: `"development"` |

---

## 10. Integrity Verification & Artifact Summary

| Artifact | File Path | Records | Dimensions | SHA-256 Checksum |
| :--- | :--- | :---: | :---: | :--- |
| **Raw Input** | `data/raw/pakistan_social_media_posts.csv` | 3,030 | 17 | `7fc6b6c5ccd04a9b03d4718c4fafd01c1b525cc2481240bcda2bbc501f928240` |
| **Processed Dataset** | `data/processed/fashion_development.csv` | 436 | 19 | `6ba8dd211951138f5b6f36613b9e4cf13b712e9492aa1dcdbf5a1ef51416c948` |
| **Profile Profile** | `reports/dataset_profile.json` | — | — | Machine-readable metadata & distribution profile |
| **Quality Report** | `reports/data_quality_report.md` | — | — | This comprehensive auditing report |

**Verification Confirmation:**
1. The raw source dataset SHA-256 hash was validated before and after execution; it remains **strictly untouched**.
2. The processed dataset loads without errors via `pandas.read_csv()`.
3. 100% of rows in `data/processed/fashion_development.csv` belong exclusively to `Fashion & Lifestyle`.
4. Exactly 8 duplicate records were removed.
5. All 17 original columns are preserved, and 2 metadata columns (`data_provenance`, `data_role`) are present.
