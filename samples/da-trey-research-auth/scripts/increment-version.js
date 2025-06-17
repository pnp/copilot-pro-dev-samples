const fs = require('fs')
const path = require('path')
const { stdout } = require('process')
const semver = require('semver')

const manifestPath = path.join(__dirname, '../appPackage/manifest.json')
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'))
const newVersion = semver.inc(manifest.version, 'patch')

manifest.version = newVersion
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf8')

console.log(`Updated version to ${newVersion}`);