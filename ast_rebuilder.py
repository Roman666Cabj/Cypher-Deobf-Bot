import re

def rebuild_ast(code):

    lines = code.split("\n")
    result = []

    indent = 0

    for line in lines:

        l = line.strip()

        if not l:
            continue

        if re.match(r'^(end|else|elseif|until)', l):
            indent = max(indent-1,0)

        result.append("    "*indent + l)

        if re.match(r'^(if|for|while|function|repeat)', l) or l.endswith("then") or l.endswith("do"):
            indent += 1

    return "\n".join(result)
