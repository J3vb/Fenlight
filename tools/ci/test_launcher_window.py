"""Launcher window rules: a fixed-size window, a bottom bar that never grows out of it, and
an Install dialog instead of installing on start; stdlib only."""

import json
import re
import unittest
from pathlib import Path

LAUNCHER = Path(__file__).resolve().parents[2] / "launcher"


def css_rule(css: str, selector: str) -> str:
    match = re.search(r"(?m)^" + re.escape(selector) + r"\s*\{([^}]*)\}", css)
    if not match:
        raise AssertionError(f"no CSS rule for {selector}")
    return match.group(1)


class WindowTests(unittest.TestCase):
    def setUp(self):
        conf = json.loads((LAUNCHER / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
        self.window = conf["app"]["windows"][0]
        self.html = (LAUNCHER / "ui" / "index.html").read_text(encoding="utf-8")
        self.css = (LAUNCHER / "ui" / "style.css").read_text(encoding="utf-8")
        self.capability = (LAUNCHER / "src-tauri" / "capabilities" / "default.json").read_text(encoding="utf-8")

    def test_window_has_one_fixed_size(self):
        self.assertIs(self.window["resizable"], False)
        self.assertIs(self.window["maximizable"], False)
        self.assertNotIn("minWidth", self.window)
        self.assertNotIn('id="win-max"', self.html)
        self.assertNotIn("maximize", self.capability)

    def test_status_line_cannot_push_the_bar_out_of_the_window(self):
        status = css_rule(self.css, "#status")
        self.assertRegex(status, r"(?<![-\w])width:\s*\d+px")
        self.assertIn("overflow: hidden", status)
        self.assertNotIn("nowrap", status)
        self.assertIn("min-width: 0", css_rule(self.css, ".install"))

    def test_install_dialog_has_location_browse_and_install(self):
        for element in ("install-ask", "install-path", "install-browse", "install-free", "install-go"):
            self.assertIn(f'id="{element}"', self.html)

    def test_window_only_installs_after_the_install_button(self):
        app = (LAUNCHER / "ui" / "app.js").read_text(encoding="utf-8")
        start = app.index("async function show()")
        show = app[start : app.index("\n}\n", start)]
        self.assertEqual(show.count("startInstall("), 1, "show() starts a download only for updates")
        self.assertGreater(show.index("startInstall("), show.index("if (state.auto_update && action"))
        self.assertIn("installGo.addEventListener", app)


if __name__ == "__main__":
    unittest.main()
