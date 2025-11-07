import discord
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

synced = False

@bot.event
async def on_ready():
    global synced
    print(f"{bot.user} está online!")

    if not synced:
        await tree.sync(guild=discord.Object(id=GUILD_ID))
        synced = True

@tree.command(name="registro", description="Registrar uma punição", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    nick="Nick do jogador punido",
    motivo="Motivo da punição",
    punicao="Tempo ou tipo da punição (ex: 2d, 4h, 30m)",
    provas_link="Link das provas (opcional)",
    provas_arquivo="Upload de provas (opcional)"
)
async def registro(interaction: discord.Interaction, nick: str, motivo: str, punicao: str, provas_link: str = None, provas_arquivo: discord.Attachment = None):
    embed = discord.Embed(title="Registro de Punição", color=discord.Color.red())
    embed.add_field(name="Nick", value=nick, inline=True)
    embed.add_field(name="Motivo", value=motivo, inline=True)
    embed.add_field(name="Punição", value=punicao, inline=True)
    if provas_link:
        embed.add_field(name="Provas (link)", value=provas_link, inline=False)
    if provas_arquivo:
        embed.set_image(url=provas_arquivo.url)
    await interaction.response.send_message(embed=embed)

@tree.command(name="conferir", description="Conferir punições registradas", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nick="Nick do jogador")
async def conferir(interaction: discord.Interaction, nick: str):
    embed = discord.Embed(title="Consulta de Punições", color=discord.Color.blue())
    embed.add_field(name="Nick", value=nick, inline=True)
    embed.add_field(name="Status", value="Sem punições registradas", inline=True)
    await interaction.response.send_message(embed=embed)

@tree.command(name="anular", description="Anular uma punição registrada", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nick="Nick do jogador punido")
async def anular(interaction: discord.Interaction, nick: str):
    await interaction.response.send_message(f"Punição de {nick} anulada com sucesso.")

@tree.command(name="ajuda", description="Mostrar ajuda sobre os comandos", guild=discord.Object(id=GUILD_ID))
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Comandos disponíveis",
        description="Veja abaixo os comandos que você pode usar com o bot Sigma:",
        color=discord.Color.green()
    )
    embed.add_field(name="/registro", value="Registra uma punição com nick, motivo, tempo e provas.", inline=False)
    embed.add_field(name="/conferir", value="Consulta se um jogador tem punições registradas.", inline=False)
    embed.add_field(name="/anular", value="Remove uma punição registrada de um jogador.", inline=False)
    embed.add_field(name="/ping", value="Testa se o bot está online e respondendo.", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ping", description="Testa se o bot está respondendo", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

bot.run(TOKEN)
