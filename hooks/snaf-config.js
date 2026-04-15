#!/usr/bin/env node
// snaf — shared configuration resolver
//
// Resolution order for default mode:
//   1. SNAF_DEFAULT_MODE environment variable
//   2. ~/.claude/.snaf-mode (one-line file: "on" or "off")
//   3. 'on'

const fs = require('fs');
const path = require('path');
const os = require('os');

const VALID_MODES = ['on', 'off'];

function getDefaultMode() {
  // 1. Environment variable (highest priority)
  const envMode = process.env.SNAF_DEFAULT_MODE;
  if (envMode && VALID_MODES.includes(envMode.toLowerCase())) {
    return envMode.toLowerCase();
  }

  // 2. ~/.claude/.snaf-mode — co-located with plugin scope
  try {
    const claudeMode = fs.readFileSync(
      path.join(os.homedir(), '.claude', '.snaf-mode'), 'utf8'
    ).trim().toLowerCase();
    if (VALID_MODES.includes(claudeMode)) return claudeMode;
  } catch (e) {}

  // 3. Default
  return 'on';
}

module.exports = { getDefaultMode, VALID_MODES };
