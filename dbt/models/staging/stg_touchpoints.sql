-- stg_touchpoints.sql
SELECT * FROM {{ source('crm', 'touchpoints') }}