# Launcher UI (plain JS)

1. **Buttons that start work** are disabled before the `invoke`, not after
   the `await`, and enabled again in `finally`. A double click or a held
   Enter cannot call the command twice.
2. **Every `invoke` handles failure.** The player sees the backend's message,
   not a generic one. No unhandled promise rejection.
3. **State comes from the backend.** After every action and event the UI
   re-reads `status`; it does not guess. After a channel change the Play
   button, version text and patch list all update.
4. **Overlapping async work.** An older reply cannot overwrite a newer one.
   A poll does not overlap itself. Listeners are added once; intervals are cleared.
5. **Events.** `progress` and `finished` payloads match what Rust sends.
   A `finished` with an error, and a cancel, both reset the busy UI.
6. **Outside text is text.** News, patch notes, release names, paths and
   error strings go in with `textContent`, never `innerHTML`. Links open
   only http(s) addresses.
7. **Inputs.** `Number("")` is 0 and bad text is `NaN`: port and player
   count are checked for range before the call. Argument names match Rust.
8. **Every state has the right buttons.** First run, no install, offline,
   installing, update ready, hosting: Play, Install, Repair, Uninstall and
   the channel picker are enabled only when the action is safe.
9. **Close and quit.** Closing during a download or with a server running
   asks first, and Quit really stops the server.
10. **Light work per event.** No heavy DOM work on every progress event, no
    blocking loop.
11. **Plain pieces.** No framework, bundler or new dependency. Every id used
    exists in `index.html`. No state shared between `app.js`, `host.js` and
    `pages.js` by accident.
12. **Fixed window.** Long paths and long messages wrap or cut cleanly;
    keyboard focus still works.
