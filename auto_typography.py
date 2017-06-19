import collections
import operator as opi
import re

import sublime
import sublime_plugin

opi_map = {
    sublime.OP_EQUAL: opi.eq,
    sublime.OP_NOT_EQUAL: opi.ne,
    sublime.OP_REGEX_CONTAINS: re.search,
    sublime.OP_NOT_REGEX_CONTAINS: lambda p, s: re.search(p, s),
    sublime.OP_REGEX_MATCH: re.match,
    sublime.OP_NOT_REGEX_MATCH: lambda p, s: re.match(p, s),
}


typography = {
    "...": "…",
    "--": "–",  # ndash
    "–-": "—",  # mdash
    "->": "→",
    "→>": "↠",
    "–>": "⟶",
}


transformation_char_map = collections.defaultdict(lambda: {})
for k, v in typography.items():
    char = k[-1:]
    prefix = k[:-1]
    transformation_char_map[char][prefix[::-1]] = v
    transformation_char_map[""][k[::-1]] = v

unpack_char_map = {v[::-1]: k for k, v in typography.items()}


def replace_prefix(view, edit, iterator, insert_else=""):
    # ensure we can iterate several times if necessary
    if len(view.sel()) > 1:
        iterator = list(iterator)
    for sel in view.sel():
        pos = sel.b
        line_before_reg = sublime.Region(view.line(pos).a, pos)
        line_before = view.substr(line_before_reg)[::-1]
        for prefix, value in iterator:
            if line_before.startswith(prefix):
                prefix_reg = sublime.Region(pos - len(prefix), pos)
                view.replace(edit, prefix_reg, value)
                break
        else:
            if insert_else:
                view.insert(edit, pos, insert_else)


class AutoTypographyCommand(sublime_plugin.TextCommand):
    def run(self, edit, character=""):
        iterator = transformation_char_map[character].items()
        replace_prefix(self.view, edit, iterator, character)


class AutoTypographyUnpackCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        replace_prefix(self.view, edit, unpack_char_map.items())


class AutoTypographyContextListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if not key.startswith("auto_typography."):
            return
        key_array = key.split(".")[1:]
        try:
            context_func = getattr(self, "_ctx_" + key_array[0])
        except KeyError:
            print("No context function for '{}'".format(key))
            return

        key_array = key_array[1:]
        op = opi_map[operator]
        quantor = all if match_all else any
        result = quantor(
            op(operand, context_func(view, sel, key_array))
            for sel in view.sel()
        )
        return result

    def _ctx_valid_scope(self, view, sel, *args):
        settings = sublime.load_settings("AutoTypography.sublime-settings")
        scope = settings.get("enable_scope", "text")
        return bool(view.score_selector(sel.b, scope))

    def _ctx_unpack_backwards(self, view, sel, *args):
        char_before = self.__get_string_before(view, sel.b, "char")
        result = any(char_before == uc_char for uc_char in unpack_char_map)
        return result

    def _ctx_is_prefixed(self, view, sel, keys, *args):
        character = keys[0][-1:]
        line_before = self.__get_string_before(view, sel.b, "line")
        result = any(
            line_before.startswith(prefix)
            for prefix in transformation_char_map[character]
        )
        return result

    def __get_string_before(self, view, pos, by="line"):
        if by == "line":
            before_reg = sublime.Region(view.line(pos).a, pos)
        elif by == "char":
            before_reg = sublime.Region(pos - 1, pos)
        else:
            raise Exception("Unknown type {}".format(by))
        return view.substr(before_reg)[::-1]
