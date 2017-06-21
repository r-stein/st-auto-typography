import sublime


def get_setting(key, default=None, view=None):
    if view is not None:
        value = view.settings().get("auto_typography." + key)
        if value is not None:
            return value
    settings = sublime.load_settings("AutoTypography.sublime-settings")
    return settings.get(key, default)
