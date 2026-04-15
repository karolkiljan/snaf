#!/usr/bin/env node
// snaf — SessionStart activation hook
//
// Runs on every session start:
//   1. Writes flag file at ~/.claude/.snaf-active (statusline reads this)
//   2. Emits snaf ruleset as SessionStart context — reads SKILL.md at runtime
//      so edits to the source of truth propagate automatically, no duplication.
//   3. Detects missing statusline config and emits setup nudge

const fs = require('fs');
const path = require('path');
const os = require('os');
const { getDefaultMode } = require('./snaf-config');

const claudeDir = path.join(os.homedir(), '.claude');
const flagPath = path.join(claudeDir, '.snaf-active');
const settingsPath = path.join(claudeDir, 'settings.json');

const mode = getDefaultMode();

// "off" mode — skip activation entirely, don't write flag or emit rules
if (mode === 'off') {
  try { fs.unlinkSync(flagPath); } catch (e) {}
  process.stdout.write('OK');
  process.exit(0);
}

// 1. Write flag file
try {
  fs.mkdirSync(path.dirname(flagPath), { recursive: true });
  fs.writeFileSync(flagPath, mode);
} catch (e) {
  // Silent fail — flag is best-effort, don't block the hook
}

// 2. Emit snaf ruleset.
//    Reads SKILL.md at runtime so edits propagate automatically — no hardcoded
//    duplication. Fallback to minimal hardcoded rules for standalone installs.

let skillContent = '';
try {
  skillContent = fs.readFileSync(
    path.join(__dirname, '..', 'skills', 'snaf', 'SKILL.md'), 'utf8'
  );
} catch (e) { /* standalone install — will use fallback below */ }

let output;

if (skillContent) {
  // Strip YAML frontmatter
  const body = skillContent.replace(/^---[\s\S]*?---\s*/, '');
  output = 'SNAF TRYB AKTYWNY\n\n' + body;
} else {
  // Fallback when SKILL.md is not found (standalone hook install without skills dir).
  output =
    'SNAF TRYB AKTYWNY. ' +
    '4 PRAW: ' +
    '1. ZAKAZ PIERDOŁÓW: zakaz Oczywiście!/Chętnie/właściwie/po prostu/jednak/ponadto/można by rozważyć. ZERO emoji (wyjątek: 🔴🟡🔵❓ severity w code review). KONIEC ODPOWIEDZI = FAKT LUB KOD. Gdy brak info: załóż typowy przypadek, napisz założenie, odpowiedz. Nie pytaj. Zacznij od rzeczy. ' +
    '2. ŁAMANA GRAMATYKA: \'ty robi\' nie \'zrobisz\'. Bezokolicznik = wszystkie czasy: \'naprawić\' nie \'naprawiłem\'. Pomiń czasownik gdy sens jasny: token wygasły. Mianownik zawsze: middleware nie przez middleware. Pomiń \'że\' → dwukropek. ' +
    '3. PRYMITYWNY SŁOWNIK: implementować→robić, konfigurować→dawać, uruchamiać→puszczać, zweryfikować→sprawdzić, zapewnić→daj. ' +
    '4. MAKSYMALNA KOMPRESJA: jeden fakt=jedno zdanie. \'=\' i \'→\' zamiast opisów. Tryb rozkazujący: zrób nie należy zrobić. Raport→przeszły (naprawił). Instrukcja→rozkaz (napraw). Pytanie = max 1-3 zdania + 1 kod, zero nagłówków nawet złożone pytania. ' +
    'Wzorzec: [rzecz] [problem]. [fix]. ' +
    '\'normalny tryb\' lub \'stop snaf\' dezaktywuje.';
}

// 3. Detect missing statusline config — nudge Claude to help set it up
try {
  let hasStatusline = false;
  if (fs.existsSync(settingsPath)) {
    const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
    if (settings.statusLine) {
      hasStatusline = true;
    }
  }

  if (!hasStatusline) {
    const isWindows = process.platform === 'win32';
    const scriptName = isWindows ? 'snaf-statusline.ps1' : 'snaf-statusline.sh';
    const scriptPath = path.join(__dirname, scriptName);
    const command = isWindows
      ? `powershell -ExecutionPolicy Bypass -File "${scriptPath}"`
      : `bash "${scriptPath}"`;
    const statusLineSnippet =
      '"statusLine": { "type": "command", "command": ' + JSON.stringify(command) + ' }';
    output += '\n\nSTATUSLINE SETUP NEEDED: The snaf plugin includes a statusline badge showing [SNAF] when active. ' +
      'It is not configured yet. ' +
      'To enable, add this to ~/.claude/settings.json: ' +
      statusLineSnippet + ' ' +
      'Proactively offer to set this up for the user on first interaction.';
  }
} catch (e) {
  // Silent fail — don't block session start over statusline detection
}

process.stdout.write(output);
