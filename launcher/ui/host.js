// The Host a server panel: runs the newest installed game as a dedicated server, shows
// whether it runs, and asks before closing the launcher while it does (plan step 4).
"use strict";

(() => {
  const { invoke } = window.__TAURI__.core;
  const { listen } = window.__TAURI__.event;

  const portInput = document.getElementById("host-port");
  const playersSelect = document.getElementById("host-players");
  const toggle = document.getElementById("host-toggle");
  const logsButton = document.getElementById("host-logs");
  const statusLine = document.getElementById("host-status");
  const hint = document.getElementById("host-hint");
  const closeAsk = document.getElementById("close-ask");

  let running = null;
  let stopping = false;
  let loaded = false;

  function showStatus(text, isError) {
    statusLine.textContent = text;
    statusLine.classList.toggle("error", Boolean(isError));
  }

  async function show() {
    let state;
    try {
      state = await invoke("host_status");
    } catch (problem) {
      return showStatus(String(problem), true);
    }
    if (!loaded) {
      portInput.value = state.port;
      playersSelect.value = String(state.max_players);
      loaded = true;
    }
    const wasRunning = running;
    running = state.running;
    if (!running) stopping = false;
    portInput.disabled = playersSelect.disabled = Boolean(running);
    toggle.textContent = running ? "Stop server" : "Start server";
    toggle.disabled = !running && !state.installed;
    if (stopping) {
      showStatus("Stopping the server…");
    } else if (running) {
      showStatus(`Server v${running} is running on port ${portInput.value}. Join it from Servers in the game.`);
    } else if (wasRunning) {
      showStatus("The server stopped.");
    } else if (!state.installed) {
      showStatus("Install the game to host a server.");
    }
    hint.textContent =
      `Friends on other networks need UDP port ${portInput.value} forwarded on your router to this PC. ` +
      "Windows may ask to let the server through the firewall the first time.";
  }

  toggle.addEventListener("click", async () => {
    try {
      if (running) {
        await invoke("host_stop");
        stopping = true;
      } else {
        await invoke("host_start", { port: Number(portInput.value), maxPlayers: Number(playersSelect.value) });
      }
    } catch (problem) {
      showStatus(String(problem), true);
    }
    show();
  });

  logsButton.addEventListener("click", () => invoke("open_logs").catch((problem) => showStatus(String(problem), true)));
  portInput.addEventListener("input", show);

  listen("close_requested", () => {
    closeAsk.hidden = false;
  });
  document.getElementById("close-keep").addEventListener("click", () => {
    closeAsk.hidden = true;
  });
  document.getElementById("close-stop").addEventListener("click", () => {
    stopping = true;
    showStatus("Stopping the server…");
    invoke("quit");
  });

  show();
  setInterval(show, 1000);
})();
