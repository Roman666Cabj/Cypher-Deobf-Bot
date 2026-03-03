import discord
from discord.ext import commands
import aiohttp
import os
import io

from dotenv import load_dotenv

from detector import detect_obfuscator
from string_resolver import decode_lua_decimal_escapes, resolve_string_tables
from ast_rebuilder import rebuild_ast

# IMPORTAR DEOBFUSCADORES
from Moonsec_V3_Deobfuscator.script_processor import process_script as moonsec_deob
from Moonsec_V3_Decompiler.decompiler import decompile as moonsec_decompile
from IronBrew_Deobfuscator.script_processor import process_script as ironbrew_deob
from WeAreDevs_deobfuscator.script_processor import process_script as wearedevs_deob


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)

MAX_PREVIEW = 3900

VIOLET = 0xA855F7
PURPLE = 0x7C3AED
EMERALD = 0x10B981
CYAN = 0x00FFFF


@bot.event
async def on_ready():
    print(f"Cypher Deob Bot conectado como {bot.user}")


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


async def send_result(ctx,title,color,text):

    if len(text) > MAX_PREVIEW:

        file = discord.File(io.BytesIO(text.encode()), filename="deob.lua")

        embed = discord.Embed(
            title=title,
            description="Resultado enviado como archivo",
            color=color
        )

        await ctx.send(embed=embed,file=file)

    else:

        embed = discord.Embed(
            title=title,
            description=f"```lua\n{text}\n```",
            color=color
        )

        await ctx.send(embed=embed)


# DETECT

@bot.command()
async def detect(ctx,*,code_or_link=None):

    code = await get_code(ctx,code_or_link)

    if not code:
        return

    code = decode_lua_decimal_escapes(code)

    obf = detect_obfuscator(code)

    embed = discord.Embed(
        title="Detector",
        description=f"Detectado: **{obf}**",
        color=CYAN
    )

    await ctx.send(embed=embed)


# AUTO DEOB

@bot.command()
async def deob(ctx,*,code_or_link=None):

    code = await get_code(ctx,code_or_link)

    if not code:
        return

    code = decode_lua_decimal_escapes(code)
    code = resolve_string_tables(code)

    obf = detect_obfuscator(code)

    try:

        if obf == "moonsec":

            stage1 = moonsec_deob(code)
            result = moonsec_decompile(stage1)

        elif obf == "ironbrew":

            result = ironbrew_deob(code)

        elif obf == "wearedevs":

            result = wearedevs_deob(code)

        else:

            result = rebuild_ast(code)

        result = rebuild_ast(result)

        await send_result(ctx,f"Auto Deob ({obf})",EMERALD,result)

    except Exception as e:

        await ctx.send(f"Error: {e}")


# MOONSEC

@bot.command()
async def moonsec(ctx,*,code_or_link=None):

    code = await get_code(ctx,code_or_link)

    stage1 = moonsec_deob(code)
    result = moonsec_decompile(stage1)

    result = rebuild_ast(result)

    await send_result(ctx,"Moonsec Deob",PURPLE,result)


# IRONBREW

@bot.command()
async def ironbrew(ctx,*,code_or_link=None):

    code = await get_code(ctx,code_or_link)

    result = ironbrew_deob(code)

    result = rebuild_ast(result)

    await send_result(ctx,"IronBrew Deob",VIOLET,result)


# WEAREDEVS

@bot.command()
async def wearedevs(ctx,*,code_or_link=None):

    code = await get_code(ctx,code_or_link)

    result = wearedevs_deob(code)

    result = rebuild_ast(result)

    await send_result(ctx,"WeAreDevs Deob",EMERALD,result)


# BEAUTIFY

@bot.command()
async def beautify(ctx,*,code_or_link=None):

    code = await get_code(ctx,code_or_link)

    result = rebuild_ast(code)

    await send_result(ctx,"Beautified Lua",PURPLE,result)


# HELP

@bot.command()
async def help(ctx):

    embed = discord.Embed(
        title="Cypher Deob Bot",
        color=VIOLET
    )

    embed.add_field(name="$detect",value="Detecta obfuscador",inline=False)
    embed.add_field(name="$deob",value="Deobfuscación automática",inline=False)
    embed.add_field(name="$moonsec",value="Moonsec Deob",inline=False)
    embed.add_field(name="$ironbrew",value="IronBrew Deob",inline=False)
    embed.add_field(name="$wearedevs",value="WeAreDevs Deob",inline=False)
    embed.add_field(name="$beautify",value="Formatea Lua",inline=False)

    await ctx.send(embed=embed)


bot.run(TOKEN)
