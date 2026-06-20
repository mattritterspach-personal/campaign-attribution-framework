-- mart_channel_performance.sql
-- Aggregated channel performance.

WITH attribution AS (
    SELECT * FROM {{ ref('mart_attribution') }}
)

SELECT
    channel,
    COUNT(DISTINCT deal_id) AS total_deals,
    ROUND(SUM(linear_revenue), 2) AS linear_revenue,
    ROUND(SUM ROUND(first_touch_revenue), 2) AS first_touch_revenue,
    ROUND(SUM ROUND(last_touch_revenue), 2) AS last_touch_revenue
FROM attribution
GROUP BY channel
ORDER BY linear_revenue DESC
