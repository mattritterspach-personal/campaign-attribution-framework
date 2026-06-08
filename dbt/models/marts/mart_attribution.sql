-- mart_attribution.sql
-- Final attribution mart: one row per touchpoint with credit assigned
-- under each of 5 attribution models. Join to deals/campaigns for reporting.

WITH journeys AS (
    SELECT * FROM {{ ref('int_journey_positions') }}
),

-- ─── Attribution Weight Calculations ─────────────────────────────────────────

with_weights AS (
    SELECT
        *,

        -- First Touch
        CASE WHEN is_first_touch THEN 1.0 ELSE 0.0 END
            AS first_touch_weight,

        -- Last Touch
        CASE WHEN is_last_touch  THEN 1.0 ELSE 0.0 END
            AS last_touch_weight,

        -- Linear
        1.0 / NULLIF(n_touches, 0)
            AS linear_weight,

        -- Time Decay (pre-calculated in intermediate)
        time_decay_weight,

        -- U-Shaped: 40% first, 40% last, 20% evenly to middle
        CASE
            WHEN n_touches = 1                             THEN 1.0
            WHEN n_touches = 2 AND is_first_touch          THEN 0.5
            WHEN n_touches = 2 AND is_last_touch           THEN 0.5
            WHEN is_first_touch                            THEN 0.40
            WHEN is_last_touch                             THEN 0.40
            ELSE 0.20 / NULLIF(n_touches - 2, 0)
        END AS u_shaped_weight

    FROM journeys
    WHERE is_converted = TRUE
),

-- ─── Attributed Revenue ───────────────────────────────────────────────────────

with_revenue AS (
    SELECT
        touchpoint_id,
        customer_id,
        deal_id,
        touchpoint_at,
        touchpoint_month,
        channel,
        campaign,
        touchpoint_type,
        touch_number,
        n_touches,
        is_first_touch,
        is_last_touch,
        days_before_conversion,
        deal_value,

        ROUND(deal_value * first_touch_weight,  2) AS first_touch_revenue,
        ROUND(deal_value * last_touch_weight,   2) AS last_touch_revenue,
        ROUND(deal_value * linear_weight,       2) AS linear_revenue,
        ROUND(deal_value * time_decay_weight,   2) AS time_decay_revenue,
        ROUND(deal_value * u_shaped_weight,     2) AS u_shaped_revenue,

        first_touch_weight,
        last_touch_weight,
        linear_weight,
        time_decay_weight,
        u_shaped_weight

    FROM with_weights
)

SELECT * FROM with_revenue
ORDER BY deal_id, touch_number
