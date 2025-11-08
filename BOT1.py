import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("A")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
guild = discord.Object(id=GUILD_ID)

@tree.command(name="ping", description="Mostra o ping do bot", guild=guild)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! 🏓 {round(bot.latency * 1000)}ms")

@tree.command(name="postar_edital", description="Posta o edital com o link do formulário", guild=guild)
@app_commands.describe(link="Link do formulário")
async def postar_edital(interaction: discord.Interaction, link: str):
    canal = discord.utils.get(interaction.guild.text_channels, name="edital-staff")
    if not canal:
        await interaction.response.send_message("❌ Canal 'edital-staff' não encontrado.", ephemeral=True)
        return
    texto = (
        "📢 **NOVO EDITAL ABERTO**\n\n"
        "O Rio Roleplay acaba de abrir seu novo formulário para a equipe de administração. "
        "As vagas agora são ilimitadas e o processo de seleção foi reformulado, tornando-se mais criterioso, "
        "profissional e original. Cada candidato será avaliado com atenção, considerando o perfil geral, "
        "conhecimento técnico, aplicação das regras, ética, postura e capacidade de análise.\n\n"
        "**Regras:**\n"
        "1️⃣ Solicitar o resultado acarretará na anulação do formulário.\n"
        "2️⃣ O uso de Inteligência Artificial resultará em desclassificação imediata.\n"
        "3️⃣ Resultados serão divulgados após o encerramento das inscrições.\n"
        "4️⃣ Utilize apenas suas próprias palavras; respostas copiadas não serão aceitas.\n\n"
        f"📎 **Formulário:** {link}\n\n"
        "Boa sorte a todos! 🍀"
    )
    await canal.send(texto)
    await interaction.response.send_message("✅ Edital postado com sucesso!", ephemeral=True)

@tree.command(name="resultado", description="Envia o resultado no canal edital-staff", guild=guild)
async def resultado(interaction: discord.Interaction):
    canal = discord.utils.get(interaction.guild.text_channels, name="edital-staff")
    if canal:
        await canal.send("📢 **O resultado do processo seletivo foi publicado!**")
        await interaction.response.send_message("✅ Resultado enviado!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Canal 'edital-staff' não encontrado.", ephemeral=True)

@tree.command(name="registro", description="Envia um registro no canal punições", guild=guild)
async def registro(interaction: discord.Interaction):
    canal = discord.utils.get(interaction.guild.text_channels, name="punições")
    if canal:
        await canal.send("📋 Novo registro adicionado ao sistema de punições.")
        await interaction.response.send_message("✅ Registro enviado!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Canal 'punições' não encontrado.", ephemeral=True)

@tree.command(name="anular", description="Envia uma anulação no canal punições", guild=guild)
async def anular(interaction: discord.Interaction):
    canal = discord.utils.get(interaction.guild.text_channels, name="punições")
    if canal:
        await canal.send("⚠️ Uma punição foi anulada.")
        await interaction.response.send_message("✅ Anulação enviada!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Canal 'punições' não encontrado.", ephemeral=True)

@bot.event
async def on_ready():
    synced = await tree.sync(guild=guild)
    print(f"✅ {len(synced)} comandos sincronizados na guild {GUILD_ID}")
    print(f"Bot conectado como {bot.user}")

bot.run(TOKEN)
