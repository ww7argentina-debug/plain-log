import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

const requiredFiles = ['style.css', 'index.php', 'functions.php'];

for (const file of requiredFiles) {
  if (!statSync(file, { throwIfNoEntry: false })?.isFile()) {
    throw new Error(`Missing required theme file: ${file}`);
  }
}

const stylesheet = readFileSync('style.css', 'utf8');
const header = stylesheet.slice(0, 8192).match(/^\s*\/\*([\s\S]*?)\*\//)?.[1];

if (!header) {
  throw new Error('style.css must begin with a theme header comment');
}

function headerValue(name) {
  const match = header.match(new RegExp(`^[ \\t]*\\*?[ \\t]*${name}:[ \\t]*([^\\r\\n]*)$`, 'm'));
  const value = match?.[1].trim();

  if (!value) {
    throw new Error(`Missing or empty ${name} in style.css theme header`);
  }

  return value;
}

headerValue('Theme Name');
const version = headerValue('Version');
const textDomain = headerValue('Text Domain');

if (!/^\d+(?:\.\d+)*(?:[-+][0-9A-Za-z.-]+)?$/.test(version)) {
  throw new Error('Invalid Version in style.css theme header');
}

if (textDomain !== 'plain-log') {
  throw new Error('Text Domain must match the plain-log theme directory');
}

const theme = JSON.parse(readFileSync('theme.json', 'utf8'));

if (!theme || typeof theme !== 'object' || Array.isArray(theme) || !Number.isInteger(theme.version) || theme.version < 1) {
  throw new Error('theme.json must be an object with a positive integer version');
}

for (const key of ['settings', 'styles']) {
  if (key in theme && (!theme[key] || typeof theme[key] !== 'object' || Array.isArray(theme[key]))) {
    throw new Error(`theme.json ${key} must be an object`);
  }
}

function checkJavaScript(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);

    if (entry.isDirectory()) {
      checkJavaScript(path);
    } else if (entry.isFile() && entry.name.endsWith('.js')) {
      const result = spawnSync(process.execPath, ['--check', path], { stdio: 'inherit' });

      if (result.error || result.status !== 0) {
        throw result.error || new Error(`JavaScript syntax check failed: ${path}`);
      }

      console.log(`JavaScript syntax OK: ${path}`);
    }
  }
}

checkJavaScript('assets');
console.log('Theme structure and theme.json basic checks passed');
