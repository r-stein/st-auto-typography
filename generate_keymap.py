import os
import textwrap

import sublime
import sublime_plugin

from .utils.transformations import get_transformation_map


format_str = textwrap.indent("""{
    "keys": ["<<character>>"], "command": "auto_typography",
    "args": {"character": "<<character>>"},
    "context": [
        { "key": "auto_typography.is_enabled"},
        { "key": "auto_typography.valid_scope"},
        { "key": "auto_typography.is_prefixed.value=<<character>>"},
    ],
},""", " " * 4)


class AutoTypographyGenerateKeymapCommand(sublime_plugin.WindowCommand):
    def run(self):
        entries = []
        for character in sorted(get_transformation_map()):
            if not character:
                continue
            entries.append(format_str.replace("<<character>>", character))

        content = "[\n{}\n]".format("\n".join(entries))

        target_path = os.path.normpath(
            "{}/AutoTypography/auto_generated"
            .format(sublime.packages_path())
        )
        os.makedirs(target_path, exist_ok=True)
        target_path = os.path.join(target_path, "Default.sublime-keymap")
        with open(target_path, "w") as f:
            f.write(content)

        self.window.open_file(target_path)
