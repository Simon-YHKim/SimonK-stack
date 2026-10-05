-- rls-adversarial-tests.sql — example RLS checks; adapt to the real schema.
--
-- Do not run UPDATE examples on production. A SELECT returning zero rows and
-- an UPDATE affecting zero rows can be the expected result; SQL need not error.
-- Audit actual grants, exposed schemas, roles and intended sharing separately.
--
-- Prerequisites:
--   - Two test users: user_a (id: $UUID_A) and user_b (id: $UUID_B)
--   - JWT tokens for each user (Supabase `supabase.auth.signInWithPassword`)
--   - Run authenticated requests with each user's JWT, and anonymous requests
--     without one. Never test through service_role/BYPASSRLS as an end user.

-- =============================================================================
-- Test 1: Cross-user SELECT
-- As user_a, try to read user_b's rows. Expected: 0 rows returned (not error).
-- =============================================================================
-- Run as user_a:
SELECT * FROM profiles WHERE user_id = '$UUID_B';
-- Expected: 0 rows for a private profile; allowed sharing needs a separate test.

-- =============================================================================
-- Test 2: Cross-user UPDATE
-- As user_a, try to modify user_b's row. Expected: 0 rows affected.
-- =============================================================================
-- Run as user_a:
UPDATE profiles SET display_name = 'HACKED' WHERE user_id = '$UUID_B';
-- Expected: UPDATE 0 or access denied, for a non-shared private profile.

-- =============================================================================
-- Test 3: Privilege escalation — self-promotion to admin
-- As user_a, try to set own role to admin. Expected: 0 rows affected OR error.
-- =============================================================================
-- Run as user_a:
UPDATE users SET role = 'admin' WHERE id = auth.uid();
-- Expected: UPDATE 0 or access denied. RLS WITH CHECK limits rows, not columns.
-- Protect role with a separate privileged table or restricted UPDATE grants;
-- verify that the stored value is unchanged even if the API returns success.

-- =============================================================================
-- Test 4: Anon role access
-- With NO JWT attached, try to read a user table. Expected: 0 rows.
-- =============================================================================
-- Run as anon (no auth header):
SELECT * FROM profiles LIMIT 10;
-- Expected: 0 rows or access denied for a private profile. A public table may
-- intentionally return rows; judge against the intended authorization contract.

-- =============================================================================
-- Test 5: RLS state and policy inventory (read-only)
-- A policy may exist while RLS is disabled. Zero policies with RLS enabled
-- means default deny, not automatic data exposure.
-- =============================================================================
SELECT
  n.nspname AS schema_name,
  c.relname AS table_name,
  c.relrowsecurity AS rls_enabled,
  c.relforcerowsecurity AS force_owner_rls,
  count(p.oid) AS policy_count
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_policy p ON p.polrelid = c.oid
WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
GROUP BY n.nspname, c.relname, c.relrowsecurity, c.relforcerowsecurity
ORDER BY n.nspname, c.relname;
-- Review every exposed row with rls_enabled=false and any unexpected grants.

-- =============================================================================
-- Bonus: JWT replay / forged claim test
-- This is not a SQL query but a client-side check. Save a copy of an admin
-- JWT, then check whether the application's revocation/expiry policy actually
-- rejects it. Logout alone does not guarantee immediate JWT revocation.
-- A payload modified without a valid signature must be rejected by the API.
-- =============================================================================
