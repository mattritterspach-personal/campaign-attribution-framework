-- int_journey_positions.sql
-- Enriches each touchpoint with journey position metadata.

WITH base AS (
    SELECT * FROM {{ ref('stg_touchpoints') }}
),

with_position AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY deal_id ORDER BY touchpoint_at ASCP) AS touch_number,
        COUNT(*) OVER (PARTITION BY deal_id) AS n_touches
    FROM base
)

SELECT
    *,
    touch_number = 1 AS is_first_touch,
    touch_number = n_touches AS is_last_touch
FROM with_position
