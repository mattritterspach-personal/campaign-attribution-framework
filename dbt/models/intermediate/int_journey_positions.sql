-- int_journey_positions.sql
-- Enriches each touchpoint with journey position metadata:
-- touch_number, n_touches, is_first, is_last, is_middle, days_before_conversion.

WITH base AS (
    SELECT * FROM {{ ref('stg_touchpoints') }}
),

with_position AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY deal_id ORDER BY touchpoint_at ASC
        )                                                          AS touch_number,
        COUNT(*) OVER (PARTITION BY deal_id)                      AS n_touches,
        MIN(touchpoint_at) OVER (PARTITION BY deal_id)            AS first_touch_at,
        MAX(touchpoint_at) OVER (PARTITION BY deal_id)            AS last_touch_at
    FROM base
),

with_flags AS (
    SELECT
        *,
        touch_number = 1                                          AS is_first_touch,
        touch_number = n_touches                                  AS is_last_touch,
        touch_number != 1 AND touch_number != n_touches          AS is_middle_touch,
        CASE
            WHEN converted_at IS NOT NULL
            THEN DATE_DIFF('day', touchpoint_at, converted_at)
            ELSE NULL
        END                                                        AS days_before_conversion,
        CASE
            WHEN n_touches = 1 THEN 1.0
            WHEN touch_number = n_touches THEN 0.0
            ELSE EXP(-LN(2) * (n_touches - touch_number) / 7.0)
        END                                                        AS time_decay_raw_weight
    FROM with_position
),

normalized AS (
    SELECT
        *,
        time_decay_raw_weight / SUM(time_decay_raw_weight) OVER (PARTITION BY deal_id)
            AS time_decay_weight
    FROM with_flags
)

SELECT * FROM normalized
