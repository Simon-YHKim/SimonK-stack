-- referral-program-builder :: schema
-- Postgres / Supabase. Adjust users(id) FK to your auth schema (e.g. auth.users).
-- 원칙: referrals(관계·상태) 와 reward_ledger(불변 원장) 분리. 보상 금액은 referrals 에 직접 쓰지 않는다.

-- ---------------------------------------------------------------------------
-- 1. 초대코드 (사용자당 안정 코드 1개 + 캠페인 일회성 코드 별도 발급 가능)
-- ---------------------------------------------------------------------------
CREATE TABLE referral_codes (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  code        TEXT NOT NULL,                 -- crypto random, 추측 불가 (순차 ID 금지)
  kind        TEXT NOT NULL DEFAULT 'personal', -- personal | campaign
  is_active   BOOLEAN NOT NULL DEFAULT true,
  max_uses    INTEGER,                       -- NULL = 무제한, 캠페인 코드는 제한
  used_count  INTEGER NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX referral_codes_code_uidx ON referral_codes (lower(code));
-- personal 코드는 소유자당 1개만
CREATE UNIQUE INDEX referral_codes_owner_personal_uidx
  ON referral_codes (owner_id) WHERE kind = 'personal';

-- ---------------------------------------------------------------------------
-- 2. 추천 관계 + 상태 머신
--    status: pending -> qualified -> rewarded
--                    \-> rejected (가드 차단)
--            qualified -> clawed_back (환불/취소 회수)
-- ---------------------------------------------------------------------------
CREATE TYPE referral_status AS ENUM (
  'pending', 'qualified', 'rewarded', 'rejected', 'clawed_back'
);

CREATE TABLE referrals (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  referrer_id     UUID NOT NULL REFERENCES users(id),
  referred_id     UUID NOT NULL REFERENCES users(id),
  code            TEXT NOT NULL,
  status          referral_status NOT NULL DEFAULT 'pending',
  attributed_via  TEXT,                      -- deeplink | deferred_deeplink | web_cookie | manual
  reject_reason   TEXT,                      -- 가드 차단 시 사유 (self_referral | multi_account | self_click | not_qualified | code_bruteforce)
  qualified_at    TIMESTAMPTZ,
  rewarded_at     TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT referrals_no_self CHECK (referrer_id <> referred_id)
);
-- 한 명은 한 번만 피추천 (다중계정 가드의 1차 방어선)
CREATE UNIQUE INDEX referrals_referred_uidx ON referrals (referred_id);
CREATE INDEX referrals_referrer_idx ON referrals (referrer_id);

-- ---------------------------------------------------------------------------
-- 3. 보상 원장 (APPEND-ONLY). 지급/회수 모두 행 추가로만 표현.
--    회수(claw-back)는 음수 amount 또는 reversal 행으로 기록.
-- ---------------------------------------------------------------------------
CREATE TABLE reward_ledger (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID NOT NULL REFERENCES users(id),
  referral_id      UUID NOT NULL REFERENCES referrals(id),
  role             TEXT NOT NULL,            -- referrer | referred
  kind             TEXT NOT NULL,            -- credit | cash | free_period | gift
  amount           INTEGER NOT NULL,         -- 최소단위(원/cent). 회수는 음수.
  currency         TEXT NOT NULL DEFAULT 'krw',
  state            TEXT NOT NULL DEFAULT 'granted', -- granted | capped | reversed
  reward_rule_version TEXT NOT NULL,         -- 멱등키 구성요소
  idempotency_key  TEXT NOT NULL,            -- referral_id + role + reward_rule_version
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- 같은 자격 이벤트 재진입 시 중복 적립 금지
CREATE UNIQUE INDEX reward_ledger_idem_uidx ON reward_ledger (idempotency_key);
CREATE INDEX reward_ledger_user_idx ON reward_ledger (user_id);

-- 사용자 보상 잔액은 원장 SUM 으로 산출 (저장하지 않는다)
-- SELECT user_id, currency, SUM(amount) FROM reward_ledger
--   WHERE state IN ('granted', 'reversed') GROUP BY user_id, currency;
-- capped 행은 미지급이고, reversed 행은 음수 회수이므로 둘을 혼동하지 않는다.

-- ---------------------------------------------------------------------------
-- 4. K-factor / 퍼널 측정용 raw 이벤트
-- ---------------------------------------------------------------------------
CREATE TABLE referral_events (
  id          BIGSERIAL PRIMARY KEY,
  event       TEXT NOT NULL,                 -- invite_shared | invite_clicked | invite_installed
                                             -- | referral_signed_up | referral_qualified | reward_granted
  actor_id    UUID,                          -- 이벤트 주체 (공유=추천인, 가입=피추천인)
  code        TEXT,
  referral_id UUID REFERENCES referrals(id),
  props       JSONB,                         -- 검증된 invite_id, platform, campaign 등
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX referral_events_event_idx ON referral_events (event, created_at);
CREATE INDEX referral_events_code_idx  ON referral_events (code);

-- RLS (Supabase): 사용자는 본인 관련 행만 읽기. 적립/상태 변경은 service role/Edge Function 에서만.
-- ALTER TABLE referrals       ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE reward_ledger   ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE referral_events ENABLE ROW LEVEL SECURITY;
