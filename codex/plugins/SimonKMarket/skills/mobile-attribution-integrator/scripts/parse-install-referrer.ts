/**
 * Pure normalization of Google Play's install_referrer string.
 *
 * The caller obtains the string with the official Install Referrer client once
 * after first launch. This helper does not call Google Play, route a deep link,
 * log click identifiers, or verify that a claimed campaign actually ran.
 */
export type InstallReferrerResult = {
  channel: 'google' | 'meta' | 'tiktok' | 'organic' | null;
  campaign: string | null;
  medium: string | null;
  matchedBy: 'install_referrer' | 'none';
  verified: false;
  reason: 'invalid_referrer' | 'duplicate_parameter' | 'invalid_value'
    | 'missing_source' | 'unknown_source' | null;
};

const MAX_REFERRER_LENGTH = 4096;
const MAX_FIELD_LENGTH = 128;
const SOURCE_TO_CHANNEL: Record<string, NonNullable<InstallReferrerResult['channel']>> = {
  google: 'google', google_ads: 'google', googleads: 'google', adwords: 'google',
  facebook: 'meta', instagram: 'meta', meta: 'meta',
  tiktok: 'tiktok',
  organic: 'organic',
};

function unmatched(reason: NonNullable<InstallReferrerResult['reason']>): InstallReferrerResult {
  return {
    channel: null, campaign: null, medium: null,
    matchedBy: 'none', verified: false, reason,
  };
}

function normalizeField(value: string | null): string | null {
  if (value === null) return null;
  if (/[\u0000-\u001f\u007f\ufffd]/u.test(value)) return null;
  const normalized = value.trim().toLowerCase();
  if (!normalized || normalized.length > MAX_FIELD_LENGTH) return null;
  return normalized;
}

export function parseInstallReferrer(raw: string | null | undefined): InstallReferrerResult {
  if (typeof raw !== 'string' || !raw || raw.length > MAX_REFERRER_LENGTH) {
    return unmatched('invalid_referrer');
  }

  let params: URLSearchParams;
  try {
    if (/^https?:\/\//iu.test(raw)) {
      const url = new URL(raw);
      params = url.searchParams;
    } else if (/^[a-z][a-z0-9+.-]*:/iu.test(raw)) {
      return unmatched('invalid_referrer');
    } else {
      params = new URLSearchParams(raw.startsWith('?') ? raw.slice(1) : raw);
    }
  } catch {
    return unmatched('invalid_referrer');
  }

  for (const key of ['utm_source', 'utm_campaign', 'utm_medium']) {
    if (params.getAll(key).length > 1) return unmatched('duplicate_parameter');
  }

  const sourceRaw = params.get('utm_source');
  if (sourceRaw === null) return unmatched('missing_source');
  const source = normalizeField(sourceRaw);
  const campaign = params.get('utm_campaign');
  const medium = params.get('utm_medium');
  if (!source || (campaign !== null && !normalizeField(campaign))
      || (medium !== null && !normalizeField(medium))) {
    return unmatched('invalid_value');
  }

  const channel = SOURCE_TO_CHANNEL[source];
  if (!channel) return unmatched('unknown_source');
  return {
    channel,
    campaign: normalizeField(campaign),
    medium: normalizeField(medium),
    matchedBy: 'install_referrer',
    verified: false,
    reason: null,
  };
}
