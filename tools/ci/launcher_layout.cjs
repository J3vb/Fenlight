// Launcher layout test: opens launcher/ui in Chromium (the engine behind Windows WebView2) at the
// window size the launcher really gets on common screens and Windows display scales, puts the
// bottom bar in each state, and fails if anything leaves the window or its section.
// Run: node tools/ci/launcher_layout.cjs [screenshot folder]
"use strict";

const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

const PAGE = "file://" + path.resolve(__dirname, "../../launcher/ui/index.html");
const WINDOW = { width: 1440, height: 860 }; // launcher/src-tauri/tauri.conf.json
const TASKBAR = 48; // Windows 11 taskbar height at 100%

// [screen width, screen height, display scale]
const SCREENS = [
  [1920, 1080, 1],
  [1920, 1080, 1.25],
  [1920, 1080, 1.5],
  [1366, 768, 1],
  [1366, 768, 1.25],
  [1600, 900, 1.25],
  [1280, 720, 1],
  [2560, 1440, 1],
  [2560, 1440, 1.5],
  [2560, 1440, 1.75],
  [3840, 2160, 1.5],
  [3840, 2160, 2],
];

const STATES = {
  play: { play: "Play", status: "Up to date", ok: true, used: "919 MB", free: "616.6 GB free" },
  installing: {
    play: "Installing",
    done: 42,
    cancel: true,
    status: "Downloading v0.1.3…",
    used: "42% · 919 MB of 2.2 GB",
    free: "616.6 GB free",
  },
  checking: { play: "Checking", done: 100, cancel: true, status: "Downloading v0.1.3…", used: "100% · 2.2 GB of 2.2 GB", free: "1234.5 GB free" },
  install: { play: "Install", status: "v0.1.12 is ready to install.", used: "Not installed", free: "616.6 GB free" },
  retry: { play: "Retry", status: "Could not update to v0.1.12-test.3. Press Retry.", error: true, used: "919 MB", free: "616.6 GB free" },
  update: { play: "Update", status: "Checking for a launcher update…", used: "919 MB", free: "616.6 GB free" },
};

// Mirrors fit_to_screen() in launcher/src-tauri/src/main.rs: the window shrinks to the work area.
function windowSize(screenW, screenH, scale) {
  const width = Math.min(WINDOW.width * scale, screenW);
  const height = Math.min(WINDOW.height * scale, screenH - TASKBAR * scale);
  return { width: Math.floor(width / scale), height: Math.floor(height / scale) };
}

function stub() {
  window.__TAURI__ = {
    core: { invoke: () => new Promise(() => {}) },
    event: { listen: () => {} },
    window: { getCurrentWindow: () => ({ minimize() {}, close() {} }) },
  };
}

function setState(state) {
  const el = (id) => document.getElementById(id);
  el("play").disabled = false;
  el("play-text").textContent = state.play;
  el("play").style.setProperty("--done", `${state.done || 0}%`);
  el("cancel").hidden = !state.cancel;
  el("status").textContent = state.status;
  el("status").className = state.ok ? "ok" : state.error ? "error" : "";
  el("disk-used").textContent = state.used;
  el("disk-free").textContent = state.free;
  el("progress").value = state.done || 42;
  const channel = el("channel");
  channel.options[0].textContent = "Stable v0.1.12";
  channel.options[1].textContent = "Test v0.1.13-test.4";
  channel.value = "test";
}

// Returns a list of problems: elements outside the window, outside their bar section, or text
// that does not fit its button.
function findProblems() {
  const problems = [];
  const slack = 0.5;
  const name = (e) => e.id ? `#${e.id}` : `${e.tagName.toLowerCase()}.${[...e.classList].join(".")}`;
  const visible = (e) => e.getClientRects().length > 0 && getComputedStyle(e).visibility !== "hidden";
  const inside = (e, box, what) => {
    const r = e.getBoundingClientRect();
    if (r.left < box.left - slack || r.right > box.right + slack || r.top < box.top - slack || r.bottom > box.bottom + slack) {
      problems.push(`${name(e)} [${Math.round(r.left)}..${Math.round(r.right)} x ${Math.round(r.top)}..${Math.round(r.bottom)}] is outside ${what}`);
    }
  };
  const win = { left: 0, top: 0, right: innerWidth, bottom: innerHeight };
  if (document.documentElement.scrollWidth > innerWidth) problems.push("the page scrolls sideways");
  for (const e of document.querySelectorAll(".sidebar, main, .hero, .latest, .strip, .strip > *, .bar")) {
    if (visible(e)) inside(e, win, "the window");
  }
  const bar = document.querySelector(".bar").getBoundingClientRect();
  for (const e of document.querySelectorAll(".bar *")) {
    if (visible(e) && !e.closest(".menu")) inside(e, bar, "the bottom bar");
  }
  for (const section of document.querySelectorAll(".bar > *")) {
    const box = section.getBoundingClientRect();
    for (const e of section.querySelectorAll("*")) {
      if (visible(e) && !e.closest(".menu")) inside(e, box, name(section));
    }
  }
  const play = document.getElementById("play");
  const text = document.getElementById("play-text").getBoundingClientRect();
  const button = play.getBoundingClientRect();
  if (text.left < button.left - slack || text.right > button.right + slack) problems.push("the Play label is wider than the button");
  return problems;
}

async function main() {
  const shots = process.argv[2];
  if (shots) fs.mkdirSync(shots, { recursive: true });
  const browser = await chromium.launch();
  const failures = [];
  let checks = 0;
  for (const [screenW, screenH, scale] of SCREENS) {
    const viewport = windowSize(screenW, screenH, scale);
    const page = await browser.newPage({ viewport, deviceScaleFactor: scale });
    await page.addInitScript(stub);
    await page.goto(PAGE);
    // Segoe UI is not on Linux. DejaVu Sans is wider, so a layout that fits with it fits on Windows.
    await page.addStyleTag({ content: 'body, button, select { font-family: "DejaVu Sans", sans-serif; }' });
    for (const [stateName, state] of Object.entries(STATES)) {
      await page.evaluate(setState, state);
      const problems = await page.evaluate(findProblems);
      const label = `${screenW}x${screenH} at ${scale * 100}% (window ${viewport.width}x${viewport.height}), ${stateName}`;
      checks += 1;
      for (const problem of problems) failures.push(`${label}: ${problem}`);
      if (shots && (stateName === "installing" || problems.length)) {
        await page.screenshot({ path: path.join(shots, `${screenW}x${screenH}_${scale * 100}_${stateName}.png`) });
      }
    }
    await page.close();
  }
  await browser.close();
  for (const failure of failures) console.log(`FAIL ${failure}`);
  console.log(`${checks} layouts checked, ${failures.length} problems`);
  process.exit(failures.length ? 1 : 0);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
