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


class AbstractAutoTypographyContext(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        try:
            prefix = self.key_prefix + "."
        except AttributeError:
            return
        if not key.startswith(prefix):
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
