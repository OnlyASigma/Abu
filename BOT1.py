import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("A")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
tree = bot.tree
guild = discord.Object(id=GUILD_ID)


def get_text_channel_by_name(guild_obj: discord.Guild, name: str) -> discord.TextChannel | None:
    return discord.utils.get(guild_obj.text_channels, name=name)


async def try_send(channel: discord.TextChannel, content: str):
    try:
        await channel.send(content)
        return True, None
    except discord.Forbidden:
        return False, "O bot não tem permissão para enviar mensagens neste canal."
    except discord.HTTPException as e:
        return False, f"Falha ao enviar mensagem: {e}"


@tree.command(name="ping", description="Mostra o ping do bot", guild=guild)
async def ping(interaction: discord.Interaction):
    latency_ms = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! 🏓 {latency_ms}ms", ephemeral=True)


@tree.command(name="postar_edital", description="Posta o edital com o link do formulário", guild=guild)
@app_commands.describe(link="Link do formulário")
async def postar_edital(interaction: discord.Interaction, link: str):
    await interaction.response.defer(ephemeral=True)
    canal = get_text_channel_by_name(interaction.guild, "edital-staff")
    if not canal:
        await interaction.followup.send("❌ Canal 'edital-staff' não encontrado.", ephemeral=True)
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

    success, err = await try_send(canal, texto)
    if success:
        await interaction.followup.send("✅ Edital postado com sucesso!", ephemeral=True)
    else:
        await interaction.followup.send(f"❌ Não foi possível postar o edital: {err}", ephemeral=True)


@tree.command(name="resultado", description="Envia o resultado no canal edital-staff", guild=guild)
async def resultado(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    canal = get_text_channel_by_name(interaction.guild, "edital-staff")
    if canal:
        success, err = await try_send(canal, "📢 **O resultado do processo seletivo foi publicado!**")
        if success:
            await interaction.followup.send("✅ Resultado enviado!", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Não foi possível enviar o resultado: {err}", ephemeral=True)
    else:
        await interaction.followup.send("❌ Canal 'edital-staff' não encontrado.", ephemeral=True)


@tree.command(name="registro", description="Envia um registro no canal punições", guild=guild)
async def registro(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    canal = get_text_channel_by_name(interaction.guild, "punições")
    if canal:
        success, err = await try_send(canal, "📋 Novo registro adicionado ao sistema de punições.")
        if success:
            await interaction.followup.send("✅ Registro enviado!", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Não foi possível enviar o registro: {err}", ephemeral=True)
    else:
        await interaction.followup.send("❌ Canal 'punições' não encontrado.", ephemeral=True)


@tree.command(name="anular", description="Envia uma anulação no canal punições", guild=guild)
async def anular(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    canal = get_text_channel_by_name(interaction.guild, "punições")
    if canal:
        success, err = await try_send(canal, "⚠️ Uma punição foi anulada.")
        if success:
            await interaction.followup.send("✅ Anulação enviada!", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Não foi possível enviar a anulação: {err}", ephemeral=True)
    else:
        await interaction.followup.send("❌ Canal 'punições' não encontrado.", ephemeral=True)


@bot.event
async def on_ready():
    await bot.tree.clear_commands(guild=guild)
    await bot.tree.sync(guild=guild)


if __name__ == "__main__":
    bot.run(TOKEN)
