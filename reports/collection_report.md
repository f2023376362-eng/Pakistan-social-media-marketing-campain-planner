# Real Social Audience Data Collection Report
**Project 3: Pakistan Social Audience & Campaign Intelligence Engine (Clustering Based)**  
**Phase 2: Real Pakistani Fashion Audience Data Collection**  
*Collection Timestamp: 2026-11-18 18:34:14Z*

---

## 1. Executive Summary

This report documents the harvesting and verification of **genuine, publicly accessible YouTube social media data** regarding top Pakistani fashion brands: **Khaadi**, **Sapphire**, and **Gul Ahmed**.

In accordance with Phase 2 project objectives, this pipeline utilized the official **YouTube Data API v3** to collect authentic audience discussions, shopping reviews, haul reactions, and brand campaign feedback.

> [!IMPORTANT]
> **Data Provenance & Academic Integrity Verification:**  
> - **Source Data Provenance:** `real_public` (Directly harvested via YouTube Data API v3).
> - **Target Role:** `analysis` (Reserved strictly for audience segmentation, feature engineering, and clustering).
> - **Strict Separation:** This real dataset is maintained entirely separate from the 436-record synthetic development dataset created in Phase 1.
> - **Zero Fabrication:** No comments, likes, replies, or timestamps were fabricated. Original user text across Urdu, Roman Urdu, and English has been preserved verbatim without automated translation or modification.

---

## 2. Dataset Collection Summary

| Dimension | Metric Count | Documentation & Notes |
| :--- | :---: | :--- |
| **Total Videos Harvested** | **45** | High-engagement, brand-specific fashion videos |
| **Total Comments Harvested (Raw)** | **2889** | Top-level comment threads + nested replies |
| **Exact Duplicates Removed** | **0** | Deduplicated strictly by canonical `comment_id` |
| **Total Clean Real Comments** | **2889** | **Falls directly in target range of 2,000–5,000 comments** |
| **Date Range of Comments** | `2019-02-22T13:39:14Z` to `2026-11-17T12:25:44Z` | Organic multi-year audience discourse |
| **Collection Mode** | YouTube Data API v3 | Official authenticated REST endpoints |

---

## 3. Brand Distribution & Coverage

Data was gathered across all three target brands with balanced representation:

### 3.1 Comment Volume by Brand
| Brand Name | Verified Videos | Clean Comments Collected | Percentage of Dataset |
| :--- | :---: | :---: | :---: |
| **Khaadi** | 15 | **1,009** | 34.93% |
| **Sapphire** | 15 | **720** | 24.92% |
| **Gul Ahmed** | 15 | **1,160** | 40.15% |
| **Total** | **45** | **2,889** | **100.00%** |

### 3.2 Top Contributing Videos by Brand

#### Brand: Khaadi
| Video ID | Comments Collected | Views | Video Title |
| :--- | :---: | :---: | :--- |
| [`28lYJjJ4Cp4`](https://www.youtube.com/watch?v=28lYJjJ4Cp4) | 150 | 651480 | Khaadi X Esra | My Symphony |
| [`UZXcyktS180`](https://www.youtube.com/watch?v=UZXcyktS180) | 150 | 1695554 | KHAADI X ESRA | BTS |
| [`FmvskqykOjM`](https://www.youtube.com/watch?v=FmvskqykOjM) | 147 | 16358 | Summer Shopping Haul | Khaadi Haul . |
| [`9dQVVgqaGYc`](https://www.youtube.com/watch?v=9dQVVgqaGYc) | 136 | 54026 | the real-est try-on haul *unfiltered* ft. Khaadi |
| [`X0hRFJ_5iSc`](https://www.youtube.com/watch?v=X0hRFJ_5iSc) | 105 | 354534 | Khaadi X Esra | My Symphony | Blooming Hues |

#### Brand: Sapphire
| Video ID | Comments Collected | Views | Video Title |
| :--- | :---: | :---: | :--- |
| [`c-UBH4uuDBs`](https://www.youtube.com/watch?v=c-UBH4uuDBs) | 150 | 467397 | Sapphire, J.Dot, Khaadi, Bonanza | Perfume Comparision & Review | |
| [`yIZF7okPutE`](https://www.youtube.com/watch?v=yIZF7okPutE) | 97 | 8022 | Sapphire Textile Sale 2026 | Massive Home Shopping Haul | New Bed |
| [`47nlSLOfK8c`](https://www.youtube.com/watch?v=47nlSLOfK8c) | 83 | 925886 | Sapphire sale Pakistan 😂 #trendingshorts #ytshorts #foryou #sapph |
| [`f_Ad8Mc-dOY`](https://www.youtube.com/watch?v=f_Ad8Mc-dOY) | 78 | 2228988 | sapphire sale today / sapphire lawn collection 2024 |
| [`8bXpWLRetVs`](https://www.youtube.com/watch?v=8bXpWLRetVs) | 46 | 60143 | exposing a fraud brand website #sapphire #onlineshopping #fashion |

#### Brand: Gul Ahmed
| Video ID | Comments Collected | Views | Video Title |
| :--- | :---: | :---: | :--- |
| [`y8k0U2sUAA4`](https://www.youtube.com/watch?v=y8k0U2sUAA4) | 150 | 230957 | Gul Ahmed Summer Lawn Collection 2019 |
| [`si7k1YQD8m0`](https://www.youtube.com/watch?v=si7k1YQD8m0) | 150 | 485750 | #PakistanKiPehchan GulAhmed Summer Lawn Collection 2020 |
| [`Yg9iLrkxxC8`](https://www.youtube.com/watch?v=Yg9iLrkxxC8) | 150 | 360547 | Original Branded Clothes at Unbelievable Prices | Sapphire,Cross  |
| [`23d3hxpBNHY`](https://www.youtube.com/watch?v=23d3hxpBNHY) | 150 | 582734 | GulAhmed Summer Lawn 2021 |
| [`2osz5F-vB4Y`](https://www.youtube.com/watch?v=2osz5F-vB4Y) | 150 | 622356 | branded gul ahmed men wash n wear fabric | soft shalwar kameez fo |

---

## 4. Video Selection Criteria & Relevance Validation

To ensure the collected audience comments reflect genuine consumer sentiment toward Pakistani fashion:
1. **Brand Context Filtering:**  
   - **Khaadi:** Selected videos referencing Khaadi unstitched lawn, prêt, sale hauls, and major campaign launches (e.g. Khaadi X Esra). Filtered out unrelated Ayurvedic or non-Pakistani Khadi Indian crafts.
   - **Sapphire:** Targeted Sapphire Pakistan unstitched, ready-to-wear, summer/winter sales, and lifestyle discussions. Excluded unrelated technology/gaming (e.g., Radeon Sapphire GPUs) and Pokémon releases.
   - **Gul Ahmed:** Focused on Gul Ahmed Summer Lawn, Ideas sale shopping hauls, and winter fabric releases.
2. **Comment Availability Check:**  
   - Every candidate video was pre-screened to ensure public comments were enabled (`comment_count > 0`).
3. **Threaded Reply Inclusion:**  
   - Both parent comments and discussion replies were harvested to capture deep conversational sentiment and customer service interactions.

---

## 5. Linguistic Composition of Audience Comments

Pakistani fashion discourse features rich multilingual expressions spanning English, Urdu script, and Roman Urdu:

| Identified Language / Script | Comment Count | Percentage |
| :--- | :---: | :---: |
| **English** | 2,260 | 78.23% |
| **Roman Urdu** | 485 | 16.79% |
| **Other** | 92 | 3.18% |
| **Urdu** | 35 | 1.21% |
| **Mixed (Urdu-English)** | 11 | 0.38% |
| **Unknown** | 6 | 0.21% |

---

## 6. Missing Value Analysis

All fields were audited for completeness. Unpopulated attributes are preserved as standard null values:

### 6.1 Video Dataset Missing Values (`data/raw/real_fashion_videos.csv`)
| Column Name | Missing Count | Null % | Remarks |
| :--- | :---: | :---: | :--- |
| `platform` | 0 | 0.00% | Complete |
| `source_platform` | 0 | 0.00% | Complete |
| `brand_name` | 0 | 0.00% | Complete |
| `video_id` | 0 | 0.00% | Complete |
| `post_id` | 0 | 0.00% | Complete |
| `video_title` | 0 | 0.00% | Complete |
| `video_description` | 0 | 0.00% | Complete |
| `channel_id` | 0 | 0.00% | Complete |
| `channel_title` | 0 | 0.00% | Complete |
| `channel_name` | 0 | 0.00% | Complete |
| `published_at` | 0 | 0.00% | Complete |
| `video_url` | 0 | 0.00% | Complete |
| `source_url` | 0 | 0.00% | Complete |
| `view_count` | 0 | 0.00% | Complete |
| `views` | 0 | 0.00% | Complete |
| `like_count` | 0 | 0.00% | Complete |
| `likes` | 0 | 0.00% | Complete |
| `comment_count` | 0 | 0.00% | Complete |
| `comments_count` | 0 | 0.00% | Complete |
| `data_provenance` | 0 | 0.00% | Complete |
| `data_role` | 0 | 0.00% | Complete |
| `collected_at` | 0 | 0.00% | Complete |

### 6.2 Comment Dataset Missing Values (`data/raw/real_fashion_comments.csv`)
| Column Name | Missing Count | Null % | Remarks |
| :--- | :---: | :---: | :--- |
| `platform` | 0 | 0.00% | Complete |
| `source_platform` | 0 | 0.00% | Complete |
| `brand_name` | 0 | 0.00% | Complete |
| `video_id` | 0 | 0.00% | Complete |
| `post_id` | 0 | 0.00% | Complete |
| `video_url` | 0 | 0.00% | Complete |
| `comment_id` | 0 | 0.00% | Complete |
| `parent_comment_id` | 1832 | 63.41% | Top-level comments (expected) |
| `author` | 0 | 0.00% | Complete |
| `comment_text` | 0 | 0.00% | Complete |
| `likes` | 0 | 0.00% | Complete |
| `published_at` | 0 | 0.00% | Complete |
| `reply_count` | 0 | 0.00% | Complete |
| `data_provenance` | 0 | 0.00% | Complete |
| `data_role` | 0 | 0.00% | Complete |
| `collected_at` | 0 | 0.00% | Complete |
| `detected_language` | 0 | 0.00% | Complete |

---

## 7. Deduplication & Data Integrity Verification

- **Deduplication Strategy:** Applied strict primary-key deduplication on `comment_id`.
- **Duplicate Records Removed:** 0 duplicate records were eliminated during pagination resolution.
- **Urdu & Roman Urdu Text Preservation:** Zero characters were corrupted; all UTF-8 characters including Nastaliq script and emoji reactions were preserved.
- **Privacy Compliance:** Only publicly posted usernames and text were retrieved. No private or protected content was accessed.

---

## 8. API Quota & Technical Log Analysis

- **API Base:** `https://www.googleapis.com/youtube/v3`
- **Total Quota Expended:** Approximately 1,150 quota units (well within 10,000 daily limit).
- **Encountered Issues & Resolutions:**
  - Zero blocking API errors encountered. All video details and comment batches executed successfully.

---

## 9. Artifact Inventory

| Artifact Type | File Path | Records | Encoding | Description |
| :--- | :--- | :---: | :---: | :--- |
| **Raw Video Metadata** | `data/raw/real_fashion_videos.csv` | 45 | UTF-8 | Video attributes, titles, channels, view/like metrics |
| **Raw Real Comments** | `data/raw/real_fashion_comments.csv` | 2,889 | UTF-8 | Audience comments, author handles, timestamps, likes, replies |
| **Collection Report** | `reports/collection_report.md` | — | Markdown | Comprehensive audit and validation report |

*Phase 2 Data Collection Pipeline Successfully Completed.*
