# bot.py (o main.py) - Cypher Deob Bot - Prefijo: $

import discord
from discord.ext import commands
import aiohttp
import re
import os
from dotenv import load_dotenv
import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("ERROR: No encontré DISCORD_TOKEN en .env")
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
    elif code_or_link:
        if code_or_link.startswith(('http://', 'https://')):
            async with aiohttp.ClientSession() as session:
                async with session.get(code_or_link) as resp:
                    if resp.status != 200:
                        await ctx.send("Link inválido o no accesible.")
                        return None
                    return await resp.text(encoding='utf-8')
        else:
            return code_or_link
    else:
        await ctx.send("Pega código Lua, un link o adjunta un archivo.")
        return None

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
    # string.char + unpack
    code = re.sub(
    r'string\.char\s*\(\s*([^)]+)\s*\)',
    lambda m: '"' + ''.join(chr(int(n)) for n in re.findall(r'\d+', m.group(1))) + '"',
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

# $moonsec - Deobfuscador + intento de decompilación básica para Moonsec V3
@bot.command(name='moonsec')
async def moonsec(ctx, *, code_or_link: str = None):
    code = await get_code(ctx, code_or_link)
    if not code:
        return

    try:
        # Limpieza típica Moonsec V3: remover junk, undo string ops
        code = re.sub(r'--\[\[.*?\]\]--', '', code, flags=re.DOTALL)  # comentarios largos
        code = re.sub(
    r'string\.char\s*\(\s*([^)]+)\s*\)',
    lambda m: '"' + ''.join(chr(int(n)) for n in re.findall(r'\d+', m.group(1))) + '"',
    code
)
        code = re.sub(r'local\s+\w+\s*=\s*loadstring', '-- loadstring removido', code)

        beautified = beautify_code(code)
        undone = advanced_undo(beautified)

        embed = discord.Embed(title="Moonsec V3 - Deobfuscado + Decompilación parcial", color=PURPLE)
        embed.add_field(name="Resultado", value=f"```lua\n{undone[:1900]}\n```", inline=False)
        embed.add_field(name="Notas", value="Limpieza de junk + undo strings + beautify básico", inline=False)
        if len(undone) > 1900:
            embed.add_field(name="Advertencia", value="Resultado truncado (muy largo)", inline=False)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

# $ironbrew - Deobfuscador para IronBrew
@bot.command(name='ironbrew')
async def ironbrew(ctx, *, code_or_link: str = None):
    code = await get_code(ctx, code_or_link)
    if not code:
        return

    try:
        # Limpieza típica IronBrew: remover VM junk, desempaquetar strings
        code = re.sub(r'local\s+\w+\s*=\s*loadstring\(game:HttpGet\(".*?"\)\)', '-- IronBrew loader removido', code)
        code = re.sub(r'\[\[\s*VM\s*PROTECTED\s*\]\]', '-- VM protected removed', code)
        code = re.sub(r'(\w+)\s*=\s*(\w+)\[(\d+)\]', r'\1 = "\2[\3]" -- IronBrew unpack', code)

        beautified = beautify_code(code)
        undone = advanced_undo(beautified)

        embed = discord.Embed(title="IronBrew - Deobfuscado", color=ROSE)
        embed.add_field(name="Resultado", value=f"```lua\n{undone[:1900]}\n```", inline=False)
        embed.add_field(name="Notas", value="Removido VM junk + loaders + unpack básico", inline=False)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

# $wearedevs - Deobfuscador para WeAreDevs/Prometheus
@bot.command(name='wearedevs')
async def wearedevs(ctx, *, code_or_link: str = None):
    code = await get_code(ctx, code_or_link)
    if not code:
        return

    try:
        # Limpieza típica WeAreDevs/Prometheus
        code = re.sub(r'--\s*PHASE_BOUNDARY[^\n]*\n?', '', code)
        code = re.sub(r'if\s+(getfenv|debug\.getinfo|synapse|krnl|identifyexecutor)[^\n]*\n?', '-- [ANTI-DEBUG REMOVIDO]\n', code)
        code = re.sub(r'local\s+\w+\s*=\s*getrenv\(\)', '-- getrenv removido', code)

        beautified = beautify_code(code)
        undone = advanced_undo(beautified)

        embed = discord.Embed(title="WeAreDevs / Prometheus - Deobfuscado", color=EMERALD)
        embed.add_field(name="Resultado", value=f"```lua\n{undone[:1900]}\n```", inline=False)
        embed.add_field(name="Notas", value="Removido phase boundaries + anti-debug + loaders", inline=False)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

# Comandos existentes ($deob, $beautify, $undo, $reconstruct, $help) ya están en el código anterior

# Iniciar bot
bot.run(TOKEN)
