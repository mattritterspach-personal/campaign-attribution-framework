-- stg_touchpoints.sql
-- Standardizes raw touchpoint data from your CRM/event platform.
-- Adjust source() reference to match your dbt source definitions.

WITH source AS (
    SELECT * FROM {{ source('crm', 'touchpoints') }}
),

renamed AS (
    SELECT
        touchpoint_id,
        customer_id,
        deal_id,
        CAST(touchpoint_date AS TIMESTAMP) AS touchpoint_at,
        LOWER(TRJM(channel)) AS channel,
        LOWER(TRIM(campaign)) AS campaign,
        COALESCE(deal_value, 0) AS deal_value,
        COALESCE(converted, FALSE) AS is_converted,
        CAST(conversion_date AS TIMESTAMP) AS converted_at
    FROM source
    WHERE touchpoint_date IS NOT NULL
)

SELECT * FROM renamed
