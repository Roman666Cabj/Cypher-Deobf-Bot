# Cypher Deob Bot PRO
# Prefijo $

import discord
from discord.ext import commands
import aiohttp
import re
import os
import io
from dotenv import load_dotenv

# =====================
# CONFIG
# =====================

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("DISCORD_TOKEN no encontrado")
    exit()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="$",
    intents=intents,
    help_command=None
)

MAX_PREVIEW = 3900


# =====================
# BOT READY
# =====================

@bot.event
async def on_ready():
    print(f"Cypher Deob Bot activo como {bot.user}")


# =====================
# CODE FETCH
# =====================

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


# =====================
# RESULT OUTPUT
# =====================

async def send_result(ctx, title, code):

    code = str(code)

if len(code) > MAX_PREVIEW:

        file = discord.File(
            io.BytesIO(code.encode()),
            filename="deob.lua"
        )

        embed = discord.Embed(
            title=title,
            description="Resultado enviado como archivo",
            color=0xA855F7
        )

        await ctx.send(embed=embed, file=file)

    else:

        embed = discord.Embed(
            title=title,
            description=f"```lua\n{code}\n```",
            color=0xA855F7
        )

        await ctx.send(embed=embed)


# =====================
# BEAUTIFY
# =====================

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


# =====================
# DECODERS
# =====================

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


# =====================
# VM BREAKER
# =====================

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


# =====================
# TABLE RECONSTRUCTION
# =====================

def reconstruct_tables(code):

    table_pattern = r'local\s+(\w+)\s*=\s*\{(.*?)\}'

    tables = {}

    for match in re.finditer(table_pattern, code, re.DOTALL):

        name = match.group(1)
        content = match.group(2)

        strings = re.findall(r'"(.*?)"|\'(.*?)\'', content)

        decoded = []

        for s1, s2 in strings:

            val = s1 if s1 else s2

            try:
                val = bytes(val,"utf8").decode("unicode_escape")
            except:
                pass

            decoded.append(val)

        tables[name] = decoded

    for table,values in tables.items():

        for i,val in enumerate(values):

            pattern = rf"{table}\s*\[\s*{i+1}\s*\]"

            code = re.sub(pattern,f'"{val}"',code)

    code = re.sub(table_pattern,"-- removed obfuscation table",code)

    return code


# =====================
# WEAREDEVS DEOB
# =====================

def wearedevs_deob(code):

    code = reconstruct_tables(code)

    code = decode_string_char(code)

    code = decode_decimal(code)

    code = vm_break(code)

    code = re.sub(
        r'if\s+(getfenv|debug\.getinfo|identifyexecutor)[^\n]*',
        '-- removed anti debug',
        code
    )

    return code


# =====================
# DETECTOR
# =====================

def detect_obfuscator(code):

    if "PHASE_BOUNDARY" in code:
        return "wearedevs"

    if "MoonSec" in code:
        return "moonsec"

    if "IronBrew" in code:
        return "ironbrew"

    if "LPH!" in code:
        return "luraph"

    return "unknown"


# =====================
# COMMANDS
# =====================

@bot.command()
async def detect(ctx, *, arg=None):

    code = await get_code(ctx,arg)

    if not code:
        await ctx.send("No encontré código")
        return

    obf = detect_obfuscator(code)

    embed = discord.Embed(
        title="Detector",
        description=f"Detectado: **{obf}**",
        color=0x7C3AED
    )

    await ctx.send(embed=embed)


@bot.command()
async def beautify(ctx, *, arg=None):

    code = await get_code(ctx,arg)

    if not code:
        return

    result = beautify(code)

    await send_result(ctx,"Beautify",result)


@bot.command()
async def wearedevs(ctx, *, arg=None):

    code = await get_code(ctx,arg)

    if not code:
        return

    result = await wearedevs_deob(code)

    result = beautify(result)

    await send_result(ctx,"WeAreDevs Deobfuscado",result)


@bot.command()
async def deob(ctx, *, arg=None):

    code = await get_code(ctx,arg)

    if not code:
        return

    obf = detect_obfuscator(code)

    if obf == "wearedevs":

        code = wearedevs_deob(code)

    code = beautify(code)

    await send_result(ctx,f"Deobfuscado ({obf})",code)


# =====================
# HELP
# =====================

@bot.command()
async def help(ctx):

    embed = discord.Embed(
        title="Cypher Deob Bot PRO",
        color=0xA855F7
    )

    embed.add_field(
        name="$detect",
        value="Detecta obfuscador",
        inline=False
    )

    embed.add_field(
        name="$deob",
        value="Deob automático",
        inline=False
    )

    embed.add_field(
        name="$wearedevs",
        value="Deobfuscador Prometheus",
        inline=False
    )

    embed.add_field(
        name="$beautify",
        value="Formatea código",
        inline=False
    )

    await ctx.send(embed=embed)


# =====================
# RUN
# =====================

bot.run(TOKEN)
