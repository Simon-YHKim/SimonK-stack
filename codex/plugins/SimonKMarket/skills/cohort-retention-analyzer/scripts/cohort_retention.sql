-- cohort_retention.sql — signup-cohort retention triangle from a raw events table.
--
-- Assumed schema (adapt names as needed):
--   events(user_id text, event text, event_time timestamptz)
--
-- Replace the placeholders before running:
--   {{COHORT_EVENT}}  signup / first-touch event name        e.g. 'signup'
--   {{RETURN_EVENT}}  the "still alive" event                e.g. 'session_start'
--   {{PERIOD}}        bucket granularity: 'day' | 'week' | 'month'
--   {{LOOKBACK}}      how far back to include cohorts         e.g. 90  (in {{PERIOD}} units)
--
-- Output columns: cohort | period_number | cohort_size | retained
--   period_number = 0 is the signup bucket itself (== cohort_size).
-- Export as CSV/TSV and feed to: python retention_calc.py curve --input cohorts.csv
--
-- ====================================================================
-- DIALECT A — PostgreSQL / Supabase  (default; uses date_trunc + age math)
-- ====================================================================

WITH cohort AS (
    -- first occurrence of the cohort-defining event per user
    SELECT
        user_id,
        date_trunc('{{PERIOD}}', MIN(event_time)) AS cohort_bucket
    FROM events
    WHERE event = '{{COHORT_EVENT}}'
    GROUP BY user_id
),
activity AS (
    -- every return event, bucketed to the same granularity
    SELECT DISTINCT
        e.user_id,
        date_trunc('{{PERIOD}}', e.event_time) AS active_bucket
    FROM events e
    WHERE e.event = '{{RETURN_EVENT}}'
),
joined AS (
    SELECT
        c.cohort_bucket,
        c.user_id,
        a.active_bucket,
        -- whole-period offset between activity bucket and cohort bucket
        CASE '{{PERIOD}}'
            WHEN 'day'   THEN (a.active_bucket::date - c.cohort_bucket::date)
            WHEN 'week'  THEN ((a.active_bucket::date - c.cohort_bucket::date) / 7)
            WHEN 'month' THEN (
                (EXTRACT(YEAR  FROM a.active_bucket) - EXTRACT(YEAR  FROM c.cohort_bucket)) * 12
              + (EXTRACT(MONTH FROM a.active_bucket) - EXTRACT(MONTH FROM c.cohort_bucket))
            )
        END AS period_number
    FROM cohort c
    JOIN activity a
      ON a.user_id = c.user_id
     AND a.active_bucket >= c.cohort_bucket
),
sizes AS (
    SELECT cohort_bucket, COUNT(*) AS cohort_size
    FROM cohort
    GROUP BY cohort_bucket
)
SELECT
    to_char(j.cohort_bucket, 'YYYY-MM-DD') AS cohort,
    j.period_number,
    s.cohort_size,
    COUNT(DISTINCT j.user_id)              AS retained
FROM joined j
JOIN sizes s ON s.cohort_bucket = j.cohort_bucket
WHERE j.cohort_bucket >= date_trunc('{{PERIOD}}', now())
                         - ({{LOOKBACK}} || ' {{PERIOD}}')::interval
GROUP BY j.cohort_bucket, j.period_number, s.cohort_size
ORDER BY j.cohort_bucket, j.period_number;


-- ====================================================================
-- DIALECT B — BigQuery   (uncomment; comment out Dialect A above)
-- DATE_DIFF / DATE_TRUNC differ. period offset via DATE_DIFF on the bucket dates.
-- ====================================================================
--
-- WITH cohort AS (
--   SELECT user_id, DATE_TRUNC(DATE(MIN(event_time)), {{PERIOD_UPPER}}) AS cohort_bucket
--   FROM `events`
--   WHERE event = '{{COHORT_EVENT}}'
--   GROUP BY user_id
-- ),
-- activity AS (
--   SELECT DISTINCT user_id, DATE_TRUNC(DATE(event_time), {{PERIOD_UPPER}}) AS active_bucket
--   FROM `events`
--   WHERE event = '{{RETURN_EVENT}}'
-- ),
-- joined AS (
--   SELECT c.cohort_bucket, c.user_id,
--          DATE_DIFF(a.active_bucket, c.cohort_bucket, {{PERIOD_UPPER}}) AS period_number
--   FROM cohort c
--   JOIN activity a ON a.user_id = c.user_id AND a.active_bucket >= c.cohort_bucket
-- ),
-- sizes AS (
--   SELECT cohort_bucket, COUNT(*) AS cohort_size FROM cohort GROUP BY cohort_bucket
-- )
-- SELECT FORMAT_DATE('%Y-%m-%d', j.cohort_bucket) AS cohort,
--        j.period_number, s.cohort_size,
--        COUNT(DISTINCT j.user_id) AS retained
-- FROM joined j JOIN sizes s USING (cohort_bucket)
-- WHERE j.cohort_bucket >= DATE_SUB(CURRENT_DATE(), INTERVAL {{LOOKBACK}} {{PERIOD_UPPER}})
-- GROUP BY 1, 2, 3
-- ORDER BY 1, 2;
--
-- ({{PERIOD_UPPER}} = DAY | WEEK | MONTH)
--
-- ====================================================================
-- NOTES
-- - This is the cohort TRIANGLE (bracket-style retained-or-after via >=). For strict
--   N-day retention, change the activity join to equality on a single bucket offset,
--   or post-process in retention_calc.py which derives both from this triangle.
-- - Right-censoring: the newest cohorts have not lived long enough to fill high
--   period_number cells. retention_calc.py marks those NA automatically; do not
--   hand-compare a half-grown cohort against a mature one.
-- - For BEHAVIORAL cohorts, swap {{COHORT_EVENT}} from 'signup' to the first
--   key-action event (e.g. 'first_project_created').
