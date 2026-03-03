# ============================================
# Cypher Deob Bot PRO
# Prefix $
# ============================================

import discord
from discord.ext import commands
import aiohttp
import re
import os
import io
import inspect
from dotenv import load_dotenv

# ============================================
# CONFIG
# ============================================

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("ERROR: DISCORD_TOKEN no encontrado")
    exit()

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

# ============================================
# BOT READY
# ============================================

@bot.event
async def on_ready():
    print(f"🟣 Cypher Deob Bot activo como {bot.user}")
    print("Prefijo: $")
    print("-" * 40)

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

        if arg.startswith("http"):

            async with aiohttp.ClientSession() as session:
                async with session.get(arg) as r:
                    return await r.text()

        return arg

    return None

# ============================================
# SEND RESULT
# ============================================

async def send_result(ctx, title, code):

    code = str(code)

    if len(code) > MAX_PREVIEW:

        file = discord.File(
            io.BytesIO(code.encode()),
            filename="deob.lua"
        )

        embed = discord.Embed(
            title=title,
            description="📁 Resultado demasiado largo, enviado como archivo.",
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

async def resolve_async(value):

    if inspect.iscoroutine(value):
        value = await value

    return value

# ============================================
# BEAUTIFY
# ============================================

def beautify(code):

    lines = code.split("\n")

    indent = 0
    result = []

    for line in lines:

        stripped = line.strip()

        if stripped.startswith(("end","elseif","else","until")):
            indent -= 1

        result.append("    "*max(indent,0) + stripped)

        if re.search(r"\bthen\b|\bdo\b|\bfunction\b", stripped):
            indent += 1

    return "\n".join(result)

# ============================================
# DECODERS
# ============================================

def decode_string_char(code):

    return re.sub(
        r'string\.char\((.*?)\)',
        lambda m: '"' + ''.join(
            chr(int(x))
            for x in re.findall(r'\d+', m.group(1))
        ) + '"',
        code
    )

def decode_decimal(code):

    def repl(m):

        n = int(m.group(1))

        if 0 <= n <= 255:
            return chr(n)

        return m.group(0)

    return re.sub(r'\\(\d{1,3})', repl, code)

def decode_hex(code):

    return re.sub(
        r'0x([0-9A-Fa-f]+)',
        lambda m: str(int(m.group(1),16)),
        code
    )

def decode_reverse(code):

    def repl(m):
        s = m.group(1)
        return '"' + s[::-1] + '"'

    return re.sub(
        r'string\.reverse\(\s*["\']([^"\']+)["\']\s*\)',
        repl,
        code
    )

def decode_concat(code):

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
# VM BREAKER
# ============================================

def vm_break(code):

    code = re.sub(
        r'loadstring\([^)]*\)',
        '-- removed loadstring',
        code
    )

    code = re.sub(
        r'pcall\([^)]*\)',
        '',
        code
    )

    code = re.sub(
        r'getfenv\([^)]*\)',
        'nil',
        code
    )

    return code

# ============================================
# STRING TABLE RECONSTRUCTION
# ============================================

def reconstruct_tables(code):

    table_pattern = r'local\s+(\w+)\s*=\s*\{([^}]+)\}'

    tables = {}

    for match in re.finditer(table_pattern, code, re.DOTALL):

        name = match.group(1)
        content = match.group(2)

        elements = re.findall(r'"([^"]*)"|\'([^\']*)\'', content)

        values = []

        for s1, s2 in elements:

            value = s1 if s1 else s2

            try:
                value = bytes(value, "utf-8").decode("unicode_escape")
            except:
                pass

            values.append(value)

        tables[name] = values

    for table, values in tables.items():

        for i, value in enumerate(values):

            pattern = rf"{table}\s*\[\s*{i+1}\s*\]"

            code = re.sub(pattern, f'"{value}"', code)

    code = re.sub(table_pattern, "-- removed string table", code)

    return code

# ============================================
# MULTI LAYER DEOB
# ============================================

def multi_layer_deob(code, passes=5):

    previous = ""

    for _ in range(passes):

        if code == previous:
            break

        previous = code

        code = decode_string_char(code)
        code = decode_decimal(code)
        code = decode_hex(code)
        code = decode_reverse(code)
        code = decode_concat(code)
        code = reconstruct_tables(code)
        code = vm_break(code)

    return code

# ============================================
# WEAREDEVS DEOB
# ============================================

def wearedevs_deob(code):

    code = multi_layer_deob(code)

    code = re.sub(
        r'if\s+(getfenv|debug\.getinfo|identifyexecutor)[^\n]*',
        '-- removed anti debug',
        code
    )

    return code

# ============================================
# DETECTOR
# ============================================

def detect_obfuscator(code):

    code_lower = code.lower()

    # WeAreDevs / Prometheus
    if (
        "wearedevs.net/obfuscator" in code_lower
        or "phase_boundary" in code_lower
        or "prometheus" in code_lower
    ):
        return "wearedevs"

    # MoonSec V3
    if (
        "moonsec" in code_lower
        or re.search(r'local\s+_env', code_lower)
        or re.search(r'setfenv\(', code_lower)
    ):
        return "moonsec"

    # IronBrew / forks
    if (
        "ironbrew" in code_lower
        or "ib2" in code_lower
        or "aztupbrew" in code_lower
    ):
        return "ironbrew"

    # Luraph
    if "lph!" in code_lower:
        return "luraph"

    # VM
    if "bytecode" in code_lower and "vm" in code_lower:
        return "vm"

    return "unknown"

# ============================================
# COMMANDS
# ============================================

@bot.command()
async def detect(ctx, *, arg=None):

    code = await get_code(ctx,arg)

    if not code or len(code.strip()) == 0:

    obf = detect_obfuscator(code)

    embed = discord.Embed(
        title="🔍 Obfuscator Detector",
        description=f"Detectado: **{obf}**",
        color=COLOR_ALT
    )

    await ctx.send(embed=embed)

# ============================================

@bot.command()
async def beautify(ctx, *, arg=None):

    code = await get_code(ctx,arg)

    if not code:
        return

    result = beautify(code)

    await send_result(ctx,"🧹 Beautify Lua",result)

# ============================================

@bot.command()
async def wearedevs(ctx, *, arg=None):

    code = await get_code(ctx, arg)

    if not code:
        await ctx.send("No se encontró código.")
        return

    result = wearedevs_deob(code)

    result = await resolve_async(result)

    result = beautify(result)

    await send_result(ctx, "🟢 WeAreDevs Deobfuscated", result)

# ============================================

@bot.command()
async def deob(ctx, *, arg=None):

    code = await get_code(ctx, arg)

    if not code:
        return

    obf = detect_obfuscator(code)

    if obf == "wearedevs":
        result = wearedevs_deob(code)
    else:
        result = code

    result = await resolve_async(result)

    result = multi_layer_deob(result)

    result = beautify(result)

    await send_result(ctx, f"⚡ Auto Deob ({obf})", result)

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
        value="Deobfuscador específico para Prometheus / WeAreDevs.",
        inline=False
    )

    embed.add_field(
        name="🧹 $beautify",
        value="Formatea código Lua para mejor lectura.",
        inline=False
    )

    embed.set_footer(text="Cypher Deob Bot • Lua Reverse Toolkit")

    await ctx.send(embed=embed)

# ============================================
# RUN
# ============================================

bot.run(TOKEN)
