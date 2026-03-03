# bot.py - Cypher Deob Bot - Prefijo: $

import discord
from discord.ext import commands
import aiohttp
import re
import os
import io
from dotenv import load_dotenv
import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("ERROR: No encontré DISCORD_TOKEN en .env / Variables")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

# Colores del tema Cypher
VIOLET = 0xA855F7
PURPLE = 0x7C3AED
EMERALD = 0x10B981
ROSE = 0xE11D48
AMBER = 0xD97706
CYAN = 0x00FFFF

MAX_PREVIEW = 3900  # Embed description \~4096 (dejamos margen por ```lua)

@bot.event
async def on_ready():
    print(f'Cypher Deob Bot conectado como {bot.user} (ID: {bot.user.id})')
    print('Prefijo: $')
    print('-' * 50)

# Función auxiliar: obtener código de mensaje, adjunto o link
async def get_code(ctx, code_or_link: str = None):
    if ctx.message.attachments:
        att = ctx.message.attachments[0]
        if not att.filename.lower().endswith(('.lua', '.txt', '.log')):
            await ctx.send("Solo archivos .lua, .txt o .log por favor.")
            return None
        async with aiohttp.ClientSession() as session:
            async with session.get(att.url) as resp:
                if resp.status != 200:
                    await ctx.send("No pude descargar el archivo adjunto.")
                    return None
                return await resp.text(encoding='utf-8')

    if code_or_link:
        if code_or_link.startswith(('http://', 'https://')):
            async with aiohttp.ClientSession() as session:
                async with session.get(code_or_link) as resp:
                    if resp.status != 200:
                        await ctx.send("Link inválido o no accesible.")
                        return None
                    return await resp.text(encoding='utf-8')
        return code_or_link

    await ctx.send("Pega código Lua, un link o adjunta un archivo.")
    return None

# Enviar resultado sin romper límites de Discord
async def send_result(ctx, title: str, color: int, code_text: str, notes: str = None, filename: str = "deob.lua"):
    if code_text is None:
        await ctx.send("No hay resultado para mostrar.")
        return

    # Si es demasiado largo, mandar archivo
    if len(code_text) > MAX_PREVIEW:
        file = discord.File(io.BytesIO(code_text.encode("utf-8")), filename=filename)
        embed = discord.Embed(
            title=title,
            description="Resultado muy largo, te lo envié como archivo adjunto ✅",
            color=color
        )
        if notes:
            embed.add_field(name="Notas", value=notes[:1024], inline=False)
        await ctx.send(embed=embed, file=file)
        return

    # Si entra, mandar embed normal
    embed = discord.Embed(
        title=title,
        description=f"```lua\n{code_text}\n```",
        color=color
    )
    if notes:
        embed.add_field(name="Notas", value=notes[:1024], inline=False)
    await ctx.send(embed=embed)

# Beautify simple pero efectivo
def beautify_code(code: str) -> str:
    lines = code.split('\n')
    indent_level = 0
    result = []

    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            result.append('')
            continue

        if re.match(r'^(end\b|else\b|elseif\b|until\b|\}|\))', trimmed):
            indent_level = max(0, indent_level - 1)

        indented = '  ' * indent_level + trimmed

        if re.match(r'^(local\s+)?function\b|if\b|for\b|while\b|repeat\b|then\b|else\b|elseif\b|do\b|\{', trimmed) or \
           trimmed.endswith(('do', '{', 'then')):
            indent_level += 1

        result.append(indented)

    return '\n'.join(result)

# Undo avanzado general
def advanced_undo(code: str) -> str:
    # string.char(...)
    code = re.sub(
        r'string\.char\s*\(\s*([^)]+)\s*\)',
        lambda m: '"' + ''.join(chr(int(n.strip())) for n in re.findall(r'\d+', m.group(1))) + '"',
        code
    )

    # Join split strings
    code = re.sub(r"'([^']*)'\s*\.\.\s*'([^']*)'", r'"\1\2"', code)
    code = re.sub(r'"([^"]*)"\s*\.\.\s*"([^"]*)"', r'"\1\2"', code)

    # Proxy locals
    code = re.sub(r'local\s+(\w+)\s*=\s*proxy_(\w+)', r'local \2 = proxy_\1 -- proxy undone', code)

    # Constants
    code = re.sub(r'CONST\[(\d+)\]', r'"CONST_\1"', code)

    return code

# Reconstrucción desde log
def reconstruct_from_log(log_text: str) -> str:
    reconstructed = '-- Reconstruido aproximado desde log/env dump\n'
    lines = log_text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('print('):
            match = re.search(r'print\("([^"]+)"\)', line)
            if match:
                reconstructed += f'print("{match.group(1)}")\n'
        if 'loadstring' in line or 'LOADSTRING' in line:
            reconstructed += '-- Loadstring detectado\n'
        if 'Instance.new' in line:
            match = re.search(r'Instance\.new\("([^"]+)"\)', line)
            if match:
                reconstructed += f'local obj = Instance.new("{match.group(1)}")\n'
        if '[LARGE CONCAT]' in line or 'PAYLOAD' in line:
            reconstructed += '-- Payload grande detectado\n'
    reconstructed += '\n-- Usa $deob o Grok para reconstrucción completa'
    return reconstructed

# $moonsec - Deobfuscador + intento de limpieza básica
@bot.command(name='moonsec')
async def moonsec(ctx, *, code_or_link: str = None):
    code = await get_code(ctx, code_or_link)
    if not code:
        return

    try:
        # Limpieza típica Moonsec V3: comentarios largos + string.char
        code = re.sub(r'--\[\[.*?\]\]--', '', code, flags=re.DOTALL)  # comentarios multilínea
        code = re.sub(
            r'string\.char\s*\(\s*([^)]+)\s*\)',
            lambda m: '"' + ''.join(chr(int(n.strip())) for n in re.findall(r'\d+', m.group(1))) + '"',
            code
        )
        code = re.sub(r'local\s+\w+\s*=\s*loadstring', '-- loadstring removido', code)

        beautified = beautify_code(code)
        undone = advanced_undo(beautified)

        await send_result(
            ctx,
            title="Moonsec V3 - Procesado",
            color=PURPLE,
            code_text=undone,
            notes="Limpieza de junk + undo strings + beautify básico",
            filename="moonsec_deob.lua"
        )

    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

# $ironbrew - Limpieza básica
@bot.command(name='ironbrew')
async def ironbrew(ctx, *, code_or_link: str = None):
    code = await get_code(ctx, code_or_link)
    if not code:
        return

    try:
        code = re.sub(
            r'local\s+\w+\s*=\s*loadstring\(game:HttpGet\(".*?"\)\)',
            '-- IronBrew loader removido',
            code
        )
        code = re.sub(r'\[\[\s*VM\s*PROTECTED\s*\]\]', '-- VM protected removed', code)
        code = re.sub(r'(\w+)\s*=\s*(\w+)\[(\d+)\]', r'\1 = "\2[\3]" -- IronBrew unpack', code)

        beautified = beautify_code(code)
        undone = advanced_undo(beautified)

        await send_result(
            ctx,
            title="IronBrew - Procesado",
            color=ROSE,
            code_text=undone,
            notes="Removido VM junk + loaders + unpack básico",
            filename="ironbrew_deob.lua"
        )

    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

# $wearedevs - Limpieza básica
@bot.command(name='wearedevs')
async def wearedevs(ctx, *, code_or_link: str = None):
    code = await get_code(ctx, code_or_link)
    if not code:
        return

    try:
        code = re.sub(r'--\s*PHASE_BOUNDARY[^\n]*\n?', '', code)
        code = re.sub(
            r'if\s+(getfenv|debug\.getinfo|synapse|krnl|identifyexecutor)[^\n]*\n?',
            '-- [ANTI-DEBUG REMOVIDO]\n',
            code
        )
        code = re.sub(r'local\s+\w+\s*=\s*getrenv\(\)', '-- getrenv removido', code)

        beautified = beautify_code(code)
        undone = advanced_undo(beautified)

        await send_result(
            ctx,
            title="WeAreDevs / Prometheus - Procesado",
            color=EMERALD,
            code_text=undone,
            notes="Removido phase boundaries + anti-debug + loaders",
            filename="wearedevs_deob.lua"
        )

    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="🟣 Cypher Deob Bot - Comandos",
        color=VIOLET
    )

    embed.add_field(
        name="$moonsec",
        value="Procesa scripts tipo Moonsec",
        inline=False
    )

    embed.add_field(
        name="$ironbrew",
        value="Procesa scripts tipo IronBrew",
        inline=False
    )

    embed.add_field(
        name="$wearedevs",
        value="Procesa scripts tipo WeAreDevs / Prometheus",
        inline=False
    )

    embed.add_field(
        name="Uso",
        value="Podés pegar código, mandar archivo (.lua/.txt/.log) o pasar link.",
        inline=False
    )

    embed.set_footer(text="Cypher Deob Bot • Prefijo: $")

    await ctx.send(embed=embed)

# Iniciar bot
bot.run(TOKEN)
