import re

def decode_lua_decimal_escapes(text):

    def repl(m):
        n = int(m.group(1))
        if 0 <= n <= 255:
            return chr(n)
        return m.group(0)

    return re.sub(r'\\(\d{1,3})', repl, text)


def resolve_string_tables(code):

    table_match = re.search(r'local\s+(\w+)\s*=\s*{([^}]+)}', code)

    if not table_match:
        return code

    table_name = table_match.group(1)
    body = table_match.group(2)

    strings = re.findall(r'"([^"]*)"', body)

    for i,s in enumerate(strings,1):
        code = code.replace(f"{table_name}[{i}]", f'"{s}"')

    return code
