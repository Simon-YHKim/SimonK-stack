import { contextBridge, ipcRenderer } from 'electron';
import { PRELOAD_GLOBAL } from '../shared/ipc';
import { createPreloadApi } from './bridge';

contextBridge.exposeInMainWorld(PRELOAD_GLOBAL, createPreloadApi(ipcRenderer));
