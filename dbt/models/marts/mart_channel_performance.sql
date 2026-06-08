-- mart_channel_performance.sql
-- Aggregated channel performance under each attribution model.
-- This is the "reporting layer" — connect BI tools (Looker, Tableau, Metabase) here.

WITH attribution AS (
    SELECT * FROM {{ ref('mart_attribution') }}
)

SELECT
    touchpoint_month,
    channel,
    campaign,

    -- Volume
    COUNT(DISTINCT deal_id)                                         AS total_deals,
    COUNT(touchpoint_id)                                            AS total_touchpoints,
    ROUND(AVG(n_touches), 1)                                        AS avg_touches_per_deal,

    -- Attributed Revenue by Model
    ROUND(SUM(first_touch_revenue),  2)                             AS first_touch_revenue,
    ROUND(SUM(last_touch_revenue),   2)                             AS last_touch_revenue,
    ROUND(SUM(linear_revenue),       2)                             AS linear_revenue,
    ROUND(SUM(time_decay_revenue),   2)                             AS time_decay_revenue,
    ROUND(SUM(u_shaped_revenue),     2)                             AS u_shaped_revenue,

    -- Attributed Deals (fractional)
    ROUND(SUM(first_touch_weight),   2)                             AS first_touch_deals,
    ROUND(SUM(last_touch_weight),    2)                             AS last_touch_deals,
    ROUND(SUM(linear_weight),        2)                             AS linear_deals,
    ROUND(SUM(time_decay_weight),    2)                             AS time_decay_deals,
    ROUND(SUM(u_shaped_weight),      2)                             AS u_shaped_deals,

    -- Average days before conversion for this channel
    ROUND(AVG(days_before_conversion), 1)                           AS avg_days_before_conversion,

    -- First-touch and last-touch share
    ROUND(
        SUM(CASE WHEN is_first_touch THEN 1 ELSE 0 END) * 1.0
        / NULLIF(COUNT(touchpoint_id), 0), 4
    )                                                               AS first_touch_rate,
    ROUND(
        SUM(CASE WHEN is_last_touch THEN 1 ELSE 0 END) * 1.0
        / NULLIF(COUNT(touchpoint_id), 0), 4
    )                                                               AS last_touch_rate

FROM attribution
GROUP BY 1, 2, 3
ORDER BY touchpoint_month DESC, linear_revenue DESC
