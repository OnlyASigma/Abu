import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Bot online como {bot.user}")

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} comandos sincronizados com o Discord.")
    except Exception as e:
        print(e)

def has_role(interaction, role_name):
    return discord.utils.get(interaction.user.roles, name=role_name) is not None

@tree.command(name="registro", description="Registrar uma punição", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    nick="Nick do jogador punido",
    motivo="Motivo da punição",
    punicao="Tempo ou tipo da punição (ex: 2d, 4h, 30m)",
    provas_link="Link das provas (opcional)",
    provas_arquivo="Upload de provas (opcional)"
)
async def registro(interaction: discord.Interaction, nick: str, motivo: str, punicao: str, provas_link: str = None, provas_arquivo: discord.Attachment = None):
    if not has_role(interaction, "Punições"):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return
    embed = discord.Embed(title="Registro de Punição", color=discord.Color.red())
    embed.add_field(name="Nick", value=nick, inline=True)
    embed.add_field(name="Motivo", value=motivo, inline=True)
    embed.add_field(name="Punição", value=punicao, inline=True)
    if provas_link:
        embed.add_field(name="Provas (link)", value=provas_link, inline=False)
    elif provas_arquivo:
        embed.add_field(name="Provas (arquivo)", value=provas_arquivo.url, inline=False)
    else:
        embed.add_field(name="Provas", value="Nenhuma enviada.", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="resultado", description="Postar resultado da whitelist", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(texto="Mensagem do resultado")
async def resultado(interaction: discord.Interaction, texto: str):
    if not has_role(interaction, "Whitelist"):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return
    await interaction.response.send_message(f"📝 Resultado: {texto}")

@tree.command(name="postar_edital", description="Postar edital da whitelist", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(texto="Conteúdo do edital")
async def postar_edital(interaction: discord.Interaction, texto: str):
    if not has_role(interaction, "Whitelist"):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return
    await interaction.response.send_message(f"📜 Edital: {texto}")

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
    embed.add_field(name="/registro", value="Registra uma punição (cargo Punições).", inline=False)
    embed.add_field(name="/conferir", value="Consulta se um jogador tem punições registradas.", inline=False)
    embed.add_field(name="/anular", value="Remove uma punição registrada.", inline=False)
    embed.add_field(name="/resultado", value="Posta resultado da whitelist (cargo Whitelist).", inline=False)
    embed.add_field(name="/postar_edital", value="Posta o edital da whitelist (cargo Whitelist).", inline=False)
    embed.add_field(name="/ping", value="Testa se o bot está online e respondendo.", inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ping", description="Testa se o bot está respondendo", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

bot.run(TOKEN)
