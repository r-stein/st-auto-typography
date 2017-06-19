import sublime
import sublime_plugin

from .utils.contexts import AbstractAutoTypographyContext
from .utils.transformations import load_resource


def get_quote_resource():
    if hasattr(get_quote_resource, "result"):
        return get_quote_resource.result
    get_quote_resource.result = load_resource()["quotes"]
    return get_quote_resource.result


def extract_quotes(view, return_quote_type=False):
    quote_type = view.settings().get("auto_typograhy.quote_type")
    if quote_type:
        return quote_type
    settings = sublime.load_settings("AutoTypography.sublime-settings")
    quote_type = settings.get("quote_type", "english")
    quotes = get_quote_resource()[quote_type]
    if return_quote_type:
        return quotes, quote_type
    else:
        return quotes


def set_quotes(view, quote_type):
    view.settings().set("auto_typograhy.quote_type", quote_type)


def has_word_separators(view, quote_type):
    return view.settings().get("auto_typograhy.word_separators") == quote_type


def update_word_separators(view, quote_type):
    quotes = get_quote_resource()[quote_type]
    word_separators = view.settings().get("word_separators")
    found = False
    for quote in quotes:
        if quote not in word_separators:
            found = True
            word_separators += quote
    if found:
        view.settings().set("word_separators", word_separators)
    view.settings().set("auto_typograhy.word_separators", quote_type)


class AutoTypographyQuotesCommand(sublime_plugin.TextCommand):
    @staticmethod
    def is_quote_open(qopen, qclose, content, is_closed=False):
        if is_closed:
            qopen, qclose = qclose, qopen
        return content.count(qopen) > content.count(qclose)

    def run(self, edit, quote_type="", single_quotes=False):
        view = self.view

        quotes, quote_type = extract_quotes(view, return_quote_type=True)

        if not has_word_separators(view, quote_type):
            update_word_separators(view, quote_type)

        qopen, qclose = quotes[:2] if not single_quotes else quotes[2:]

        # context detection
        for sel in view.sel():
            sb, se = sel.begin(), sel.end()
            if not sel.empty():
                view.insert(edit, se, qclose)
                view.insert(edit, sb, qopen)
                return

            line_before = view.substr(
                sublime.Region(view.line(sb).a, sb))[::-1]
            line_after = view.substr(sublime.Region(se, view.line(se).b))
            is_quote_open = self.is_quote_open(qopen, qclose, line_before)
            is_quote_closed = self.is_quote_open(
                qopen, qclose, line_after, is_closed=True)
            is_word_before = line_before[:1].isalpha()
            is_word_after = line_after[:1].isalpha()
            is_quote_closed_after = line_after.startswith(qclose)
            auto_match = view.settings().get("auto_match_enabled", True)

            pos = sel.b
            # step over closing quotes
            if is_quote_closed_after:
                view.sel().subtract(sel)
                view.sel().add(sublime.Region(pos + len(qclose)))
            # close open quotes
            elif is_quote_open and not is_quote_closed:
                view.insert(edit, pos, qclose)
            # if we are at the start of a word -> open a quote
            elif is_word_before:
                view.insert(edit, pos, qclose)
            # if we are at the end of a word -> close a quote
            elif is_word_after:
                view.insert(edit, pos, qopen)
            # if auto_match is enabled -> insert a open and closing quote
            elif auto_match:
                view.sel().subtract(sel)
                view.insert(edit, pos, qopen + qclose)
                view.sel().add(sublime.Region(pos + len(qopen)))
            # otherwise open a quote
            else:
                view.insert(edit, pos, qopen)


class AutoTypographyQuotesContext(AbstractAutoTypographyContext):
    key_prefix = "auto_typography_quotes"

    def _ctx_inside_quotes(self, view, sel, keys, *args):
        print("keys:", keys)
        if not sel.empty():
            return False
        pos = sel.b
        s = view.substr(sublime.Region(pos - 1, pos + 1))
        quotes = "".join(extract_quotes(view))
        return s == quotes[:2] or s == quotes[2:]

    def _ctx_valid_scope(self, view, sel, *args):
        settings = sublime.load_settings("AutoTypography.sublime-settings")
        scope = settings.get("quote_scope", "text")
        return bool(view.score_selector(sel.b, scope))
