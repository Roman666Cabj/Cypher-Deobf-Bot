import re

def detect_vm(code):

    if "return(function(...)" in code:
        return True

    if "local vm =" in code and "pcall(function" in code:
        return True

    return False


def break_vm(code):

    # quitar wrapper VM común
    code = re.sub(r'return\(function\(\.\.\.\)(.*?)end\)\(\)', r'\1', code, flags=re.S)

    return code
