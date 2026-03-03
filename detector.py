import re

def detect_obfuscator(code):

    c = code.lower()

    if "moonsec" in c or "msv3" in c:
        return "moonsec"

    if "ironbrew" in c or "ib2" in c:
        return "ironbrew"

    if "prometheus" in c or "wearedevs" in c:
        return "wearedevs"

    if "phase_boundary" in c:
        return "wearedevs"

    if "string.char" in code and "loadstring" in code:
        return "char_loader"

    return "unknown"
