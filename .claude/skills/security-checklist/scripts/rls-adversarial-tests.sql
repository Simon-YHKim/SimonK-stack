-- rls-adversarial-tests.sql — 5 adversarial test queries for Row Level Security.
--
-- Copy this into your regression test suite (e.g. tests/security/rls.sql or
-- a Vitest test that runs these via Supabase client). Each query should FAIL
-- when RLS is working correctly. If any succeeds, your RLS is broken.
--
-- Prerequisites:
--   - Two test users: user_a (id: $UUID_A) and user_b (id: $UUID_B)
--   - JWT tokens for each user (Supabase `supabase.auth.signInWithPassword`)
--   - Run as the `anon` role with user's JWT attached, NOT service_role

-- =============================================================================
-- Test 1: Cross-user SELECT
-- As user_a, try to read user_b's rows. Expected: 0 rows returned (not error).
-- =============================================================================
-- Run as user_a:
SELECT * FROM profiles WHERE user_id = '$UUID_B';
-- Expected: 0 rows. If any row returned, RLS SELECT policy is missing or broken.

-- =============================================================================
-- Test 2: Cross-user UPDATE
-- As user_a, try to modify user_b's row. Expected: 0 rows affected.
-- =============================================================================
-- Run as user_a:
UPDATE profiles SET display_name = 'HACKED' WHERE user_id = '$UUID_B';
-- Expected: UPDATE 0. If "UPDATE 1", RLS UPDATE policy or WITH CHECK is broken.

-- =============================================================================
-- Test 3: Privilege escalation — self-promotion to admin
-- As user_a, try to set own role to admin. Expected: 0 rows affected OR error.
-- =============================================================================
-- Run as user_a:
UPDATE users SET role = 'admin' WHERE id = auth.uid();
-- Expected: UPDATE 0 (role column excluded from user's UPDATE policy) OR
-- policy rejects the update entirely. If "UPDATE 1", sensitive field is not
-- on the RLS WITH CHECK exclusion list. Add `role` to the blocked columns.

-- =============================================================================
-- Test 4: Anon role access
-- With NO JWT attached, try to read a user table. Expected: 0 rows.
-- =============================================================================
-- Run as anon (no auth header):
SELECT * FROM profiles LIMIT 10;
-- Expected: 0 rows. If rows returned, the table has a policy that lets anon
-- read. Review the USING clause of the SELECT policy.

-- =============================================================================
-- Test 5: Policy coverage audit
-- List all tables in the public schema that have ZERO RLS policies.
-- Any table in this list is a potential data leak.
-- =============================================================================
SELECT
  schemaname,
  tablename,
  CASE WHEN relrowsecurity THEN 'enabled' ELSE 'DISABLED' END AS rls_enabled,
  CASE WHEN relforcerowsecurity THEN 'forced' ELSE 'NOT_FORCED' END AS rls_forced
FROM pg_tables pt
JOIN pg_class pc ON pc.relname = pt.tablename
WHERE pt.schemaname = 'public'
  AND pt.tablename NOT IN (
    SELECT DISTINCT tablename FROM pg_policies WHERE schemaname = 'public'
  )
ORDER BY tablename;
-- Expected: 0 rows. Any listed table either (a) has RLS enabled but no
-- policies (blocks everything), or (b) has RLS disabled entirely. Case (b)
-- is a data leak. Case (a) is usually a mistake — you probably wanted at
-- least one SELECT policy.

-- =============================================================================
-- Bonus: JWT replay / forged claim test
-- This is not a SQL query but a client-side check. Save a copy of an admin
-- JWT, then try to reuse it after the admin logs out. Expected: 401.
-- Also try modifying the JWT payload (via any JWT tool) to inject
-- {"role": "service_role"} and replay. Expected: 401 (Supabase rejects
-- unsigned or wrong-signature JWTs at the gateway).
-- =============================================================================
