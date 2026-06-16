#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const envFile = fs.readFileSync(path.resolve(__dirname, '..', 'env', '.env.local'), 'utf8');
const env = Object.fromEntries(
  envFile.split('\n')
    .filter(line => line.includes('=') && !line.startsWith('#'))
    .map(line => { const i = line.indexOf('='); return [line.slice(0, i).trim(), line.slice(i + 1).trim()]; })
);

const audience = env.ENTRA_APP_CLIENT_ID;
const issuer = `https://login.microsoftonline.com/${env.ENTRA_APP_TENANT_ID}/v2.0`;

const files = [
  path.resolve(__dirname, '..', '.devproxy', 'dishes-api.json'),
  path.resolve(__dirname, '..', '.devproxy', 'orders-api.json')
];

for (const file of files) {
  const config = JSON.parse(fs.readFileSync(file, 'utf8'));
  config.entraAuthConfig.audience = audience;
  config.entraAuthConfig.issuer = issuer;
  fs.writeFileSync(file, JSON.stringify(config, null, 2) + '\n');
}
