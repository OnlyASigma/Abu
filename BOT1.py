import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import View, Select
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import re
import asyncio

load_dotenv()
TOKEN = os.getenv("A")

GUILD_ID = 1396593110506803260
EDITAL_CHANNEL_ID = 1435760584271335598
CANAL_REGISTRO_ID = 1396604035338862836
WHITELIST_IDS = [852244599321264202, 1386151968384221284]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
GUILD_OBJ = discord.Object(id=GUILD_ID)
processed_messages = set()

def calcular_tempo_faltando(data_registro, duracao_str):
    duracao = timedelta()
    for valor, unidade in re.findall(r"(\d+)([dhm])", duracao_str.lower()):
        if unidade == "d":
            duracao += timedelta(days=int(valor))
        elif unidade == "h":
            duracao += timedelta(hours=int(valor))
        elif unidade == "m":
            duracao += timedelta(minutes=int(valor))
    fim = data_registro + duracao
    restante = fim - datetime.now()
    return restante

async def verificar_registro_ativo(guild, nick):
    canal = guild.get_channel(CANAL_REGISTRO_ID)
    async for msg in canal.history(limit=200):
        if msg.id in processed_messages:
            continue
        if msg.embeds:
            embed = msg.embeds[0]
            if embed.title.startswith("Registro de Punição"):
                campos = {f.name: f.value for f in embed.fields}
                if campos.get("Nick do Player", "").lower() == nick.lower():
                    data_str = embed.footer.text.replace("Registrado em: ", "")
                    try:
                        data_registro = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
                        restante = calcular_tempo_faltando(data_registro, campos.get("Punição", ""))
                        if restante.total_seconds() > 0:
                            return True
                    except:
                        pass
    return False

@bot.tree.command(name="registro", description="Registrar uma punição", guild=GUILD_OBJ)
@app_commands.describe(
    nick="Nick do jogador punido",
    motivo="Motivo da punição",
    punicao="Tempo ou tipo da punição (ex: 2d, 4h, 30m)",
    provas_link="Link das provas (opcional)",
    provas_arquivo="Upload de provas (opcional)"
)
async def registro(interaction: discord.Interaction, nick: str, motivo: str, punicao: str,
                   provas_link: str = None, provas_arquivo: discord.Attachment = None):
    if await verificar_registro_ativo(interaction.guild, nick):
        await interaction.response.send_message(
            f"⚠️ Já existe uma punição ativa para **{nick}**.", ephemeral=True
        )
        return

    staff = interaction.user.mention
    canal = interaction.guild.get_channel(CANAL_REGISTRO_ID)
    if not canal:
        await interaction.response.send_message("Canal de registro não encontrado.", ephemeral=True)
        return

    embed = discord.Embed(title="Registro de Punição", color=discord.Color.green())
    embed.add_field(name="Staff", value=staff, inline=False)
    embed.add_field(name="Nick do Player", value=nick, inline=False)
    embed.add_field(name="Motivo", value=motivo, inline=False)
    embed.add_field(name="Punição", value=punicao, inline=False)

    if provas_arquivo:
        url = provas_arquivo.url
        nome = provas_arquivo.filename.lower()
        if nome.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            embed.set_image(url=url)
            embed.add_field(name="Provas (imagem)", value=f"[Clique aqui]({url})", inline=False)
        elif nome.endswith((".mp4", ".mov", ".webm")):
            embed.add_field(name="Provas (vídeo)", value=f"[Clique aqui]({url})", inline=False)
        else:
            embed.add_field(name="Provas (arquivo)", value=f"[Baixar]({url})", inline=False)
    elif provas_link:
        embed.add_field(name="Provas (link)", value=f"[Abrir link]({provas_link})", inline=False)
    else:
        embed.add_field(name="Provas", value="Nenhuma enviada.", inline=False)

    embed.set_footer(text=f"Registrado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    msg = await canal.send(embed=embed)
    processed_messages.add(msg.id)
    await interaction.response.send_message("✅ Registro de punição enviado.", ephemeral=True)

@tasks.loop(minutes=5)
async def verificar_punicoes():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    canal = guild.get_channel(CANAL_REGISTRO_ID)
    async for message in canal.history(limit=200):
        if message.id in processed_messages:
            continue
        if message.embeds:
            embed = message.embeds[0]
            if embed.title == "Registro de Punição":
                campos = {f.name: f.value for f in embed.fields}
                data_str = embed.footer.text.replace("Registrado em: ", "")
                try:
                    data_registro = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
                    restante = calcular_tempo_faltando(data_registro, campos.get("Punição", ""))
                    if restante.total_seconds() <= 0:
                        embed.title = "⏰ Punição Finalizada"
                        embed.color = discord.Color.red()
                        await message.edit(embed=embed)
                    processed_messages.add(message.id)
                except:
                    continue

@bot.event
async def on_ready():
    verificar_punicoes.start()
    await bot.tree.sync(guild=GUILD_OBJ)

bot.run(TOKEN)
