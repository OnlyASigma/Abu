import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime, timedelta
import asyncio

load_dotenv()

TOKEN = os.getenv("A")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
tree = bot.tree
guild = discord.Object(id=GUILD_ID)

punicoes_ativas = []

def get_text_channel_by_name(guild_obj: discord.Guild, name: str):
    return discord.utils.get(guild_obj.text_channels, name=name)

async def try_send(channel: discord.TextChannel, content=None, embed=None, file=None):
    try:
        msg = await channel.send(content=content, embed=embed, file=file)
        return True, msg, None
    except discord.Forbidden:
        return False, None, "Sem permissão para enviar mensagens neste canal."
    except discord.HTTPException as e:
        return False, None, f"Erro ao enviar mensagem: {e}"

@tree.command(name="ping", description="Mostra o ping do bot", guild=guild)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! 🏓 {round(bot.latency * 1000)}ms", ephemeral=True)

@tree.command(name="registro", description="Cria um registro de punição", guild=guild)
@app_commands.describe(
    staff="Staff responsável pela punição",
    player="Nick do player punido",
    motivo="Motivo da punição",
    tempo="Tempo da punição em minutos",
    provas_link="Link das provas (opcional)",
    provas_arquivo="Arquivo de prova (opcional)"
)
async def registro(
    interaction: discord.Interaction,
    staff: str,
    player: str,
    motivo: str,
    tempo: int,
    provas_link: str = None,
    provas_arquivo: discord.Attachment = None
):
    await interaction.response.defer(ephemeral=True)
    canal = get_text_channel_by_name(interaction.guild, "punições")
    if not canal:
        await interaction.followup.send("❌ Canal 'punições' não encontrado.", ephemeral=True)
        return

    embed = discord.Embed(title="📋 Punição Aplicada", color=discord.Color.red())
    embed.add_field(name="Responsável", value=staff, inline=False)
    embed.add_field(name="Player", value=player, inline=False)
    embed.add_field(name="Motivo", value=motivo, inline=False)
    embed.add_field(name="Tempo", value=f"{tempo} minutos", inline=False)

    file = None
    if provas_link:
        embed.add_field(name="Provas", value=provas_link, inline=False)
    elif provas_arquivo:
        file = await provas_arquivo.to_file()

    success, msg, err = await try_send(canal, embed=embed, file=file)
    if success:
        hora_final = datetime.utcnow() + timedelta(minutes=tempo)
        punicoes_ativas.append({
            "player": player,
            "canal_id": canal.id,
            "mensagem_id": msg.id,
            "hora_final": hora_final
        })
        await interaction.followup.send("✅ Registro enviado!", ephemeral=True)
    else:
        await interaction.followup.send(f"❌ Erro ao enviar registro: {err}", ephemeral=True)

async def monitorar_punicoes():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.utcnow()
        for punicao in punicoes_ativas[:]:
            if now >= punicao["hora_final"]:
                canal = bot.get_channel(punicao["canal_id"])
                try:
                    msg = await canal.fetch_message(punicao["mensagem_id"])
                    embed = msg.embeds[0]
                    embed.color = discord.Color.green()
                    embed.title += " (Expirada)"
                    await msg.edit(embed=embed)
                    punicoes_ativas.remove(punicao)
                except:
                    punicoes_ativas.remove(punicao)
        await asyncio.sleep(60)

@bot.event
async def on_ready():
    guild_obj = bot.get_guild(GUILD_ID)
    if guild_obj:
        await bot.tree.sync(guild=guild_obj)
    else:
        await bot.tree.sync()
    bot.loop.create_task(monitorar_punicoes())
    print(f"✅ Bot conectado como {bot.user}")

bot.run(TOKEN)
