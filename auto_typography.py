import sublime
import sublime_plugin

from .utils.contexts import AbstractAutoTypographyContext
from .utils.settings import get_setting
from .utils.transformations import (
    get_transformation_map, get_inverse_transformation_map
)


def replace_prefix(view, edit, iterator, insert_else=""):
    # ensure we can iterate several times if necessary
    if len(view.sel()) > 1:
        iterator = list(iterator)
    for sel in view.sel():
        pos = sel.b
        line_before_reg = sublime.Region(view.line(pos).a, pos)
        line_before = view.substr(line_before_reg)[::-1]
        for prefix, value in iterator:
            if len(value) == 0:
                continue
            elif line_before.startswith(prefix):
                prefix_reg = sublime.Region(pos - len(prefix), pos)
                value = value[0]
                view.replace(edit, prefix_reg, value)
                break
        else:
            if insert_else:
                view.insert(edit, pos, insert_else)


class AutoTypographyCommand(sublime_plugin.TextCommand):
    def run(self, edit, character=""):
        iterator = get_transformation_map()[character].items()
        replace_prefix(self.view, edit, iterator, character)


class AutoTypographyUnpackCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        iterator = get_inverse_transformation_map().items()
        replace_prefix(self.view, edit, iterator)


class AutoTypographyEnableCommand(sublime_plugin.WindowCommand):
    def is_visible(self, *args):
        view = self.window.active_view()
        scope = get_setting("enable_scope", "text")
        if not any(view.score_selector(sel.b, scope) for sel in view.sel()):
            return False
        return not get_setting("enable", view=view)

    def run(self):
        view = self.window.active_view()
        view.settings().set("auto_typography.enable", True)
        sublime.status_message("AutoTypography enabled.")


class AutoTypographyDisableCommand(sublime_plugin.WindowCommand):
    def is_visible(self, *args):
        view = self.window.active_view()
        scope = get_setting("enable_scope", "text")
        if not any(view.score_selector(sel.b, scope) for sel in view.sel()):
            return False
        return bool(get_setting("enable", view=view))

    def run(self):
        view = self.window.active_view()
        view.settings().set("auto_typography.enable", False)
        sublime.status_message("AutoTypography disabled.")


class AutoTypographyContextListener(AbstractAutoTypographyContext):
    key_prefix = "auto_typography"

    def _ctx_is_enabled(self, view, *args):
        return bool(get_setting("enable", True, view=view))

    def _ctx_valid_scope(self, view, sel, *args):
        scope = get_setting("enable_scope", "text")
        return bool(view.score_selector(sel.b, scope))

    def _ctx_unpack_backwards(self, view, sel, *args):
        char_before = self.__get_string_before(view, sel.b, "char")
        result = any(
            char_before == uc_char
            for uc_char in get_inverse_transformation_map()
        )
        return result

    def _ctx_is_prefixed(self, view, sel, keys, *args):
        character = ".".join(keys)[-1:]
        line_before = self.__get_string_before(view, sel.b, "line")
        result = any(
            line_before.startswith(prefix)
            for prefix in get_transformation_map()[character]
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
