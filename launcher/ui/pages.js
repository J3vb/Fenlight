// Sidebar pages, title bar, news and the Installation "..." menu (plan step 5).
"use strict";

(() => {
  const { invoke } = window.__TAURI__.core;
  const appWindow = window.__TAURI__.window.getCurrentWindow();
  const SEEN_KEY = "news-seen";
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  const pages = document.querySelectorAll(".page");
  const navButtons = document.querySelectorAll("nav .nav");
  const newsDot = document.getElementById("news-dot");
  const moreMenu = document.getElementById("more-menu");
  const ask = document.getElementById("ask");
  let news = [];
  let pendingAsk = null;

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function niceDate(date) {
    const [year, month, day] = date.split("-").map(Number);
    return year ? `${MONTHS[month - 1]} ${day}, ${year}` : "";
  }

  function newsImage(item) {
    return `url("news/${encodeURIComponent(item.image)}")`;
  }

  function readSeen() {
    try {
      return Number(localStorage.getItem(SEEN_KEY)) || 0;
    } catch (problem) {
      return 0;
    }
  }

  function markSeen() {
    if (!news.length) return;
    try {
      localStorage.setItem(SEEN_KEY, String(news[0].id));
    } catch (problem) {
      // No storage: the dot just shows again next time.
    }
    newsDot.hidden = true;
  }

  function openPage(name) {
    for (const page of pages) page.hidden = page.id !== `page-${name}`;
    for (const button of navButtons) button.classList.toggle("active", button.dataset.page === name);
    if (name === "news") markSeen();
    if (name === "patches") showPatches();
  }

  function showNews() {
    const hero = news[0];
    document.getElementById("hero").style.backgroundImage = newsImage(hero);
    document.getElementById("hero-kicker").textContent = hero.kicker;
    document.getElementById("hero-title").textContent = hero.title;
    document.getElementById("hero-summary").textContent = hero.summary;
    const latest = document.getElementById("latest");
    latest.replaceChildren(...news.slice(0, 3).map(latestItem));
    document.getElementById("news-list").replaceChildren(...news.map(fullItem));
    newsDot.hidden = news[0].id <= readSeen();
  }

  function latestItem(item) {
    const row = element("li");
    const thumb = element("div", "thumb");
    thumb.style.backgroundImage = newsImage(item);
    const text = element("div");
    text.append(element("h4", "", item.title), element("p", "", item.summary), element("time", "", niceDate(item.date)));
    row.append(thumb, text);
    row.addEventListener("click", () => openItem(item.id));
    return row;
  }

  function fullItem(item) {
    const card = element("article", "news-item");
    card.id = `news-${item.id}`;
    const picture = element("div", "picture");
    picture.style.backgroundImage = newsImage(item);
    const text = element("div");
    text.append(
      element("p", "kicker", item.kicker),
      element("h3", "", item.title),
      element("time", "", niceDate(item.date)),
      element("p", "", item.body),
    );
    card.append(picture, text);
    return card;
  }

  function openItem(id) {
    openPage("news");
    document.getElementById(`news-${id}`).scrollIntoView();
  }

  async function showPatches() {
    const list = await invoke("patches");
    document.getElementById("patches-empty").textContent = list.length ? "" : "No patch notes yet. Are you offline?";
    document.getElementById("patches-list").replaceChildren(
      ...list.map((patch) => {
        const card = element("article", "patch");
        card.append(element("h3", "", `v${patch.version}`), element("time", "", niceDate(patch.date)));
        card.append(...notesLines(patch.notes || "No notes for this release."));
        return card;
      }),
    );
  }

  // Release notes are short Markdown: headings and bullets become plain lines.
  function notesLines(notes) {
    return notes
      .split("\n")
      .filter((line) => line.trim())
      .map((line) => {
        const heading = line.match(/^#+\s*(.*)/);
        if (heading) return element("h4", "", heading[1]);
        const bullet = line.match(/^\s*[-*]\s+(.*)/);
        return bullet ? element("p", "bullet", bullet[1]) : element("p", "", line);
      });
  }

  function askFirst(text, yes, action) {
    document.getElementById("ask-text").textContent = text;
    document.getElementById("ask-yes").textContent = yes;
    pendingAsk = action;
    ask.hidden = false;
  }

  async function run(command, done) {
    try {
      await invoke(command);
      statusLine.textContent = done;
      statusLine.className = "ok";
    } catch (problem) {
      statusLine.textContent = String(problem);
      statusLine.className = "error";
    }
    show();
  }

  async function openPlace(place) {
    moreMenu.hidden = true;
    try {
      await invoke("open_place", { place });
    } catch (problem) {
      document.getElementById("support-status").textContent = String(problem);
    }
  }

  for (const button of document.querySelectorAll("[data-page]")) {
    button.addEventListener("click", () => openPage(button.dataset.page));
  }
  for (const button of document.querySelectorAll("[data-place]")) {
    button.addEventListener("click", () => openPlace(button.dataset.place));
  }
  document.getElementById("hero-more").addEventListener("click", () => openItem(news[0].id));
  document.getElementById("win-min").addEventListener("click", () => appWindow.minimize());
  document.getElementById("win-close").addEventListener("click", () => appWindow.close());

  document.getElementById("more").addEventListener("click", (event) => {
    event.stopPropagation();
    moreMenu.hidden = !moreMenu.hidden;
  });
  document.addEventListener("click", () => {
    moreMenu.hidden = true;
  });
  document.getElementById("repair").addEventListener("click", () =>
    askFirst("Check the game files and replace any that are missing or damaged?", "Repair", () =>
      run("repair", "Checking game files…"),
    ),
  );
  document.getElementById("uninstall").addEventListener("click", () =>
    askFirst("Uninstall the game? Your saves and settings stay.", "Uninstall", () => run("uninstall", "Game uninstalled.")),
  );
  document.getElementById("ask-yes").addEventListener("click", () => {
    ask.hidden = true;
    pendingAsk();
  });
  document.getElementById("ask-no").addEventListener("click", () => {
    ask.hidden = true;
  });

  const closeOnPlay = document.getElementById("close-on-play");
  closeOnPlay.addEventListener("change", () => invoke("set_close_on_play", { close: closeOnPlay.checked }));
  document.addEventListener("launcher-state", (event) => {
    closeOnPlay.checked = event.detail.close_on_play;
    document.getElementById("launcher-version").textContent = `Launcher v${event.detail.version}`;
    document.getElementById("repair").disabled = !event.detail.installed.length || event.detail.hosting;
    document.getElementById("uninstall").disabled = !event.detail.installed.length || event.detail.hosting;
  });

  invoke("news").then((items) => {
    news = items;
    if (news.length) showNews();
  });
})();
