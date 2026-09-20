import path from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  USER_DATA_DIR_NAME,
  bridgeRootFor,
  isPathInside,
  profileDirFor,
  profilesRootFor,
  resolveLocalDataRoot,
  resolveResourcesDir,
  userDataPathFor,
} from './paths';

describe('paths', () => {
  it('userData never reuses the v1 folder name', () => {
    expect(USER_DATA_DIR_NAME).not.toBe('ai-usage-taskbar-widget');
    expect(userDataPathFor(path.resolve('/appdata'))).toBe(path.join(path.resolve('/appdata'), 'AIUsageWidgetV2'));
  });

  it('local data root comes from LOCALAPPDATA or an override', () => {
    const local = path.resolve('/local');
    expect(resolveLocalDataRoot({ LOCALAPPDATA: local })).toBe(path.join(local, 'AIUsageWidget'));
    expect(resolveLocalDataRoot({}, path.resolve('/tmp/x'))).toBe(path.resolve('/tmp/x'));
    expect(() => resolveLocalDataRoot({})).toThrow();
    const root = resolveLocalDataRoot({ LOCALAPPDATA: local });
    expect(profilesRootFor(root)).toBe(path.join(root, 'profiles'));
    expect(bridgeRootFor(root)).toBe(path.join(root, 'bridge'));
  });

  it('isPathInside handles siblings and equality', () => {
    const base = path.resolve('/a/b');
    expect(isPathInside(base, path.join(base, 'c'))).toBe(true);
    expect(isPathInside(base, base)).toBe(false);
    expect(isPathInside(base, path.resolve('/a/bc'))).toBe(false);
    expect(isPathInside(base, path.resolve('/a'))).toBe(false);
  });

  it('profileDirFor validates provider and id', () => {
    const root = path.resolve('/profiles');
    expect(profileDirFor(root, 'codex', 'acc-1')).toBe(path.join(root, 'codex', 'acc-1'));
    expect(() => profileDirFor(root, 'codex', '../escape')).toThrow();
    expect(() => profileDirFor(root, 'codex', '')).toThrow();
    expect(() => profileDirFor(root, 'gemini' as never, 'a')).toThrow();
  });

  it('resources dir depends on packaging', () => {
    const input = { resourcesPath: path.resolve('/res'), appPath: path.resolve('/app') };
    expect(resolveResourcesDir({ ...input, isPackaged: true })).toBe(path.join(input.resourcesPath, 'resources'));
    expect(resolveResourcesDir({ ...input, isPackaged: false })).toBe(path.join(input.appPath, 'resources'));
  });
});
