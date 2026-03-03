# Cypher Deob Bot
# Prefijo: $

import discord
from discord.ext import commands
import aiohttp
import re
import os
import io
import sys
import importlib.util
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("ERROR: DISCORD_TOKEN no encontrado")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)

# -----------------------------
# FIX PATHS (carpetas con espacios)
# -----------------------------

sys.path.append(os.getcwd())
sys.path.append("Moonsec V3 Deobfuscator")
sys.path.append("IronBrew Deobfuscator")
sys.path.append("WeAreDevs deobfuscator")

# -----------------------------
# Loader de módulos
# -----------------------------

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# -----------------------------
# Cargar deobfuscadores
# -----------------------------

try:
    moonsec_module = load_module(
        "moonsec_deob",
        "Moonsec V3 Deobfuscator/Deobfuscator.py"
    )
except:
    moonsec_module = None

try:
    ironbrew_module = load_module(
        "ironbrew_deob",
        "IronBrew Deobfuscator/main.py"
    )
except:
    ironbrew_module = None

try:
    wearedevs_module = load_module(
        "wearedevs_deob",
        "WeAreDevs deobfuscator/controller_main.py"
    )
except:
    wearedevs_module = None


# -----------------------------
# Helpers
# -----------------------------

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


def detect_obfuscator(code):

    if "MoonSec" in code or "moonsec" in code:
        return "moonsec"

    if "IronBrew" in code or "IB2" in code:
        return "ironbrew"

    if "Prometheus" in code or "PHASE_BOUNDARY" in code:
        return "wearedevs"

    if "VM" in code and "BYTECODE" in code:
        return "vm"

    return "unknown"


def beautify(code):

    lines = code.split("\n")

    indent = 0
    result = []

    for line in lines:

        line = line.strip()

        if line.startswith("end"):
            indent -= 1

        result.append("    "*max(indent,0)+line)

        if re.search(r"\bthen\b|\bdo\b|\bfunction\b", line):
            indent += 1

    return "\n".join(result)


async def send_result(ctx, title, code):

    if len(code) > 3900:

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


# -----------------------------
# BOT READY
# -----------------------------

@bot.event
async def on_ready():
    print(f"Cypher Deob Bot listo como {bot.user}")


# -----------------------------
# DETECT
# -----------------------------

@bot.command()
async def detect(ctx, *, arg=None):

    code = await get_code(ctx, arg)

    if not code:
        await ctx.send("No se encontró código.")
        return

    result = detect_obfuscator(code)

    embed = discord.Embed(
        title="Detector",
        description=f"Obfuscador detectado: **{result}**",
        color=0x7C3AED
    )

    await ctx.send(embed=embed)


# -----------------------------
# BEAUTIFY
# -----------------------------

@bot.command()
async def beautify(ctx, *, arg=None):

    code = await get_code(ctx, arg)

    if not code:
        return

    result = beautify(code)

    await send_result(ctx,"Beautify",result)


# -----------------------------
# MOONSEC
# -----------------------------

@bot.command()
async def moonsec(ctx, *, arg=None):

    if not moonsec_module:
        await ctx.send("Moonsec module no disponible.")
        return

    code = await get_code(ctx,arg)

    try:
        result = moonsec_module.deobfuscate(code)
    except:
        result = code

    await send_result(ctx,"Moonsec Deobfuscado",result)


# -----------------------------
# IRONBREW
# -----------------------------

@bot.command()
async def ironbrew(ctx, *, arg=None):

    if not ironbrew_module:
        await ctx.send("IronBrew module no disponible.")
        return

    code = await get_code(ctx,arg)

    try:
        result = ironbrew_module.main(code)
    except:
        result = code

    await send_result(ctx,"IronBrew Deobfuscado",result)


# -----------------------------
# WEAREDEVS
# -----------------------------

@bot.command()
async def wearedevs(ctx, *, arg=None):

    if not wearedevs_module:
        await ctx.send("WeAreDevs module no disponible.")
        return

    code = await get_code(ctx,arg)

    try:
        result = wearedevs_module.main(code)
    except:
        result = code

    await send_result(ctx,"WeAreDevs Deobfuscado",result)


# -----------------------------
# AUTO DEOB
# -----------------------------

@bot.command()
async def deob(ctx, *, arg=None):

    code = await get_code(ctx,arg)

    if not code:
        return

    obf = detect_obfuscator(code)

    if obf == "moonsec":
        await moonsec(ctx,arg=code)
        return

    if obf == "ironbrew":
        await ironbrew(ctx,arg=code)
        return

    if obf == "wearedevs":
        await wearedevs(ctx,arg=code)
        return

    await ctx.send("No pude detectar el obfuscador.")


# -----------------------------
# HELP
# -----------------------------

@bot.command()
async def help(ctx):

    embed = discord.Embed(
        title="Cypher Deob Bot",
        color=0xA855F7
    )

    embed.add_field(
        name="$detect",
        value="Detecta el obfuscador",
        inline=False
    )

    embed.add_field(
        name="$deob",
        value="Deobfuscación automática",
        inline=False
    )

    embed.add_field(
        name="$moonsec",
        value="Deobfuscador Moonsec",
        inline=False
    )

    embed.add_field(
        name="$ironbrew",
        value="Deobfuscador IronBrew",
        inline=False
    )

    embed.add_field(
        name="$wearedevs",
        value="Deobfuscador Prometheus",
        inline=False
    )

    embed.add_field(
        name="$beautify",
        value="Formatea código Lua",
        inline=False
    )

    await ctx.send(embed=embed)


bot.run(TOKEN)
