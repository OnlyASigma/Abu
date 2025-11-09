import os
from pathlib import Path
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import logging

logging.getLogger("discord").setLevel(logging.CRITICAL)
logging.getLogger("discord.http").setLevel(logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)

dotenv_path = Path("./.env")
load_dotenv(dotenv_path=dotenv_path)

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID_STR = os.getenv("GUILD_ID")

if TOKEN is None:
    raise ValueError("DISCORD_TOKEN não encontrado no .env")

if GUILD_ID_STR is None:
    raise ValueError("GUILD_ID não encontrado no .env")

GUILD_ID = int(GUILD_ID_STR)
guild = discord.Object(id=GUILD_ID)

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
tree = bot.tree

punicoes = {}

def get_text_channel_by_name(guild_obj: discord.Guild, name: str) -> discord.TextChannel | None:
    return discord.utils.get(guild_obj.text_channels, name=name)

def has_role(interaction: discord.Interaction, roles_allowed: list):
    for role_name in roles_allowed:
        if discord.utils.get(interaction.user.roles, name=role_name):
            return True
    return False

async def try_send(channel: discord.TextChannel, content=None, embed=None, files=None):
    try:
        await channel.send(content=content, embed=embed, files=files)
        return True, None
    except:
        return False, "Falha ao enviar mensagem."

@tree.command(name="ping", description="Mostra o ping do bot", guild=guild)
async def ping(interaction: discord.Interaction):
    latency_ms = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! 🏓 {latency_ms}ms", ephemeral=True)

@tree.command(name="postar_edital", description="Posta o edital com o link do formulário", guild=guild)
@app_commands.describe(link="Link do formulário")
async def postar_edital(interaction: discord.Interaction, link: str):
    if not has_role(interaction, ["Lead Admin"]):
        await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    canal = get_text_channel_by_name(interaction.guild, "edital-staff")
    if canal:
        texto = f"📢 **NOVO EDITAL ABERTO**\n📎 Formulário: {link}"
        await try_send(canal, content=texto)
    await interaction.followup.send("✅ Edital postado!", ephemeral=True)

@tree.command(name="resultado", description="Envia resultado no canal edital-staff", guild=guild)
@app_commands.describe(ids="IDs dos aprovados separados por espaço")
async def resultado(interaction: discord.Interaction, ids: str):
    if not has_role(interaction, ["Lead Admin"]):
        await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    canal = get_text_channel_by_name(interaction.guild, "edital-staff")
    if canal:
        menções = " ".join(f"<@{user_id}>" for user_id in ids.split())
        embed = discord.Embed(title="📢 Resultado do Processo Seletivo", color=discord.Color.green())
        embed.add_field(name="Aprovados", value=menções if menções else "Nenhum ID fornecido", inline=False)
        await try_send(canal, embed=embed)
    await interaction.followup.send("✅ Resultado enviado!", ephemeral=True)

@tree.command(name="registro", description="Registra punição no canal punições", guild=guild)
@app_commands.describe(staff="Staff responsável", nick="Nick do player", motivo="Motivo", tempo="Tempo da punição", provas="Links das provas", arquivo="Arquivo (imagem ou vídeo)")
async def registro(interaction: discord.Interaction, staff: str, nick: str, motivo: str, tempo: str, provas: str, arquivo: discord.Attachment = None):
    if not has_role(interaction, ["Lead Admin", "Staff"]):
        await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    canal = get_text_channel_by_name(interaction.guild, "punições")
    if not canal:
        await interaction.followup.send("❌ Canal 'punições' não encontrado.", ephemeral=True)
        return
    tempo_formatado = f"{tempo} minutos" if tempo.isdigit() else tempo
    embed = discord.Embed(title="📋 Novo Registro de Punição", color=discord.Color.green())
    embed.add_field(name="Staff Responsável", value=staff, inline=False)
    embed.add_field(name="Nick do Player", value=nick, inline=False)
    embed.add_field(name="Motivo", value=motivo, inline=False)
    embed.add_field(name="Tempo", value=tempo_formatado, inline=False)
    embed.add_field(name="Provas", value=provas, inline=False)
    files = []
    if arquivo:
        if arquivo.content_type.startswith("image/"):
            files.append(await arquivo.to_file())
        elif arquivo.content_type.startswith("video/"):
            video_file = await arquivo.to_file()
        else:
            await interaction.followup.send("❌ Apenas imagem ou vídeo.", ephemeral=True)
            return
    punicoes[nick.lower()] = embed
    if arquivo and arquivo.content_type.startswith("video/"):
        await try_send(canal, embed=embed)
        await try_send(canal, files=[video_file])
    else:
        await try_send(canal, embed=embed, files=files)
    await interaction.followup.send("✅ Registro enviado!", ephemeral=True)

@tree.command(name="anular", description="Anula punição no canal punições", guild=guild)
@app_commands.describe(staff="Staff responsável", motivo="Motivo", nick="Nick do player punido")
async def anular(interaction: discord.Interaction, staff: str, motivo: str, nick: str):
    if not has_role(interaction, ["Lead Admin"]):
        await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    canal = get_text_channel_by_name(interaction.guild, "punições")
    if canal:
        embed = discord.Embed(title="⚠️ Punição Anulada", color=discord.Color.orange())
        embed.add_field(name="Staff Responsável", value=staff, inline=False)
        embed.add_field(name="Motivo da Anulação", value=motivo, inline=False)
        embed.add_field(name="Nick do Player", value=nick, inline=False)
        punicoes.pop(nick.lower(), None)
        await try_send(canal, embed=embed)
    await interaction.followup.send("✅ Anulação enviada!", ephemeral=True)

@tree.command(name="conferir", description="Confere punição pelo nick", guild=guild)
@app_commands.describe(nick="Nick do player punido")
async def conferir(interaction: discord.Interaction, nick: str):
    await interaction.response.defer(ephemeral=True)
    embed = punicoes.get(nick.lower())
    if embed:
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send("❌ Nenhuma punição encontrada.", ephemeral=True)

@bot.event
async def on_ready():
    guild_obj = bot.get_guild(GUILD_ID)
    if guild_obj:
        await tree.sync(guild=guild_obj)

if __name__ == "__main__":
    bot.run(TOKEN)
