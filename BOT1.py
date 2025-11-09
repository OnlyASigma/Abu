import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("A")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
tree = bot.tree
guild = discord.Object(id=GUILD_ID)

def get_text_channel_by_name(guild_obj: discord.Guild, name: str):
    return discord.utils.get(guild_obj.text_channels, name=name)

async def try_send(channel: discord.TextChannel, content=None, embed=None, file=None):
    try:
        await channel.send(content=content, embed=embed, file=file)
        return True, None
    except discord.Forbidden:
        return False, "Sem permissão para enviar mensagens neste canal."
    except discord.HTTPException as e:
        return False, f"Erro ao enviar mensagem: {e}"

@tree.command(name="ping", description="Mostra o ping do bot", guild=guild)
async def ping(interaction: discord.Interaction):
    try:
        await interaction.response.send_message(f"Pong! 🏓 {round(bot.latency * 1000)}ms", ephemeral=True)
    except:
        pass

@tree.command(name="postar_edital", description="Posta o edital com o link do formulário", guild=guild)
@app_commands.describe(link="Link do formulário")
async def postar_edital(interaction: discord.Interaction, link: str):
    try:
        await interaction.response.defer(ephemeral=True)
        canal = get_text_channel_by_name(interaction.guild, "edital-staff")
        if not canal:
            await interaction.followup.send("❌ Canal 'edital-staff' não encontrado.", ephemeral=True)
            return
        texto = (
            "📢 **NOVO EDITAL ABERTO**\n\n"
            "O Rio Roleplay acaba de abrir seu novo formulário para a equipe de administração. "
            "As vagas agora são ilimitadas e o processo de seleção foi reformulado.\n\n"
            "**Regras:**\n"
            "1️⃣ Solicitar o resultado acarretará na anulação do formulário.\n"
            "2️⃣ O uso de Inteligência Artificial resultará em desclassificação imediata.\n"
            "3️⃣ Resultados serão divulgados após o encerramento das inscrições.\n"
            "4️⃣ Utilize apenas suas próprias palavras; respostas copiadas não serão aceitas.\n\n"
            f"📎 **Formulário:** {link}\n\n"
            "Boa sorte a todos! 🍀"
        )
        success, err = await try_send(canal, texto)
        if success:
            await interaction.followup.send("✅ Edital postado com sucesso!", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Falha ao postar o edital: {err}", ephemeral=True)
    except:
        pass

@tree.command(name="resultado", description="Posta o resultado do edital", guild=guild)
@app_commands.describe(aprovados="IDs dos aprovados separados por espaço", data="Data de lançamento")
async def resultado(interaction: discord.Interaction, aprovados: str, data: str):
    try:
        await interaction.response.defer(ephemeral=True)
        canal = get_text_channel_by_name(interaction.guild, "edital-staff")
        if not canal:
            await interaction.followup.send("❌ Canal 'edital-staff' não encontrado.", ephemeral=True)
            return
        ids = aprovados.split()
        mentions = "\n".join([f"<@{id_}> (ID: {id_})" for id_ in ids])
        embed = discord.Embed(title=f"📢 Resultado do Processo Seletivo — {data}", color=discord.Color.blue())
        embed.add_field(name="Aprovados", value=mentions if mentions else "Nenhum aprovado", inline=False)
        await canal.send(embed=embed)
        await interaction.followup.send("✅ Resultado enviado!", ephemeral=True)
    except:
        pass

@tree.command(name="registro", description="Cria um registro de punição", guild=guild)
@app_commands.describe(
    player="Nick do player punido",
    staff="Staff responsável pela punição",
    motivo="Motivo da punição",
    tempo="Tempo da punição em minutos",
    provas="Link ou arquivo de prova"
)
async def registro(
    interaction: discord.Interaction,
    player: str,
    staff: str,
    motivo: str,
    tempo: int,
    provas: str = None
):
    try:
        await interaction.response.defer(ephemeral=True)
        canal = get_text_channel_by_name(interaction.guild, "punições")
        if not canal:
            await interaction.followup.send("❌ Canal 'punições' não encontrado.", ephemeral=True)
            return

        embed = discord.Embed(title="📋 Nova Punição", color=discord.Color.red())
        embed.add_field(name="Player", value=player, inline=False)
        embed.add_field(name="Responsável", value=staff, inline=False)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        embed.add_field(name="Tempo", value=f"{tempo} minutos", inline=False)

        file = None
        if provas and provas.startswith("http"):
            embed.add_field(name="Provas", value=provas, inline=False)
        elif interaction.attachments:
            file = await interaction.attachments[0].to_file()

        success, err = await try_send(canal, embed=embed, file=file)
        if success:
            await interaction.followup.send("✅ Registro enviado!", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Erro ao enviar registro: {err}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Ocorreu um erro: {e}", ephemeral=True)

@tree.command(name="anular", description="Envia uma anulação no canal punições", guild=guild)
async def anular(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
        canal = get_text_channel_by_name(interaction.guild, "punições")
        if not canal:
            await interaction.followup.send("❌ Canal 'punições' não encontrado.", ephemeral=True)
            return
        success, err = await try_send(canal, "⚠️ Uma punição foi anulada.")
        if success:
            await interaction.followup.send("✅ Anulação enviada!", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Erro ao enviar anulação: {err}", ephemeral=True)
    except:
        pass

@tree.command(name="conferir", description="Conferir punição de um player", guild=guild)
@app_commands.describe(nick="Nick do player punido", staff="Staff responsável pela punição")
async def conferir(interaction: discord.Interaction, nick: str, staff: str = None):
    try:
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title="Consulta de Punição", color=discord.Color.orange())
        embed.add_field(name="Nick do Player", value=nick, inline=False)
        embed.add_field(name="Status", value="Punição registrada", inline=False)
        if staff:
            embed.add_field(name="Staff Responsável", value=staff, inline=False)
        await interaction.followup.send(embed=embed)
    except:
        pass

@bot.event
async def on_ready():
    try:
        guild_obj = bot.get_guild(GUILD_ID)
        if guild_obj:
            await bot.tree.sync(guild=guild_obj)
        else:
            await bot.tree.sync()
        print(f"✅ Bot conectado como {bot.user}")
    except:
        pass

bot.run(TOKEN)
