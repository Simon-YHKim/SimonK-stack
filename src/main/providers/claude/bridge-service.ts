import { rm } from 'node:fs/promises';
import path from 'node:path';
import type { Account, ClaudeBridgeStatus, ErrorCode, UsageSnapshot } from '../../../shared/types';
import { createEmptySnapshot } from '../../../shared/usage';
import { isId } from '../../../shared/validate';
import { isPathInside } from '../../paths';
import { ProviderError, type ClaudeBridgeController, type ProviderDeps } from '../types';
import { bridgeKeyFor, normalizeConfigDir, snapshotFromBridge, type BridgeRecord } from './bridge-data';
import {
  SETTINGS_FILE_NAME,
  SETTINGS_MAX_BYTES,
  buildBridgeCommand,
  claudeBridgeLayout,
  ensureBridgeScripts,
  errorCodeOf,
  installBridgeIntoConfigDir,
  readBridgeRecord,
  readDefaultState,
  readTextIfExists,
  readWrapState,
  uninstallBridgeFromConfigDir,
  writeDefaultState,
  type BridgeRuntime,
} from './bridge-files';
import { hasBridgeStatusLine, parseSettingsJson, statusLineCommand } from './settings-merge';

export interface ClaudeBridgeService extends ClaudeBridgeController {
  /** Widget-owned profile: install automatically (no user prompt needed, the folder is ours). */
  installForProfile(account: Account): Promise<void>;
  readUsage(account: Account): Promise<UsageSnapshot>;
  removeAccountData(account: Account): Promise<void>;
}

export interface DefaultProfile {
  configDir: string;
  key: string;
}

/**
 * The user's own Claude Code profile: `CLAUDE_CONFIG_DIR` from the widget's environment
 * when it is an absolute path outside the widget profiles, otherwise `<home>\.claude`.
 */
export function resolveDefaultProfile(deps: ProviderDeps): DefaultProfile {
  const fromEnv = deps.env.CLAUDE_CONFIG_DIR;
  if (typeof fromEnv === 'string' && fromEnv.length > 0 && path.isAbsolute(fromEnv)) {
    const insideWidget =
      isPathInside(deps.profilesRoot, fromEnv) || normalizeConfigDir(fromEnv) === normalizeConfigDir(deps.profilesRoot);
    if (!insideWidget) return { configDir: path.resolve(fromEnv), key: bridgeKeyFor(fromEnv) };
  }
  return { configDir: path.join(deps.homeDir, '.claude'), key: bridgeKeyFor(null) };
}

function withError(status: ClaudeBridgeStatus, code: ErrorCode): ClaudeBridgeStatus {
  return { ...status, errorCode: code };
}

export function createBridgeService(deps: ProviderDeps, resolveRuntime: () => BridgeRuntime): ClaudeBridgeService {
  const layout = claudeBridgeLayout(deps.bridgeRoot);
  const logger = deps.logger;

  const commandFor = async (key: string): Promise<string> => {
    await ensureBridgeScripts(deps.resourcesDir, layout);
    return buildBridgeCommand(resolveRuntime(), layout, key);
  };

  const status = async (): Promise<ClaudeBridgeStatus> => {
    const profile = resolveDefaultProfile(deps);
    const result: ClaudeBridgeStatus = {
      installed: false,
      wrapsExistingCommand: false,
      targetAccountId: null,
      lastDataAt: null,
    };
    try {
      const text = await readTextIfExists(path.join(profile.configDir, SETTINGS_FILE_NAME), SETTINGS_MAX_BYTES);
      if (text !== null) {
        const doc = parseSettingsJson(text);
        if (doc === null) {
          result.errorCode = 'parse-error';
        } else {
          result.installed = hasBridgeStatusLine(doc.data) && (statusLineCommand(doc.data) ?? '').includes(profile.key);
        }
      }
    } catch (error) {
      result.errorCode = errorCodeOf(error);
    }
    if (result.installed) {
      result.targetAccountId = (await readDefaultState(layout))?.targetAccountId ?? null;
      result.wrapsExistingCommand = (await readWrapState(layout, profile.key))?.present === true;
    }
    const record = await readBridgeRecord(layout, profile.key);
    if (record.kind === 'record') result.lastDataAt = record.record.capturedAt;
    return result;
  };

  return {
    status,

    async installDefault(target) {
      if (target.provider !== 'claude' || !isId(target.id)) {
        throw new ProviderError('internal', 'bridge target must be a claude account');
      }
      const profile = resolveDefaultProfile(deps);
      let command: string;
      try {
        command = await commandFor(profile.key);
      } catch (error) {
        return withError(await status(), errorCodeOf(error));
      }
      const now = deps.now();
      const result = await installBridgeIntoConfigDir({ configDir: profile.configDir, key: profile.key, command, layout, now });
      if (!result.ok) {
        logger.warn('default profile bridge install refused', { code: result.code });
        return withError(await status(), result.code);
      }
      const previousState = await readDefaultState(layout);
      await writeDefaultState(layout, {
        targetAccountId: target.id,
        installedAt: now,
        backupPath: result.backupPath ?? previousState?.backupPath ?? null,
      });
      logger.info('default profile bridge installed', { changed: result.changed, wrapsExisting: result.wrapsExisting });
      return status();
    },

    async uninstallDefault() {
      const profile = resolveDefaultProfile(deps);
      const result = await uninstallBridgeFromConfigDir({
        configDir: profile.configDir,
        key: profile.key,
        layout,
        now: deps.now(),
      });
      if (!result.ok) {
        logger.warn('default profile bridge uninstall refused', { code: result.code });
        return withError(await status(), result.code);
      }
      await rm(layout.defaultStatePath, { force: true });
      logger.info('default profile bridge removed', { changed: result.changed });
      return status();
    },

    async installForProfile(account) {
      const key = bridgeKeyFor(account.profileDir);
      const command = await commandFor(key);
      const result = await installBridgeIntoConfigDir({ configDir: account.profileDir, key, command, layout, now: deps.now() });
      if (!result.ok) throw new ProviderError(result.code, 'profile bridge install failed');
    },

    async readUsage(account) {
      const keys = [bridgeKeyFor(account.profileDir)];
      const state = await readDefaultState(layout);
      if (state?.targetAccountId === account.id) keys.push(resolveDefaultProfile(deps).key);
      const records: BridgeRecord[] = [];
      let invalid = false;
      for (const key of keys) {
        const read = await readBridgeRecord(layout, key);
        if (read.kind === 'record') records.push(read.record);
        else if (read.kind === 'invalid') invalid = true;
      }
      if (records.length === 0 && invalid) {
        return createEmptySnapshot({
          accountId: account.id,
          provider: 'claude',
          source: 'claude-statusline',
          state: 'error',
          errorCode: 'parse-error',
        });
      }
      return snapshotFromBridge({ accountId: account.id, records, now: deps.now() });
    },

    async removeAccountData(account) {
      const key = bridgeKeyFor(account.profileDir);
      await rm(layout.recordPath(key), { force: true });
      await rm(layout.wrapPath(key), { force: true });
    },
  };
}
