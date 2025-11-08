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
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"{len(synced)} comandos sincronizados com o Discord.")
    except Exception as e:
        print(e)
    print(f"Bot online como {bot.user}")

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
    
    canal_punicoes = discord.utils.get(interaction.guild.text_channels, name="punições")
    if not canal_punicoes:
        await interaction.response.send_message("❌ Canal `punições` não encontrado!", ephemeral=True)
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
    
    await canal_punicoes.send(embed=embed)
    await interaction.response.send_message("✅ Punição registrada com sucesso!", ephemeral=True)

@tree.command(name="anular", description="Anular uma punição registrada", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(nick="Nick do jogador punido")
async def anular(interaction: discord.Interaction, nick: str):
    if not has_role(interaction, "Punições"):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return
    
    canal_punicoes = discord.utils.get(interaction.guild.text_channels, name="punições")
    if not canal_punicoes:
        await interaction.response.send_message("❌ Canal `punições` não encontrado!", ephemeral=True)
        return
    
    await canal_punicoes.send(f"⚠️ A punição de **{nick}** foi anulada.")
    await interaction.response.send_message("✅ Punição anulada com sucesso!", ephemeral=True)

@tree.command(name="resultado", description="Postar resultado da whitelist", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(texto="Mensagem do resultado")
async def resultado(interaction: discord.Interaction, texto: str):
    if not has_role(interaction, "Whitelist"):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return
    
    canal_edital = discord.utils.get(interaction.guild.text_channels, name="edital-staff")
    if not canal_edital:
        await interaction.response.send_message("❌ Canal `edital-staff` não encontrado!", ephemeral=True)
        return

    await canal_edital.send(f"📝 Resultado da Whitelist:\n{texto}")
    await interaction.response.send_message("✅ Resultado postado no canal **edital-staff**.", ephemeral=True)

@tree.command(name="postar_edital", description="Postar edital da whitelist", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(link="Link do formulário")
async def postar_edital(interaction: discord.Interaction, link: str):
    if not has_role(interaction, "Whitelist"):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return

    canal_edital = discord.utils.get(interaction.guild.text_channels, name="edital-staff")
    if canal_edital is None:
        await interaction.response.send_message("❌ Canal 'edital-staff' não encontrado.", ephemeral=True)
        return

    embed = discord.Embed(
        title="📢 Edital — Seleção da Equipe de Administração | Rio Roleplay",
        color=discord.Color.green(),
        description=(
            "O **Rio Roleplay** acaba de abrir seu **novo formulário para a equipe de administração**.\n"
            "As vagas agora são **ilimitadas** e o processo de seleção foi **reformulado**, tornando-se mais "
            "**criterioso, profissional e original**.\n\n"
            "Cada candidato será avaliado com atenção, considerando:\n"
            "- Perfil geral\n"
            "- Conhecimento técnico\n"
            "- Aplicação das regras\n"
            "- Ética e postura\n"
            "- Capacidade de análise\n\n"
            "📋 **Regras Importantes:**\n"
            "1️⃣ Solicitar o resultado acarretará na **anulação do formulário**.\n"
            "2️⃣ O uso de **Inteligência Artificial** resultará em **desclassificação imediata**.\n"
            "3️⃣ Os resultados serão divulgados **apenas após o encerramento das inscrições**.\n"
            "4️⃣ Utilize **apenas suas próprias palavras**; respostas copiadas não serão aceitas.\n\n"
            f"🔗 **Formulário:** {link}\n\n"
            "🎯 **Boa sorte a todos os candidatos!**"
        )
    )

    await canal_edital.send(embed=embed)
    await interaction.response.send_message("✅ Edital postado com sucesso no canal **edital-staff**.", ephemeral=True)

@tree.command(name="ping", description="Testa se o bot está respondendo", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

bot.run(TOKEN)
