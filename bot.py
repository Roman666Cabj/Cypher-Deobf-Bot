# ============================================
# Cypher Deob Bot PRO+
# Prefix $
# ============================================

import discord
from discord.ext import commands
import aiohttp
import re
import os
import io
import base64
import binascii
from dotenv import load_dotenv

# ============================================
# CONFIG
# ============================================

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("ERROR: DISCORD_TOKEN no encontrado")
    raise SystemExit(1)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="$",
    intents=intents,
    help_command=None
)

MAX_PREVIEW = 3900

COLOR_MAIN = 0xA855F7
COLOR_ALT = 0x7C3AED
COLOR_ERR = 0xEF4444

# ============================================
# READY
# ============================================

@bot.event
async def on_ready():
    print(f"Cypher Deob Bot activo como {bot.user}")
    print("Prefijo: $")
    print("-" * 40)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    embed = discord.Embed(
        title="❌ Error",
        description=f"```{error}```",
        color=COLOR_ERR
    )
    await ctx.send(embed=embed)

# ============================================
# FETCH CODE
# ============================================

async def get_code(ctx, arg=None):
    if ctx.message.attachments:
        file = ctx.message.attachments[0]
        async with aiohttp.ClientSession() as session:
            async with session.get(file.url) as r:
                return await r.text()

    if arg:
        if arg.startswith("http://") or arg.startswith("https://"):
            async with aiohttp.ClientSession() as session:
                async with session.get(arg) as r:
                    return await r.text()
        return arg

    return None

# ============================================
# RESULT SENDER
# ============================================

async def send_result(ctx, title, code, filename="deob.lua"):
    code = str(code)

    if len(code) > MAX_PREVIEW:
        file = discord.File(
            io.BytesIO(code.encode("utf-8")),
            filename=filename
        )
        embed = discord.Embed(
            title=title,
            description="📁 Resultado demasiado largo. Enviado como archivo.",
            color=COLOR_MAIN
        )
        await ctx.send(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title=title,
            description=f"```lua\n{code}\n```",
            color=COLOR_MAIN
        )
        await ctx.send(embed=embed)

# ============================================
# BEAUTIFY
# ============================================

def beautify(code: str) -> str:
    lines = code.split("\n")
    indent = 0
    result = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            result.append("")
            continue

        if stripped.startswith(("end", "elseif", "else", "until")):
            indent -= 1

        result.append("    " * max(indent, 0) + stripped)

        if re.search(r"\bthen\b|\bdo\b|\bfunction\b", stripped):
            indent += 1

    return "\n".join(result)

# ============================================
# DECODERS
# ============================================

def decode_string_char(code: str) -> str:
    return re.sub(
        r'string\.char\((.*?)\)',
        lambda m: '"' + ''.join(
            chr(int(x))
            for x in re.findall(r'\d+', m.group(1))
            if 0 <= int(x) <= 255
        ) + '"',
        code
    )

def decode_decimal(code: str) -> str:
    def repl(m):
        n = int(m.group(1))
        if 0 <= n <= 255:
            return chr(n)
        return m.group(0)

    return re.sub(r'\\(\d{1,3})', repl, code)

def decode_hex_numbers(code: str) -> str:
    return re.sub(
        r'0x([0-9A-Fa-f]+)',
        lambda m: str(int(m.group(1), 16)),
        code
    )

def decode_reverse(code: str) -> str:
    def repl(match):
        s = match.group(1)
        return '"' + s[::-1] + '"'

    return re.sub(
        r'string\.reverse\(\s*["\']([^"\']+)["\']\s*\)',
        repl,
        code
    )

def decode_concat(code: str) -> str:
    pattern = r'table\.concat\s*\(\s*\{([^}]+)\}\s*\)'

    def repl(match):
        content = match.group(1)
        strings = re.findall(r'"([^"]*)"|\'([^\']*)\'', content)
        result = ""

        for s1, s2 in strings:
            result += s1 if s1 else s2

        return f'"{result}"'

    return re.sub(pattern, repl, code)

# ============================================
# BASE64
# ============================================

def _is_printable_text(text: str) -> bool:
    if not text:
        return False
    printable = sum(1 for c in text if c == "\n" or c == "\r" or c == "\t" or 32 <= ord(c) <= 126)
    return printable / max(len(text), 1) > 0.85

def decode_base64_literals(code: str) -> str:
    pattern = r'["\']([A-Za-z0-9+/]{16,}={0,2})["\']'

    def repl(match):
        s = match.group(1)
        try:
            decoded = base64.b64decode(s, validate=True).decode("utf-8", errors="ignore")
            if _is_printable_text(decoded):
                return f'"{decoded}"'
        except Exception:
            pass
        return match.group(0)

    return re.sub(pattern, repl, code)

# ============================================
# XOR DECODERS
# ============================================

def decode_xor_numbers(code: str) -> str:
    # bit32.bxor(97, 1) -> 96
    code = re.sub(
        r'bit32\.bxor\(\s*(\d+)\s*,\s*(\d+)\s*\)',
        lambda m: str(int(m.group(1)) ^ int(m.group(2))),
        code
    )

    # bxor(97, 1) -> 96
    code = re.sub(
        r'\bbxor\(\s*(\d+)\s*,\s*(\d+)\s*\)',
        lambda m: str(int(m.group(1)) ^ int(m.group(2))),
        code
    )

    return code

def _xor_text_with_key(text: str, key: int) -> str:
    out = []
    for ch in text:
        out.append(chr(ord(ch) ^ key))
    return "".join(out)

def decode_xor_strings(code: str) -> str:
    # xor("abc", 23)
    pattern1 = r'\bxor\(\s*["\']([^"\']+)["\']\s*,\s*(\d{1,3})\s*\)'
    # bitxor_string("abc", 23)
    pattern2 = r'\bbitxor_string\(\s*["\']([^"\']+)["\']\s*,\s*(\d{1,3})\s*\)'

    def repl(match):
        text = match.group(1)
        key = int(match.group(2))
        if not (0 <= key <= 255):
            return match.group(0)
        try:
            decoded = _xor_text_with_key(text, key)
            if _is_printable_text(decoded):
                return f'"{decoded}"'
        except Exception:
            pass
        return match.group(0)

    code = re.sub(pattern1, repl, code)
    code = re.sub(pattern2, repl, code)
    return code

def decode_xor_byte_tables(code: str) -> str:
    # xor({112,114,105,110,116}, 0) -> "print"
    pattern = r'\bxor\(\s*\{([0-9,\s]+)\}\s*,\s*(\d{1,3})\s*\)'

    def repl(match):
        nums = [int(x) for x in re.findall(r'\d+', match.group(1))]
        key = int(match.group(2))
        if not (0 <= key <= 255):
            return match.group(0)

        try:
            decoded = "".join(chr((n ^ key) & 0xFF) for n in nums if 0 <= n <= 255)
            if _is_printable_text(decoded):
                return f'"{decoded}"'
        except Exception:
            pass
        return match.group(0)

    return re.sub(pattern, repl, code)

def decode_xor_advanced(code: str) -> str:
    code = decode_xor_numbers(code)
    code = decode_xor_strings(code)
    code = decode_xor_byte_tables(code)
    return code

# ============================================
# VM / JUNK BREAKER
# ============================================

def vm_break(code: str) -> str:
    code = re.sub(r'loadstring\([^)]*\)', '-- removed loadstring', code)
    code = re.sub(r'pcall\([^)]*\)', '', code)
    code = re.sub(r'getfenv\([^)]*\)', 'nil', code)
    code = re.sub(r'setfenv\([^)]*\)', '-- removed setfenv', code)
    return code

# ============================================
# STRING TABLE RECONSTRUCTION
# ============================================

def reconstruct_tables(code: str) -> str:
    table_pattern = r'local\s+(\w+)\s*=\s*\{([^}]+)\}'
    tables = {}

    for match in re.finditer(table_pattern, code, re.DOTALL):
        name = match.group(1)
        content = match.group(2)

        strings = re.findall(r'"([^"]*)"|\'([^\']*)\'', content)
        decoded = []

        for s1, s2 in strings:
            val = s1 if s1 else s2
            try:
                val = bytes(val, "utf-8").decode("unicode_escape")
            except Exception:
                pass
            decoded.append(val)

        if decoded:
            tables[name] = decoded

    for table, values in tables.items():
        for i, val in enumerate(values, start=1):
            pattern = rf'{table}\s*\[\s*{i}\s*\]'
            safe_val = val.replace("\\", "\\\\").replace('"', '\\"')
            code = re.sub(pattern, f'"{safe_val}"', code)

    return code

# ============================================
# BYTECODE / CHUNK ANALYSIS
# ============================================

def _extract_quoted_strings(code: str):
    matches = re.findall(r'"([^"]*)"|\'([^\']*)\'', code)
    out = []
    for a, b in matches:
        out.append(a if a else b)
    return out

def _try_decode_lua_chunk_from_string(s: str):
    candidates = []

    # raw
    candidates.append(s)

    # unicode_escape / decimal escapes
    try:
        candidates.append(bytes(s, "utf-8").decode("unicode_escape"))
    except Exception:
        pass

    # base64
    try:
        decoded_b64 = base64.b64decode(s, validate=True)
        candidates.append(decoded_b64.decode("latin1", errors="ignore"))
    except Exception:
        pass

    for candidate in candidates:
        if candidate.startswith("\x1bLua"):
            return candidate

    return None

def analyze_bytecode(code: str) -> str:
    findings = []

    if "\x1bLua" in code:
        findings.append("Lua bytecode magic encontrado directamente en el script.")

    strings = _extract_quoted_strings(code)

    for s in strings:
        chunk = _try_decode_lua_chunk_from_string(s)
        if chunk:
            version = "desconocida"
            if len(chunk) >= 5:
                version_byte = ord(chunk[4])
                version = hex(version_byte)

            preview = chunk[:64]
            preview_safe = preview.encode("unicode_escape").decode("ascii")
            findings.append(
                f"Chunk Lua detectado. Version byte: {version}. Preview: {preview_safe}"
            )
            break

    if re.search(r'loadstring\s*\(', code):
        findings.append("Se detectó loadstring(...), posible loader o payload dinámico.")

    if re.search(r'\bstring\.dump\s*\(', code):
        findings.append("Se detectó string.dump(...), posible manipulación de bytecode.")

    if not findings:
        return (
            "No encontré un chunk Lua claro para decompilar.\n"
            "Este comando hace análisis básico y extracción; no reemplaza un decompiler real."
        )

    findings.append(
        "Nota: este análisis no hace decompilación real completa; solo detecta y extrae bytecode/chunks."
    )
    return "\n".join(f"- {x}" for x in findings)

# ============================================
# MULTI LAYER DEOB
# ============================================

def multi_layer_deob(code: str, passes: int = 6) -> str:
    previous = ""

    for _ in range(passes):
        if code == previous:
            break

        previous = code

        code = decode_string_char(code)
        code = decode_decimal(code)
        code = decode_hex_numbers(code)
        code = decode_reverse(code)
        code = decode_concat(code)
        code = decode_base64_literals(code)
        code = decode_xor_advanced(code)
        code = reconstruct_tables(code)
        code = vm_break(code)

    return code

# ============================================
# PER-OBF HELPERS
# ============================================

def wearedevs_deob(code: str) -> str:
    code = multi_layer_deob(code)
    code = re.sub(
        r'if\s+(getfenv|debug\.getinfo|identifyexecutor)[^\n]*',
        '-- removed anti debug',
        code
    )
    return code

def moonsec_deob(code: str) -> str:
    # best-effort internal cleanup
    code = multi_layer_deob(code)
    code = re.sub(r'setfenv\([^)]*\)', '-- removed setfenv', code)
    return code

def ironbrew_deob(code: str) -> str:
    # best-effort internal cleanup
    code = multi_layer_deob(code)
    code = re.sub(r'bit32\.[a-z_]+\([^)]*\)', '-- removed bit32 op', code)
    return code

# ============================================
# DETECTOR
# ============================================

def detect_obfuscator(code: str) -> str:
    code_lower = code.lower()

    if (
        "wearedevs.net/obfuscator" in code_lower
        or "prometheus" in code_lower
        or "phase_boundary" in code_lower
    ):
        return "wearedevs"

    if (
        "moonsec" in code_lower
        or re.search(r'local\s+_env', code_lower)
        or re.search(r'setfenv\(', code_lower)
    ):
        return "moonsec"

    if (
        "ironbrew" in code_lower
        or "ib2" in code_lower
        or "aztupbrew" in code_lower
    ):
        return "ironbrew"

    if "lph!" in code_lower or "luraph" in code_lower:
        return "luraph"

    if "bytecode" in code_lower and "vm" in code_lower:
        return "vm"

    return "unknown"

# ============================================
# COMMANDS
# ============================================

@bot.command()
async def detect(ctx, *, arg=None):
    code = await get_code(ctx, arg)

    if not code or len(code.strip()) == 0:
        await ctx.send("❌ No encontré código.")
        return

    obf = detect_obfuscator(code)

    embed = discord.Embed(
        title="🔍 Obfuscator Detector",
        description=f"Detectado: **{obf}**",
        color=COLOR_ALT
    )
    await ctx.send(embed=embed)

@bot.command()
async def beautify_cmd(ctx, *, arg=None):
    code = await get_code(ctx, arg)

    if not code:
        await ctx.send("❌ No encontré código.")
        return

    result = beautify(code)
    await send_result(ctx, "🧹 Beautify Lua", result, filename="beautified.lua")

@bot.command(name="beautify")
async def beautify_alias(ctx, *, arg=None):
    await beautify_cmd(ctx, arg=arg)

@bot.command()
async def wearedevs(ctx, *, arg=None):
    code = await get_code(ctx, arg)

    if not code:
        await ctx.send("❌ No encontré código.")
        return

    result = wearedevs_deob(code)
    result = beautify(result)

    await send_result(ctx, "🟢 WeAreDevs Deobfuscated", result, filename="wearedevs_deob.lua")

@bot.command()
async def moonsec(ctx, *, arg=None):
    code = await get_code(ctx, arg)

    if not code:
        await ctx.send("❌ No encontré código.")
        return

    result = moonsec_deob(code)
    result = beautify(result)

    await send_result(ctx, "🌙 MoonSec Deobfuscated", result, filename="moonsec_deob.lua")

@bot.command()
async def ironbrew(ctx, *, arg=None):
    code = await get_code(ctx, arg)

    if not code:
        await ctx.send("❌ No encontré código.")
        return

    result = ironbrew_deob(code)
    result = beautify(result)

    await send_result(ctx, "⚙ IronBrew Deobfuscated", result, filename="ironbrew_deob.lua")

@bot.command()
async def deob(ctx, *, arg=None):
    code = await get_code(ctx, arg)

    if not code:
        await ctx.send("❌ No encontré código.")
        return

    obf = detect_obfuscator(code)

    if obf == "wearedevs":
        result = wearedevs_deob(code)
    elif obf == "moonsec":
        result = moonsec_deob(code)
    elif obf == "ironbrew":
        result = ironbrew_deob(code)
    else:
        result = multi_layer_deob(code)

    result = beautify(result)

    await send_result(ctx, f"⚡ Auto Deob ({obf})", result, filename="auto_deob.lua")

@bot.command()
async def strings(ctx, *, arg=None):
    code = await get_code(ctx, arg)

    if not code:
        await ctx.send("❌ No encontré código.")
        return

    matches = re.findall(r'"([^"]+)"', code)
    preview = "\n".join(matches[:200]) if matches else "No encontré strings entre comillas dobles."

    await send_result(ctx, "📜 Extracted Strings", preview, filename="strings.txt")

@bot.command()
async def tables(ctx, *, arg=None):
    code = await get_code(ctx, arg)

    if not code:
        await ctx.send("❌ No encontré código.")
        return

    matches = re.findall(r'\{([^}]+)\}', code)
    preview = "\n\n".join(matches[:80]) if matches else "No encontré tablas simples."

    await send_result(ctx, "📦 Table Data", preview, filename="tables.txt")

@bot.command()
async def bytecode(ctx, *, arg=None):
    code = await get_code(ctx, arg)

    if not code:
        await ctx.send("❌ No encontré código.")
        return

    result = analyze_bytecode(code)
    await send_result(ctx, "🧠 Bytecode Analysis", result, filename="bytecode_analysis.txt")

# ============================================
# HELP
# ============================================

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="🟣 Cypher Deob Bot",
        description="Advanced Lua Deobfuscation Toolkit",
        color=COLOR_MAIN
    )

    embed.add_field(
        name="🔍 $detect",
        value="Detecta el tipo de obfuscador.",
        inline=False
    )

    embed.add_field(
        name="⚡ $deob",
        value="Deobfuscación automática multicapa.",
        inline=False
    )

    embed.add_field(
        name="🟢 $wearedevs",
        value="Deobfuscador Prometheus / WeAreDevs.",
        inline=False
    )

    embed.add_field(
        name="🌙 $moonsec",
        value="Deobfuscador MoonSec.",
        inline=False
    )

    embed.add_field(
        name="⚙ $ironbrew",
        value="Deobfuscador IronBrew / AztupBrew.",
        inline=False
    )

    embed.add_field(
        name="🧹 $beautify",
        value="Formatea código Lua.",
        inline=False
    )

    embed.add_field(
        name="📜 $strings",
        value="Extrae strings del script.",
        inline=False
    )

    embed.add_field(
        name="📦 $tables",
        value="Muestra datos de tablas.",
        inline=False
    )

    embed.add_field(
        name="🧠 $bytecode",
        value="Analiza y extrae bytecode/chunks Lua de forma básica.",
        inline=False
    )

    embed.set_footer(text="Cypher Deob Bot • Lua Reverse Toolkit")
    await ctx.send(embed=embed)

# ============================================
# RUN
# ============================================

bot.run(TOKEN)
