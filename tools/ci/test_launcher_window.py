"""Launcher window rules: a fixed-size window, a bottom bar that never grows out of it, and
an Install dialog instead of installing on start; stdlib only. The real layout check at each
Windows display scale is tools/ci/launcher_layout.cjs."""

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

    def test_bottom_bar_parts_cannot_push_the_bar_out_of_the_window(self):
        self.assertIn("minmax(0, 1fr)", css_rule(self.css, "body"))
        status = css_rule(self.css, "#status")
        self.assertIn("overflow: hidden", status)
        self.assertIn("-webkit-line-clamp: 2", status)
        self.assertNotIn("nowrap", status)
        play = css_rule(self.css, "#play")
        self.assertRegex(play, r"(?<![-\w])width:\s*\d+px")
        self.assertIn("flex: none", play)
        self.assertIn("overflow: hidden", play)
        self.assertIn("min-width: 0", css_rule(self.css, ".install"))
        self.assertIn("min-width: 0", css_rule(self.css, ".meter"))

    def test_play_label_has_no_changing_percentage(self):
        app = (LAUNCHER / "ui" / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("`Installing ${", app)
        self.assertIn('setProperty("--done"', app)

    def test_layout_check_runs_in_ci(self):
        workflow = (LAUNCHER.parent / ".github" / "workflows" / "launcher.yml").read_text(encoding="utf-8")
        self.assertIn("node tools/ci/launcher_layout.cjs", workflow)

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
