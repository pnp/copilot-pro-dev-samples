const fs = require("fs");
const path = require("path");

// Increment the version number in the manifest file
const manifestPath = path.resolve(__dirname, "../appPackage/manifest.json");
const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
const version = manifest.version.split(".");
version[2] = parseInt(version[2]) + 1;
manifest.version = version.join(".");
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
console.log(`Incremented version to ${manifest.version}`);
