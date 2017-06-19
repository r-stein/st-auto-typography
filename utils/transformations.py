from collections import defaultdict
import yaml

import sublime


def load_resource():
    res = sublime.find_resources("auto_typography.yaml")[0]
    res_content = sublime.load_resource(res)
    resource = yaml.load(res_content)
    return resource


def _get_transformation_map():
    if hasattr(_get_transformation_map, "result"):
        return _get_transformation_map.result

    transformation_map = defaultdict(lambda: defaultdict(lambda: []))
    inverse_transformation_map = defaultdict(lambda: [])

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
        transformation_map[""][seq] = v
        char, prefix = seq[:1], seq[1:]
        transformation_map[char][prefix] = v

    for k, v in typography.items():
        for s in v:
            inverse_transformation_map[s[::-1]].append(k)

    _get_transformation_map.result = (
        transformation_map, inverse_transformation_map)

    return _get_transformation_map.result


def get_transformation_map():
    return _get_transformation_map()[0]


def get_inverse_transformation_map():
    return _get_transformation_map()[1]
