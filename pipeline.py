from detector import detect_obfuscator
from string_resolver import decode_lua_decimal_escapes, resolve_string_tables
from ast_rebuilder import rebuild_ast

from Moonsec_V3_Deobfuscator.script_processor import process_script as moonsec_deob
from Moonsec_V3_Decompiler.decompiler import decompile as moonsec_decompile
from IronBrew_Deobfuscator.script_processor import process_script as ironbrew_deob
from WeAreDevs_deobfuscator.script_processor import process_script as wearedevs_deob


def run_pipeline(code):

    code = decode_lua_decimal_escapes(code)
    code = resolve_string_tables(code)

    layers = []

    for _ in range(5):  # máximo 5 capas

        obf = detect_obfuscator(code)

        layers.append(obf)

        if obf == "moonsec":

            stage1 = moonsec_deob(code)
            code = moonsec_decompile(stage1)

        elif obf == "ironbrew":

            code = ironbrew_deob(code)

        elif obf == "wearedevs":

            code = wearedevs_deob(code)

        else:
            break

    code = rebuild_ast(code)

    return code, layers
