import assert from "node:assert/strict";
import { readFile, readdir, stat } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { marked } from "marked";

const dist = path.resolve("dist");
const catalog = JSON.parse(await readFile("public/samples.json", "utf8"));
const home = await readFile(path.join(dist, "index.html"), "utf8");
const canonical = home.match(/<link rel="canonical" href="([^"]+)"/)?.[1];
assert.ok(canonical, "Build the gallery before running tests.");
const base = new URL(canonical).pathname;
const statsBase = "https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/";
const trackerCount = (html) => (html.match(/<img\b[^>]*src="https:\/\/m365-visitor-stats\.azurewebsites\.net\//g) ?? []).length;
const pages = ["", "getting-started", "contributors", "contributing", "whats-new"];
const htmlFor = (route) => readFile(path.join(dist, route, "index.html"), "utf8");

test("all community pages use the shared navigation and exactly one route-specific tracker", async () => {
  for (const route of pages) {
    const html = await htmlFor(route);
    const nav = html.match(/<nav class="desktop-nav"[^>]*>([\s\S]*?)<\/nav>/)?.[1];
    assert.ok(nav, `Missing primary navigation on ${route}`);
    const labels = [...nav.matchAll(/<a\b[^>]*>([\s\S]*?)<\/a>/g)]
      .map((match) => match[1].replace(/<[^>]*>/g, "").replaceAll("&#39;", "'").trim());
    assert.deepEqual(labels, ["Community", "Samples", "Getting started", "Contributors", "Contributing", "What's new", "GitHub"]);
    assert.ok(nav.includes(`href="${base}"${route ? "" : ' aria-current="page"'}>Samples</a>`), `Samples should link home on ${route}`);
    assert.equal((nav.match(/aria-current="page"/g) ?? []).length, 1, `Wrong active navigation on ${route}`);
    assert.match(nav, /https:\/\/aka\.ms\/community\/home[^]*?Community[^]*?<svg/);
    assert.equal(trackerCount(html), 1, `Duplicate tracker on ${route}`);
    assert.ok(html.includes(`src="${statsBase}${route}"`), `Wrong tracker key on ${route}`);
    assert.ok(html.includes(`href="${base}${route ? `${route}/` : ""}"`), `Wrong canonical/base on ${route}`);
    assert.match(html, /role="switch" aria-checked="false"/);
    assert.match(html, /contributor-badge\.webp/);
    const contributionCallout = html.match(/<aside class="contribution-callout"[\s\S]*?<\/aside>/)?.[0];
    assert.ok(contributionCallout, `Missing contribution callout on ${route}`);
    for (const resource of ["https://aka.ms/community/calls", "https://aka.ms/community/recognition"]) {
      assert.ok(contributionCallout.includes(resource), `${route}: missing community resource ${resource}`);
    }
  }
});

test("the repository README links the captured gallery screenshot to GitHub Pages", async () => {
  const readme = await readFile(path.join("..", "README.md"), "utf8");
  assert.match(readme, /\[!\[[^\]]+\]\(\.\/assets\/sample-gallery\.png\)\]\(https:\/\/pnp\.github\.io\/copilot-pro-dev-samples\/\)/);
  const screenshot = await readFile(path.join("..", "assets", "sample-gallery.png"));
  assert.equal(screenshot.subarray(0, 8).toString("hex"), "89504e470d0a1a0a");
  assert.equal(screenshot.readUInt32BE(16), 1440);
  assert.equal(screenshot.readUInt32BE(20), 1180);
});

test("contributor documentation uses existing local links and community resources", async () => {
  const root = path.resolve("..");
  const documents = [
    path.join(root, "README.md"),
    path.join(root, "CONTRIBUTING.md"),
    path.join(root, "SUPPORT.md"),
    path.join(root, ".github", "pull_request_template.md"),
    path.resolve("README.md"),
  ];
  for (const file of documents) {
    const content = await readFile(file, "utf8");
    const targets = [];
    marked.walkTokens(marked.lexer(content), (token) => {
      if (token.type === "link" || token.type === "image") targets.push(token.href);
    });
    for (const href of targets) {
      if (/^(?:[a-z][a-z\d+.-]*:|\/\/|#)/i.test(href)) continue;
      const local = decodeURIComponent(href.split(/[?#]/)[0]);
      const destination = local.startsWith("/")
        ? path.resolve(root, `.${local}`)
        : path.resolve(path.dirname(file), local);
      assert.ok(await stat(destination).catch(() => null), `${file}: broken local link ${href}`);
    }
    if (file === path.join(root, "README.md") || file === path.join(root, "CONTRIBUTING.md")) {
      for (const resource of ["https://aka.ms/community/calls", "https://aka.ms/community/request/demo", "https://aka.ms/community/recognition", "https://pnp.github.io/sharing-is-caring/"]) {
        assert.ok(content.includes(resource), `${file}: missing community resource ${resource}`);
      }
    }
  }
});

test("the homepage opens directly into the full catalog ordered by latest update", () => {
  assert.doesNotMatch(home, /featured-sample|Featured sample/);
  assert.match(home, /class="catalog-backdrop"[^>]*>\s*<section id="browse"/);
  const folders = [...home.matchAll(/<article\b[^>]*data-sample-card\b[^>]*data-folder="([^"]+)"/g)]
    .map((match) => match[1]);
  const expected = [...catalog].sort((a, b) =>
    (b.updatedAt ? Date.parse(b.updatedAt) : 0) - (a.updatedAt ? Date.parse(a.updatedAt) : 0) ||
    a.title.localeCompare(b.title),
  ).map((sample) => sample.folder.toLowerCase());
  assert.deepEqual(folders, expected);
});

test("every sample has a generated page with its own tracker, source, and download links", async () => {
  for (const sample of catalog) {
    const html = await htmlFor(path.join("samples", sample.folder));
    assert.equal(trackerCount(html), 1, `${sample.folder}: duplicate tracker`);
    assert.ok(html.includes(`src="${statsBase}samples/${sample.folder}"`));
    assert.ok(html.includes(sample.href), `${sample.folder}: missing source link`);
    assert.ok(html.includes(encodeURIComponent(sample.href)), `${sample.folder}: missing download link`);
    const breadcrumb = html.match(/<div class="breadcrumb container">([\s\S]*?)<\/div>/)?.[1] ?? "";
    assert.ok(breadcrumb.includes(`href="${base}"`), `${sample.folder}: back link should go to the homepage catalog`);
    const readme = html.match(/<article class="readme-content"[^>]*>([\s\S]*?)<\/article>/)?.[1] ?? "";
    assert.doesNotMatch(readme, /<script\b|\sonerror=|\sonload=|(?:href|src)="javascript:/i);
    assert.doesNotMatch(readme, /(?:href|src)="\.{1,2}\//, `${sample.folder}: unresolved README URL`);
  }
});

test("catalog and contributor counts match sample metadata", async () => {
  assert.equal((home.match(/<article\b[^>]*data-sample-card/g) ?? []).length, catalog.length);
  assert.match(home, /id="active-summary" aria-live="polite"/);
  const accounts = new Set(catalog.flatMap((sample) =>
    sample.authors.map((author) => author.gitHubAccount.trim().replace(/^@/, "").toLowerCase()).filter(Boolean),
  ));
  const contributors = await htmlFor("contributors");
  assert.equal((contributors.match(/class="contributor-card"/g) ?? []).length, accounts.size);
});

test("What's new is a chronological text update list rather than a second gallery", async () => {
  const latest = await htmlFor("whats-new");
  assert.match(latest, /class="updates-list"/);
  assert.doesNotMatch(latest, /data-sample-card|class="component-grid"|class="catalog-backdrop"/);
  const entries = [...latest.matchAll(/<article>([\s\S]*?)<\/article>/g)].map((match) => match[1]);
  const expected = catalog.filter((sample) => sample.updatedAt).sort((a, b) =>
    Date.parse(b.updatedAt) - Date.parse(a.updatedAt) || a.title.localeCompare(b.title),
  );
  assert.equal(entries.length, expected.length);
  for (const [index, sample] of expected.entries()) {
    const entry = entries[index];
    assert.ok(entry.includes(`datetime="${sample.updatedAt.slice(0, 10)}"`), `${sample.folder}: wrong update date/order`);
    assert.ok(entry.includes(`href="${base}samples/${sample.folder}/"`), `${sample.folder}: missing sample link`);
    const label = sample.createdAt?.slice(0, 10) === sample.updatedAt.slice(0, 10) ? "Added" : "Updated";
    assert.ok(entry.includes(`class="eyebrow">${label}</p>`), `${sample.folder}: wrong activity label`);
    assert.doesNotMatch(entry, /<img\b/, `${sample.folder}: activity rows should not repeat preview images`);
  }
});

test("sample README trackers match their repository-relative sample paths", async () => {
  for (const sample of catalog) {
    const readme = await readFile(path.join("..", "samples", sample.folder, "README.md"), "utf8");
    const trackers = [...readme.matchAll(/https:\/\/m365-visitor-stats\.azurewebsites\.net\/[^"')\s>]+/g)];
    assert.equal(trackers.length, 1, `${sample.folder}: expected one README tracker`);
    assert.equal(trackers[0][0], `${statsBase}samples/${sample.folder}`);
  }
});

test("local links and brand assets resolve with the deployment base path", async () => {
  async function checkHtml(directory) {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      const file = path.join(directory, entry.name);
      if (entry.isDirectory()) await checkHtml(file);
      else if (entry.name.endsWith(".html")) {
        const html = await readFile(file, "utf8");
        for (const match of html.matchAll(/(?:href|src)="(\/[^"]*)"/g)) {
          if (match[1].startsWith("//")) continue;
          const target = new URL(match[1], "https://pnp.github.io").pathname;
          assert.ok(target.startsWith(base), `${file}: URL escaped deployment base: ${target}`);
          const relative = decodeURIComponent(target.slice(base.length));
          const destination = path.join(dist, relative);
          const info = await stat(destination).catch(() => null);
          assert.ok(info, `${file}: missing local target ${target}`);
          if (info.isDirectory()) await stat(path.join(destination, "index.html"));
        }
      }
    }
  }
  await checkHtml(dist);
  for (const asset of ["copilot.png", "side-bg-left.webp", "side-bg-right.webp", "contributor-badge.webp"]) {
    assert.ok((await stat(path.join(dist, "images", asset))).size > 1000);
  }
});

test("the legacy contribution URL redirects to the new page", async () => {
  const html = await htmlFor("contribute");
  assert.match(html, /http-equiv="refresh"/i);
  assert.ok(html.includes(`${base}contributing/`));
});

test("the legacy samples URL redirects home instead of rendering a duplicate catalog", async () => {
  const html = await htmlFor("samples");
  assert.ok(html.includes(`http-equiv="refresh" content="0;url=${base}"`));
  assert.ok(html.includes(`<link rel="canonical" href="${canonical}"`));
  assert.match(html, /name="robots" content="noindex"/);
  assert.doesNotMatch(html, /data-sample-card|class="page-heading|class="catalog-backdrop"/);
  assert.equal(trackerCount(html), 0);
});

test("the 404 page retains navigation and a distinct tracker", async () => {
  const html = await readFile(path.join(dist, "404.html"), "utf8");
  assert.equal(trackerCount(html), 1);
  assert.ok(html.includes(`href="${base}">Browse samples</a>`));
});
