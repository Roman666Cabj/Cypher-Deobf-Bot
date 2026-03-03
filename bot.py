import discord
from discord.ext import commands
import aiohttp
import os
import io
import time

from dotenv import load_dotenv

from detector import detect_obfuscator
from string_resolver import decode_lua_decimal_escapes, resolve_string_tables
from ast_rebuilder import rebuild_ast
from pipeline import run_pipeline
from vm_breaker import detect_vm, break_vm

from Moonsec_V3_Deobfuscator.script_processor import process_script as moonsec_deob
from Moonsec_V3_Decompiler.decompiler import decompile as moonsec_decompile
from IronBrew_Deobfuscator.script_processor import process_script as ironbrew_deob
from WeAreDevs_deobfuscator.script_processor import process_script as wearedevs_deob


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="$",
    intents=intents,
    help_command=None
)

MAX_PREVIEW = 3900

VIOLET = 0xA855F7
PURPLE = 0x7C3AED
EMERALD = 0x10B981
CYAN = 0x00FFFF

START_TIME = time.time()


@bot.event
async def on_ready():
    print(f"Cypher Deob Bot conectado como {bot.user}")


# -----------------------------
# Obtener código
# -----------------------------
async def get_code(ctx, code_or_link=None):

    if ctx.message.attachments:

        att = ctx.message.attachments[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(att.url) as resp:
                return await resp.text()

    if code_or_link:

        if code_or_link.startswith("http"):

            async with aiohttp.ClientSession() as session:
                async with session.get(code_or_link) as resp:
                    return await resp.text()

        return code_or_link

    await ctx.send("Pega código, archivo o link.")
    return None


# -----------------------------
# Enviar resultado
# -----------------------------
async def send_result(ctx, title, color, text):

    if len(text) > MAX_PREVIEW:

        file = discord.File(
            io.BytesIO(text.encode()),
            filename="deob.lua"
        )

        embed = discord.Embed(
            title=title,
            description="Resultado enviado como archivo",
            color=color
        )

        await ctx.send(embed=embed, file=file)

    else:

        embed = discord.Embed(
            title=title,
            description=f"```lua\n{text}\n```",
            color=color
        )

        await ctx.send(embed=embed)


# -----------------------------
# HELP
# -----------------------------
@bot.command()
async def help(ctx):

    embed = discord.Embed(
        title="🟣 Cypher Deob Bot",
        description="Advanced Lua Deobfuscation Toolkit",
        color=VIOLET
    )

    embed.add_field(
        name="🔍 Detection",
        value="`$detect <code/link>`",
        inline=False
    )

    embed.add_field(
        name="🤖 Auto Deob",
        value="`$deob <code/link>`",
        inline=False
    )

    embed.add_field(
        name="🌙 Moonsec",
        value="`$moonsec <code/link>`",
        inline=False
    )

    embed.add_field(
        name="⚙ IronBrew",
        value="`$ironbrew <code/link>`",
        inline=False
    )

    embed.add_field(
        name="🟢 WeAreDevs",
        value="`$wearedevs <code/link>`",
        inline=False
    )

    embed.add_field(
        name="✨ Beautify",
        value="`$beautify <code/link>`",
        inline=False
    )

    embed.add_field(
        name="📊 Stats",
        value="`$stats`",
        inline=False
    )

    embed.set_footer(text="Cypher Lua Reverse Toolkit")

    await ctx.send(embed=embed)


# -----------------------------
# DETECT
# -----------------------------
@bot.command()
async def detect(ctx, *, code_or_link=None):

    code = await get_code(ctx, code_or_link)

    if not code:
        return

    code = decode_lua_decimal_escapes(code)

    obf = detect_obfuscator(code)

    embed = discord.Embed(
        title="Obfuscator Detector",
        description=f"Detectado: **{obf}**",
        color=CYAN
    )

    await ctx.send(embed=embed)


# -----------------------------
# AUTO DEOB
# -----------------------------
@bot.command()
async def deob(ctx, *, code_or_link=None):

    code = await get_code(ctx, code_or_link)

    if not code:
        return

    code = decode_lua_decimal_escapes(code)
    code = resolve_string_tables(code)

    if detect_vm(code):
        code = break_vm(code)

    try:

        result, layers = run_pipeline(code)

        layer_text = " → ".join(layers)

        embed = discord.Embed(
            title="Auto Deobfuscation",
            description=f"Layers:\n`{layer_text}`",
            color=EMERALD
        )

        await ctx.send(embed=embed)

        await send_result(ctx, "Resultado", EMERALD, result)

    except Exception as e:

        await ctx.send(f"Error: {e}")


# -----------------------------
# MOONSEC
# -----------------------------
@bot.command()
async def moonsec(ctx, *, code_or_link=None):

    code = await get_code(ctx, code_or_link)

    stage1 = moonsec_deob(code)
    result = moonsec_decompile(stage1)

    result = rebuild_ast(result)

    await send_result(ctx, "Moonsec Deob", PURPLE, result)


# -----------------------------
# IRONBREW
# -----------------------------
@bot.command()
async def ironbrew(ctx, *, code_or_link=None):

    code = await get_code(ctx, code_or_link)

    result = ironbrew_deob(code)

    result = rebuild_ast(result)

    await send_result(ctx, "IronBrew Deob", VIOLET, result)


# -----------------------------
# WEAREDEVS
# -----------------------------
@bot.command()
async def wearedevs(ctx, *, code_or_link=None):

    code = await get_code(ctx, code_or_link)

    result = wearedevs_deob(code)

    result = rebuild_ast(result)

    await send_result(ctx, "WeAreDevs Deob", EMERALD, result)


# -----------------------------
# BEAUTIFY
# -----------------------------
@bot.command()
async def beautify(ctx, *, code_or_link=None):

    code = await get_code(ctx, code_or_link)

    result = rebuild_ast(code)

    await send_result(ctx, "Beautified Lua", PURPLE, result)


# -----------------------------
# STATS
# -----------------------------
@bot.command()
async def stats(ctx):

    uptime = int(time.time() - START_TIME)

    embed = discord.Embed(
        title="Cypher Bot Stats",
        color=CYAN
    )

    embed.add_field(name="Uptime", value=f"{uptime}s")
    embed.add_field(name="Commands", value="detect / deob / moonsec / ironbrew / wearedevs")

    await ctx.send(embed=embed)


bot.run(TOKEN)
