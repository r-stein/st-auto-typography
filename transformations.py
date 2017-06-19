from collections import defaultdict
import yaml

import sublime

_transformation_map = defaultdict(lambda: defaultdict(lambda: []))
_inverse_transformation_map = defaultdict(lambda: [])


def load_resource():
    res = sublime.find_resources("auto_typography.yaml")[0]
    res_content = sublime.load_resource(res)
    resource = yaml.load(res_content)
    return resource


def get_transformation_map():
    return _transformation_map


def get_inverse_transformation_map():
    return _inverse_transformation_map


def plugin_loaded():
    loaded_typography = load_resource()["default"]

    typography = defaultdict(lambda: [])
    # flatten the typography
    for d in loaded_typography:
        for k, v in d.items():
            typography[k].append(v)

    # replace the trigger keys
    replace = []
    for k in typography:
        for i in range(1, len(k)):
            prefix_key = k[:i]
            if prefix_key in typography:
                remaining_key = k[i:]
                replacement = typography[prefix_key][0]
                replace.append((k, replacement + remaining_key))
    for old_key, new_key in replace:
        typography[new_key] = typography[old_key]
        del typography[old_key]

    for k, v in typography.items():
        seq = k[::-1]
        _transformation_map[""][seq] = v
        char, prefix = seq[:1], seq[1:]
        _transformation_map[char][prefix] = v

    print(
        "_transformation_map:",
        dict((k, dict(v)) for k, v in _transformation_map.items()))

    for k, v in typography.items():
        for s in v:
            _inverse_transformation_map[s[::-1]].append(k)
    print("_inverse_transformation_map:", _inverse_transformation_map)
