# Campaign Attribution Framework

A complete multi-touch attribution toolkit for marketing teams. Models every major attribution methodology and includes dbt models for data warehouse deployment.

## What's Inside

| File | Description |
|------|-------------|
| `attribution.py` | Python attribution engine (all models) |
| `dashboard.py` | Streamlit dashboard — compare models side-by-side |
| `sql/attribution_queries.sql` | Raw SQL for CRM/warehouse |
| `dbt/models/` | dbt models: staging, intermediate, marts |
| `dbt/dbt_project.yml` | dbt project config |
| `requirements.txt` | Python dependencies |

## Attribution Models Included

| Model | Description | Best For |
|-------|-------------|----------|
| **First Touch** | 100% credit to first touchpoint | Brand / awareness campaigns |
| **Last Touch** | 100% credit to last touchpoint | Bottom-funnel / conversion |
| **Linear** | Equal credit to all touchpoints | Even-weighted journeys |
| **Time Decay** | More credit to recent touches | Short sales cycles |
| **U-Shaped (Position-Based)** | 40% first, 40% last, 20% middle | B2B demand gen |
| **W-Shaped** | 30% first, 30% MQL, 30% last | Full-funnel B2B |
| **Shapley Value** | Game-theoretic marginal contribution | Most accurate / data-intensive |

## Quick Start

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

## dbt Setup

```bash
cd dbt/
pip install dbt-core dbt-postgres  # or dbt-bigquery, dbt-snowflake
dbt deps
dbt run
dbt test
```

Configure your data warehouse connection in `dbt/profiles.yml`.

## Data Schema

Input data should have one row per touchpoint:

```
customer_id, touchpoint_date, channel, campaign, touchpoint_type,
deal_id, deal_value, converted, conversion_date
```

## License

MIT
