import { createDecipheriv } from 'node:crypto';
import { existsSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import koffi from 'koffi';

/** Read the signed-in Grok Bot desktop session without changing or refreshing it. */
export function readGrokBotAccessToken(appData = process.env.APPDATA): string | null {
  if (process.platform !== 'win32' || !appData) return null;
  const root = path.join(appData, 'Grok Bot');
  if (!existsSync(path.join(root, 'Local State')) || !existsSync(path.join(root, 'sand-secrets.json'))) return null;
  const readJson = (name: string): Record<string, unknown> => {
    const file = path.join(root, name);
    if (statSync(file).size > 1_048_576) throw new Error('Grok Bot data is too large');
    const value: unknown = JSON.parse(readFileSync(file, 'utf8'));
    if (value === null || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid Grok Bot data');
    return value as Record<string, unknown>;
  };
  const state = readJson('Local State');
  const osCrypt = state.os_crypt as Record<string, unknown> | undefined;
  if (typeof osCrypt?.encrypted_key !== 'string') throw new Error('Missing Grok Bot encryption key');
  const encryptedKey = Buffer.from(osCrypt.encrypted_key, 'base64');
  if (encryptedKey.subarray(0, 5).toString('ascii') !== 'DPAPI') throw new Error('Unsupported Grok Bot key');

  const blob = koffi.struct({ cbData: 'uint32', pbData: 'void *' });
  const unprotect = koffi.load('crypt32.dll').func(
    'int CryptUnprotectData(const void *input, void *description, const void *entropy, void *reserved, void *prompt, uint32 flags, _Out_ void *output)',
  );
  const localFree = koffi.load('kernel32.dll').func('void *LocalFree(void *memory)');
  const encrypted = encryptedKey.subarray(5);
  const output: { cbData: number; pbData: unknown } = { cbData: 0, pbData: null };
  const ok: unknown = unprotect(koffi.as({ cbData: encrypted.length, pbData: encrypted }, koffi.pointer(blob)),
    null, null, null, null, 1, koffi.as(output, koffi.pointer(blob)));
  if (!ok || output.pbData === null || output.cbData !== 32) {
    if (output.pbData !== null) localFree(output.pbData);
    throw new Error('Could not unlock Grok Bot session');
  }
  const key = Buffer.from(koffi.decode(output.pbData, 'uint8', output.cbData) as number[]);
  localFree(output.pbData);
  try {
    const secrets = readJson('sand-secrets.json');
    const rawAccounts = secrets['cursor-accounts'];
    const accounts = typeof rawAccounts === 'string' ? JSON.parse(rawAccounts) as unknown : rawAccounts;
    if (accounts === null || typeof accounts !== 'object') return null;
    const store = accounts as { active?: unknown; accounts?: Record<string, Record<string, unknown>> };
    const encryptedToken = typeof store.active === 'string' ? store.accounts?.[store.active]?.['cursor-access-token'] : undefined;
    if (typeof encryptedToken !== 'string') return null;
    const raw = Buffer.from(encryptedToken, 'base64');
    if (raw.subarray(0, 3).toString('ascii') !== 'v10' || raw.length < 3 + 12 + 16) {
      throw new Error('Unsupported Grok Bot token format');
    }
    const nonce = raw.subarray(3, 15);
    const cipherText = raw.subarray(15, -16);
    const tag = raw.subarray(-16);
    const decipher = createDecipheriv('aes-256-gcm', key, nonce);
    decipher.setAuthTag(tag);
    return Buffer.concat([decipher.update(cipherText), decipher.final()]).toString('utf8');
  } finally {
    key.fill(0);
  }
}
