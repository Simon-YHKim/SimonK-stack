import path from 'node:path';
import { isProviderId, type ProviderId } from '../shared/types';
import { ID_PATTERN } from '../shared/validate';

/** Roaming userData folder name. Must differ from v1's 'ai-usage-taskbar-widget'. */
export const USER_DATA_DIR_NAME = 'AIUsageWidgetV2';
/** Local (non-roaming) root for CLI profiles and bridge data. */
export const LOCAL_DATA_DIR_NAME = 'AIUsageWidget';
export const PROFILES_DIR_NAME = 'profiles';
export const BRIDGE_DIR_NAME = 'bridge';

export function userDataPathFor(appDataDir: string): string {
  return path.join(appDataDir, USER_DATA_DIR_NAME);
}

/** `%LOCALAPPDATA%\AIUsageWidget`, or `override` when given (smoke/tests). */
export function resolveLocalDataRoot(env: Readonly<Record<string, string | undefined>>, override?: string): string {
  if (override !== undefined && override.length > 0) return path.resolve(override);
  const localAppData = env.LOCALAPPDATA;
  if (localAppData === undefined || localAppData.length === 0) {
    throw new Error('LOCALAPPDATA is not set');
  }
  return path.join(localAppData, LOCAL_DATA_DIR_NAME);
}

export function profilesRootFor(localDataRoot: string): string {
  return path.join(localDataRoot, PROFILES_DIR_NAME);
}

export function bridgeRootFor(localDataRoot: string): string {
  return path.join(localDataRoot, BRIDGE_DIR_NAME);
}

function comparable(p: string): string {
  const resolved = path.resolve(p);
  return process.platform === 'win32' ? resolved.toLowerCase() : resolved;
}

/** True when `child` is strictly inside `parent` (not equal, not a sibling prefix). */
export function isPathInside(parent: string, child: string): boolean {
  const rel = path.relative(comparable(parent), comparable(child));
  return rel.length > 0 && !rel.startsWith('..') && !path.isAbsolute(rel);
}

/** `<profilesRoot>\<provider>\<accountId>` with strict id validation. */
export function profileDirFor(profilesRoot: string, provider: ProviderId, accountId: string): string {
  if (!isProviderId(provider)) throw new Error('invalid provider');
  if (!ID_PATTERN.test(accountId)) throw new Error('invalid account id');
  const dir = path.resolve(profilesRoot, provider, accountId);
  if (!isPathInside(profilesRoot, dir)) throw new Error('profile dir escapes root');
  return dir;
}

export interface ResourcesDirInput {
  isPackaged: boolean;
  resourcesPath: string;
  appPath: string;
}

/** Folder holding `resources/` assets (tray icons, provider icons, claude-bridge). */
export function resolveResourcesDir(input: ResourcesDirInput): string {
  return input.isPackaged ? path.join(input.resourcesPath, 'resources') : path.join(input.appPath, 'resources');
}
