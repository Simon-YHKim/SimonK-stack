/**
 * Custom expo-router linking config.
 *
 * expo-router derives most linking from the file-based routes automatically.
 * Use this ONLY when you need to:
 *  - add extra URL prefixes (custom scheme + multiple domains)
 *  - remap an external path shape to an internal route
 *  - preserve query params (attribution) through the parse
 *
 * Wire it in app/_layout.tsx by passing `linking` to the router, or rely on
 * expo-router defaults and keep this as a reference for getStateFromPath.
 */
import * as Linking from 'expo-linking';
import type { LinkingOptions } from '@react-navigation/native';

// Custom scheme + every verified domain. Prefer https domains; scheme is fallback.
export const prefixes = [
  Linking.createURL('/'), // myapp:// (from app.json "scheme")
  'https://app.example.com',
];

/**
 * Pull attribution params off any incoming URL without losing them.
 * Returns a flat record; persist/forward as needed (see deferred-deeplink.ts).
 */
export function extractAttribution(url: string): Record<string, string> {
  const { queryParams } = Linking.parse(url);
  const keep = ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'campaign'];
  const out: Record<string, string> = {};
  for (const k of keep) {
    const v = queryParams?.[k];
    if (typeof v === 'string') out[k] = v;
  }
  return out;
}

/**
 * Example explicit map for expo-router. Adjust `screens` to your route tree.
 * Query params survive to the target screen via useLocalSearchParams().
 */
export const linking: LinkingOptions<Record<string, unknown>> = {
  prefixes,
  config: {
    screens: {
      'post/[id]': 'post/:id',
      'invite/[code]': 'invite/:code',
      // Catch-all fallback so unknown paths land somewhere safe (no crash).
      '+not-found': '*',
    },
  },
};
