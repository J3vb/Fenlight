// The bottom bar: asks the Rust side for the state. The first install waits for the player
// to pick a folder and press Install; later updates install on their own. Play starts the
// newest installed game (docs/plans/separate-launcher.md, steps 1 and 5).
"use strict";

const { invoke } = window.__TAURI__.core;
const { listen } = window.__TAURI__.event;

const playButton = document.getElementById("play");
const playText = document.getElementById("play-text");
const cancelButton = document.getElementById("cancel");
const channelSelects = document.querySelectorAll("select.channel");
const statusLine = document.getElementById("status");
const progressBar = document.getElementById("progress");
const diskUsed = document.getElementById("disk-used");
const diskFree = document.getElementById("disk-free");

let online = true;
// An update installs on its own once per version and run; after a failure Play turns into Retry.
let tried = "";
// True while the launcher checks for its own update: Play works, but a game update waits so
// a launcher restart does not cut it off.
let checkingLauncher = false;
// What the big button does: "play", "install" (opens the Install dialog) or "retry".
let action = "play";

const installAsk = document.getElementById("install-ask");
const installPath = document.getElementById("install-path");
const installNeed = document.getElementById("install-need");
const installFree = document.getElementById("install-free");
const installProblem = document.getElementById("install-problem");
const installGo = document.getElementById("install-go");

function showStatus(text, kind) {
  statusLine.textContent = text;
  statusLine.title = text;
  statusLine.className = kind || "";
}

function gigabytes(bytes) {
  return bytes >= 1e9 ? `${(bytes / 1e9).toFixed(1)} GB` : `${Math.round(bytes / 1e6)} MB`;
}

async function showDisk(busy) {
  const disk = await invoke("disk");
  diskUsed.textContent = disk.installed ? gigabytes(disk.installed) : "Not installed";
  diskFree.textContent = `${gigabytes(disk.free)} free`;
  if (!busy) {
    const total = disk.installed + disk.free;
    progressBar.value = total > 0 ? Math.max(1, Math.round((disk.installed * 100) / total)) : 0;
  }
}

function showChannels(state) {
  for (const select of channelSelects) {
    select.value = state.channel;
    select.options[0].textContent = state.stable ? `Stable v${state.stable}` : "Stable";
    select.options[1].textContent = state.test ? `Test v${state.test}` : "Test builds";
  }
}

function showPlace(place) {
  installPath.textContent = place.dir;
  installPath.title = place.dir;
  installNeed.textContent = place.need ? `Needs about ${gigabytes(place.need)}` : "";
  installFree.textContent = `${gigabytes(place.free)} free on this drive`;
  const tooSmall = place.need > place.free;
  installProblem.textContent = tooSmall ? "Not enough free space here. Pick another drive." : "";
  installGo.disabled = tooSmall;
}

async function askInstall() {
  showPlace(await invoke("install_place"));
  installAsk.hidden = false;
}

async function startInstall(newest) {
  tried = newest.version;
  showStatus(`Downloading v${newest.version}…`);
  progressBar.value = 0;
  try {
    await invoke("install");
    return true;
  } catch (problem) {
    showStatus(String(problem), "error");
    return false;
  }
}

async function show() {
  const state = await invoke("status");
  showChannels(state);
  document.dispatchEvent(new CustomEvent("launcher-state", { detail: state }));
  showDisk(state.busy);
  const newest = state.newest;
  const installed = state.installed[0];
  cancelButton.hidden = !state.busy;
  action = installed ? "play" : "install";
  if (state.auto_update && tried === newest.version && !state.busy) action = "retry";
  playButton.disabled = state.busy || (!installed && !state.update_ready);
  playText.textContent = state.busy ? "Installing" : { play: "Play", install: "Install", retry: "Retry" }[action];
  if (state.busy) return;
  if (checkingLauncher) return;
  if (state.auto_update && action !== "retry") {
    playText.textContent = "Update";
    playButton.disabled = true;
    // A refused start (another download running) shows Retry instead of a stuck button.
    if (!(await startInstall(newest))) await show();
    return;
  }
  if (action === "retry") {
    showStatus(`Could not update to v${newest.version}. Press Retry.`, "error");
  } else if (installed) {
    showStatus(online ? "Up to date" : `Offline: playing v${installed}`, online ? "ok" : "");
  } else if (state.update_ready) {
    showStatus(`v${newest.version} is ready to install.`);
  } else {
    showStatus(online ? "Nothing to install yet." : "Connect to the internet to install the game.", online ? "" : "error");
  }
}

async function refresh() {
  try {
    await invoke("refresh");
    online = true;
  } catch (problem) {
    online = false;
  }
  if (online) {
    checkingLauncher = true;
    await show();
    showStatus("Checking for a launcher update…");
    try {
      await invoke("self_update");
    } catch (problem) {
      // A failed launcher update keeps this launcher; the game still installs and plays.
    }
    checkingLauncher = false;
  }
  await show();
}

// Started a second time (the game's "Restart to update"): look for updates again.
listen("started_again", () => {
  if (!checkingLauncher) refresh();
});

listen("progress", (event) => {
  const { done, total } = event.payload;
  progressBar.value = total > 0 ? Math.floor((done * 100) / total) : 0;
  playText.textContent = progressBar.value >= 100 ? "Checking" : `Installing ${progressBar.value}%`;
});

listen("finished", (event) => {
  const { ok, message } = event.payload;
  if (ok) tried = "";
  show().then(() => showStatus(message, ok ? "ok" : "error"));
});

playButton.addEventListener("click", async () => {
  try {
    if (action === "install") return askInstall();
    if (action === "retry") {
      tried = "";
      return show();
    }
    await invoke("play");
  } catch (problem) {
    showStatus(String(problem), "error");
  }
});

document.getElementById("install-browse").addEventListener("click", async () => {
  try {
    showPlace(await invoke("browse_install"));
  } catch (problem) {
    installProblem.textContent = String(problem);
  }
});

installGo.addEventListener("click", async () => {
  installAsk.hidden = true;
  const state = await invoke("status");
  if (state.newest) await startInstall(state.newest);
  show();
});

document.getElementById("install-no").addEventListener("click", () => {
  installAsk.hidden = true;
});

cancelButton.addEventListener("click", () => invoke("cancel"));

for (const select of channelSelects) {
  select.addEventListener("change", async () => {
    await invoke("set_channel", { channel: select.value });
    tried = "";
    await show();
  });
}

// After pages.js and host.js have added their listeners.
window.addEventListener("DOMContentLoaded", refresh);
