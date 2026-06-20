-- mart_attribution.sql
-- Final attribution mart with all models.

WITH journeys AS (
    SELECT * FROM {{ ref('int_journey_positions') }}
)

SELECT
    touchpoint_id, customer_id, deal_id, channel, campaign,
    touch_number, n_touches, deal_value,
    CASE WHEN is_first_touch THEN deal_value ELSE 0 END AS first_touch_revenue,
    CASE WHEN is_last_touch  THEN deal_value ELSE 0 END AS last_touch_revenue,
    deal_value / NULLIF(n_touches, 0) AS linear_revenue
FROM journeys
WHERE is_converted = TRUE
ORDER BY deal_id, touch_number
