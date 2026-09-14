import { ERROR_MESSAGE_KEYS, type Translator } from '../../shared/i18n';
import type { IpcError, PreloadApi } from '../../shared/ipc';
import type { ErrorCode } from '../../shared/types';

export type Api = PreloadApi;

export function ipcErrorCode(error: IpcError): ErrorCode {
  if (error.detail !== undefined) return error.detail;
  return error.code === 'not-implemented' ? 'not-implemented' : 'internal';
}

export function describeError(t: Translator, code: ErrorCode): string {
  return t('errorDetail', { error: t(ERROR_MESSAGE_KEYS[code]) });
}
