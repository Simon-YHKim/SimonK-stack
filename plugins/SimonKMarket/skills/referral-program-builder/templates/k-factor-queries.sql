-- referral-program-builder :: read-only PostgreSQL measurement queries
-- Run with a role that has SELECT only. These queries do not grant rewards or
-- mutate referral state. Do not paste raw codes, IPs, or user IDs into reports.
--
-- Exact K-factor needs one unpredictable, per-recipient invite_id on each
-- invite_shared event and the same invite_id on referral_signed_up. A generic
-- social share with unknown recipients cannot be counted as sent invitations.
-- props.invite_id is a join token, not a substitute for anti-abuse checks.
-- A signup is counted only once and only within 30 days of its invitation.
-- Cohort months below use UTC; change the zone deliberately for local reports.

-- 1. Instrumentation coverage. Missing invite IDs mean K-factor is UNKNOWN,
--    not zero; investigate before using the cohort query below.
SELECT event,
       COUNT(*) AS events,
       COUNT(*) FILTER (
         WHERE NULLIF(props ->> 'invite_id', '') IS NULL
       ) AS missing_invite_id,
       COUNT(*) FILTER (WHERE actor_id IS NULL) AS missing_actor_id
FROM referral_events
WHERE event IN ('invite_shared', 'referral_signed_up')
GROUP BY event
ORDER BY event;

-- Ambiguous tokens are excluded from the cohort metric. Return counts only.
SELECT 'invite_id_shared_by_multiple_referrers_or_codes' AS anomaly,
       COUNT(*) AS ambiguous_ids
FROM (
  SELECT props ->> 'invite_id' AS invite_id
  FROM referral_events
  WHERE event = 'invite_shared'
    AND NULLIF(props ->> 'invite_id', '') IS NOT NULL
  GROUP BY props ->> 'invite_id'
  HAVING COUNT(DISTINCT actor_id) > 1 OR COUNT(DISTINCT lower(code)) > 1
) ambiguous;

-- 2. Monthly invitation cohort: K = invitations/inviter × signups/invitation.
--    Duplicate invite_id values from multiple referrers are excluded, not
--    assigned arbitrarily. Review missing/duplicate counts separately.
WITH invitation_candidates AS (
  SELECT props ->> 'invite_id' AS invite_id,
         MIN(actor_id::text)::uuid AS referrer_id,
         MIN(lower(code)) AS code,
         MIN(created_at) AS shared_at,
         COUNT(DISTINCT actor_id) AS referrer_count,
         COUNT(DISTINCT lower(code)) AS code_count
  FROM referral_events
  WHERE event = 'invite_shared'
    AND actor_id IS NOT NULL
    AND code IS NOT NULL
    AND NULLIF(props ->> 'invite_id', '') IS NOT NULL
  GROUP BY props ->> 'invite_id'
),
invitations AS (
  SELECT invite_id, referrer_id, code, shared_at
  FROM invitation_candidates
  WHERE referrer_count = 1 AND code_count = 1
),
signup_candidates AS (
  SELECT e.props ->> 'invite_id' AS invite_id,
         MIN(e.created_at) AS signed_up_at,
         MIN(r.referrer_id::text)::uuid AS referrer_id,
         MIN(lower(r.code)) AS code,
         COUNT(DISTINCT e.actor_id) AS referred_count,
         COUNT(DISTINCT r.referrer_id) AS referrer_count,
         COUNT(DISTINCT lower(r.code)) AS code_count
  FROM referral_events e
  JOIN referrals r ON r.id = e.referral_id AND r.referred_id = e.actor_id
  WHERE e.event = 'referral_signed_up'
    AND NULLIF(e.props ->> 'invite_id', '') IS NOT NULL
  GROUP BY e.props ->> 'invite_id'
),
joined AS (
  SELECT i.referrer_id, i.shared_at,
         CASE WHEN s.referred_count = 1 AND s.referrer_count = 1
                    AND s.code_count = 1
                    AND s.signed_up_at >= i.shared_at
                    AND s.signed_up_at < i.shared_at + INTERVAL '30 days'
              THEN s.signed_up_at END AS signed_up_at
  FROM invitations i
  LEFT JOIN signup_candidates s ON s.invite_id = i.invite_id
    AND s.referrer_id = i.referrer_id AND s.code = i.code
)
SELECT date_trunc('month', shared_at AT TIME ZONE 'UTC')::date AS invite_cohort_month,
       COUNT(DISTINCT referrer_id) AS inviters,
       COUNT(*) AS sent_invitations,
       COUNT(signed_up_at) AS referred_signups_30d,
       ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT referrer_id), 0), 4)
         AS invitations_per_inviter,
       ROUND(COUNT(signed_up_at)::numeric / NULLIF(COUNT(*), 0), 4)
         AS signup_rate_per_invitation,
       ROUND(COUNT(signed_up_at)::numeric / NULLIF(COUNT(DISTINCT referrer_id), 0), 4)
         AS k_factor_30d
FROM joined
GROUP BY date_trunc('month', shared_at AT TIME ZONE 'UTC')::date
ORDER BY invite_cohort_month;

-- 3. Invite cycle time for claimed referrals. This is an aggregate; it does
--    not expose the individual join token or user identity.
WITH shares AS (
  SELECT props ->> 'invite_id' AS invite_id, MIN(created_at) AS shared_at,
         MIN(actor_id::text)::uuid AS referrer_id, MIN(lower(code)) AS code,
         COUNT(DISTINCT actor_id) AS referrer_count,
         COUNT(DISTINCT lower(code)) AS code_count
  FROM referral_events
  WHERE event = 'invite_shared'
    AND actor_id IS NOT NULL AND code IS NOT NULL
    AND NULLIF(props ->> 'invite_id', '') IS NOT NULL
  GROUP BY props ->> 'invite_id'
),
signups AS (
  SELECT e.props ->> 'invite_id' AS invite_id,
         MIN(e.created_at) AS signed_up_at,
         MIN(r.referrer_id::text)::uuid AS referrer_id,
         MIN(lower(r.code)) AS code,
         COUNT(DISTINCT e.actor_id) AS referred_count,
         COUNT(DISTINCT r.referrer_id) AS referrer_count,
         COUNT(DISTINCT lower(r.code)) AS code_count
  FROM referral_events e
  JOIN referrals r ON r.id = e.referral_id AND r.referred_id = e.actor_id
  WHERE e.event = 'referral_signed_up'
    AND NULLIF(e.props ->> 'invite_id', '') IS NOT NULL
  GROUP BY e.props ->> 'invite_id'
)
SELECT date_trunc('month', s.shared_at AT TIME ZONE 'UTC')::date AS invite_cohort_month,
       COUNT(*) AS matched_signups,
       ROUND(AVG(EXTRACT(EPOCH FROM (u.signed_up_at - s.shared_at)) / 86400)::numeric, 2)
         AS mean_days_to_signup
FROM shares s
JOIN signups u ON u.invite_id = s.invite_id
  AND u.referrer_id = s.referrer_id AND u.code = s.code
WHERE s.referrer_count = 1 AND s.code_count = 1
  AND u.referred_count = 1 AND u.referrer_count = 1 AND u.code_count = 1
  AND u.signed_up_at >= s.shared_at
  AND u.signed_up_at < s.shared_at + INTERVAL '30 days'
GROUP BY date_trunc('month', s.shared_at AT TIME ZONE 'UTC')::date
ORDER BY invite_cohort_month;

-- 4. Referral-cohort LTV requires an authoritative revenue/variable-cost
--    source. referral_events alone does NOT contain customer revenue, so this
--    section is deliberately a mapping template, not executable by default.
--    Replace actual_customer_margin with a reviewed source having
--    (user_id uuid, booked_at timestamptz, revenue_minor bigint,
--     variable_cost_minor bigint). Apply one currency and a finite horizon.
--    Reward expense belongs in CAC/acquisition cost, not fabricated revenue.
/*
WITH referred_cohort AS (
  SELECT referred_id AS user_id, date_trunc('month', created_at)::date AS cohort_month
  FROM referrals
),
monthly_margin AS (
  SELECT c.cohort_month, c.user_id,
         date_trunc('month', m.booked_at)::date AS revenue_month,
         SUM(m.revenue_minor - m.variable_cost_minor) AS contribution_minor
  FROM referred_cohort c
  JOIN actual_customer_margin m ON m.user_id = c.user_id
  WHERE m.booked_at >= c.cohort_month
    AND m.booked_at < c.cohort_month + INTERVAL '36 months'
  GROUP BY c.cohort_month, c.user_id, date_trunc('month', m.booked_at)::date
)
SELECT cohort_month, COUNT(DISTINCT user_id) AS revenue_observed_customers,
       SUM(contribution_minor) AS observed_contribution_minor
FROM monthly_margin
GROUP BY cohort_month
ORDER BY cohort_month;
*/
