# Data Engineering Quest: Event-Driven AWS Pipeline

This project implements a robust, multi-region data pipeline that automates the ingestion, storage, and analysis of economic and census data. It follows industry best practices for Infrastructure as Code (IaC) using Terraform, event-driven architecture using AWS S3 and SQS, and scalable data processing with Python and Pandas.

---

## 🚀 The Pipeline Flow

The architecture is designed to be decoupled and resilient, spanning two AWS regions:

1.  **Ingestion (Mumbai - `ap-south-1`):** An EventBridge rule triggers the `rearc-ingestion` Lambda. It fetches data from the **DataUSA API** and the **BLS (Bureau of Labor Statistics)** server.
2.  **Cross-Region Storage:** Data is uploaded to an **S3 Bucket** in **Stockholm (`eu-north-1`)**.
3.  **Event Notification:** Upon `.json` upload, S3 triggers an event notification.
4.  **Buffering (SQS):** The notification is sent to an **Amazon SQS Queue** in Stockholm, acting as a buffer for the processing stage.
5.  **Analytics (Stockholm - `eu-north-1`):** The `rearc-analytics` Lambda parses the SQS message, loads datasets into **Pandas**, and generates an economic report.



---

## 📖 Data Dictionary

### 1. Census Population Data (DataUSA API)
*Source: `raw/census_bureau/population_data.json`*

| Column | Type | Description |
| :--- | :--- | :--- |
| **Nation ID** | String | Unique identifier for the nation (e.g., `01000US`). |
| **Nation** | String | Human-readable name of the nation (e.g., `United States`). |
| **Year** | Integer | Numerical representation of the data year. |
| **Population** | Integer | Total estimated resident population count. ||

### 2. BLS Time Series Data (BLS Source)
*Source: `raw/bls/pr.data.0.Current`*

| Column | Type | Description |
| :--- | :--- | :--- |
| **series_id** | String | 17-character unique identifier for the specific economic series. |
| **year** | Integer | The year associated with the observation. |
| **period** | String | Timeframe code (e.g., `Q01` for Q1, `M01` for January). |
| **value** | Float | The numerical value/index for the given series and period. |
| **footnote_codes**| String | Supplemental codes providing context or data quality flags. |

### 3. Final Combined Report
*Produced by the Analytics Lambda*

| Column | Type | Description |
| :--- | :--- | :--- |
| **series_id** | String | The target series (e.g., `PRS30006032`). |
| **year** | Integer | Joined year from both datasets. |
| **period** | String | Quarter identifier (filtered for `Q01`). |
| **value** | Float | BLS value for that year/period. |
| **Population** | Integer | US Population for the matching year. |

---

## 🛠️ Tech Stack

* **IaC:** Terraform (AWS Provider)
* **Cloud:** AWS (Lambda, S3, SQS, EventBridge, IAM)
* **Language:** Python 3.12 (Pandas, NumPy, Boto3)
* **Regions:** Stockholm (`eu-north-1`) & Mumbai (`ap-south-1`)

---

## ⚙️ Deployment & Setup

### Prerequisites
* AWS CLI configured with appropriate credentials.
* Terraform (v1.6+) and Python 3.12+ installed locally.

### Installation
1.  **Initialize Terraform:**
    ```bash
    terraform -chdir=infrastructure init
    ```
2.  **Deploy:**
    ```bash
    terraform -chdir=infrastructure apply
    ```

---

## 🧪 Testing

### End-to-End Trigger
Manually trigger the `rearc-ingestion` Lambda in the Mumbai console. Verify that:
1. Files appear in the Stockholm S3 bucket.
2. The `rearc-analytics` Lambda prints tables to CloudWatch logs in Stockholm.

### Mock Analysis Test
Run a test event on the Analytics Lambda using an SQS-wrapped S3 payload:
```json
{
  "Records": [{
    "body": "{\"Records\":[{\"s3\":{\"bucket\":{\"name\":\"data-quest-bucket-rearc\"},\"object\":{\"key\":\"raw/datausa/population_data.json\"}}}]}"
  }]
}