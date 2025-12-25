/**
 * Global Configuration Utilities
 *
 * Read/write shared config file ~/.auto-claude/config.json
 * This file is shared between frontend (Electron) and backend (Python).
 */

import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import path from 'path';
import { app } from 'electron';

export interface GlobalConfig {
  customHaikuModelId?: string;
  customSonnetModelId?: string;
  customOpusModelId?: string;
  globalAnthropicBaseUrl?: string;
  globalAnthropicApiKey?: string;
  claudeAuthMode?: 'oauth' | 'apikey';
}

/**
 * Get the path to the global config file
 */
export function getGlobalConfigPath(): string {
  const homeDir = app.getPath('home');
  return path.join(homeDir, '.auto-claude', 'config.json');
}

/**
 * Load global configuration from ~/.auto-claude/config.json
 */
export function loadGlobalConfig(): GlobalConfig {
  const configPath = getGlobalConfigPath();

  if (!existsSync(configPath)) {
    return {};
  }

  try {
    const content = readFileSync(configPath, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    console.error('[loadGlobalConfig] Failed to parse config file:', error);
    return {};
  }
}

/**
 * Save global configuration to ~/.auto-claude/config.json
 */
export function saveGlobalConfig(config: GlobalConfig): void {
  const configPath = getGlobalConfigPath();
  const configDir = path.dirname(configPath);

  // Create directory if it doesn't exist
  if (!existsSync(configDir)) {
    mkdirSync(configDir, { recursive: true });
  }

  try {
    writeFileSync(configPath, JSON.stringify(config, null, 2));
    console.log('[saveGlobalConfig] Successfully saved config to', configPath);
  } catch (error) {
    console.error('[saveGlobalConfig] Failed to save config file:', error);
    throw error;
  }
}

/**
 * Update specific fields in global config
 */
export function updateGlobalConfig(updates: Partial<GlobalConfig>): void {
  const currentConfig = loadGlobalConfig();
  const newConfig = { ...currentConfig, ...updates };

  // Remove undefined values
  Object.keys(newConfig).forEach(key => {
    if (newConfig[key as keyof GlobalConfig] === undefined) {
      delete newConfig[key as keyof GlobalConfig];
    }
  });

  saveGlobalConfig(newConfig);
}
