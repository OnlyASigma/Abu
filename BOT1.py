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
STAFF_ROLE_ID = 1396599719454834849

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
GUILD_OBJ = discord.Object(id=GUILD_ID)
processed_messages = set()
synced = False

def calcular_tempo_faltando(data_registro, duracao_str):
    duracao = timedelta()
    for valor, unidade in re.findall(r"(\d+)([dhms])", duracao_str.lower()):
        if unidade == "d":
            duracao += timedelta(days=int(valor))
        elif unidade == "h":
            duracao += timedelta(hours=int(valor))
        elif unidade == "m":
            duracao += timedelta(minutes=int(valor))
        elif unidade == "s":
            duracao += timedelta(seconds=int(valor))
    fim = data_registro + duracao
    agora = datetime.now()
    restante = fim - agora
    return restante

async def verificar_registro_ativo(guild, nick):
    canal = guild.get_channel(CANAL_REGISTRO_ID)
    print(f"🔍 Verificando registros ativos para: {nick}")
    async for msg in canal.history(limit=200):
        if msg.embeds:
            embed = msg.embeds[0]
            print(f"📦 Embed encontrado: {embed.title}")
            if embed.title.startswith("Registro de Punição"):
                campos = {f.name: f.value for f in embed.fields}
                print(f"📋 Campos do embed: {campos}")
                nick_registrado = campos.get("Nick do Player", "").strip().lower()
                if nick_registrado == nick.strip().lower():
                    data_str = embed.footer.text.replace("Registrado em: ", "")
                    print(f"🕒 Data do registro: {data_str}")
                    try:
                        data_registro = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
                        restante = calcular_tempo_faltando(data_registro, campos.get("Punição", ""))
                        print(f"⏳ Tempo restante: {restante}")
                        if restante.total_seconds() > 0:
                            print("⚠️ Punição ainda ativa.")
                            return True
                    except Exception as e:
                        print(f"❌ Erro ao processar registro: {e}")
    print("✅ Nenhuma punição ativa encontrada.")
    return False

@bot.tree.command(name="registro", description="Registrar uma punição", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    nick="Nick do jogador punido",
    motivo="Motivo da punição",
    punicao="Tempo ou tipo da punição (ex: 2d, 4h, 30m, 10s)",
    provas_link="Link das provas (opcional)",
    provas_arquivo="Upload de provas (opcional)"
)
async def registro(interaction: discord.Interaction, nick: str, motivo: str, punicao: str, provas_link: str = None, provas_arquivo: discord.Attachment = None):
    if await verificar_registro_ativo(interaction.guild, nick):
        if not interaction.response.is_done():
            await interaction.response.send_message(f"⚠️ Já existe uma punição ativa para **{nick}**.", ephemeral=True)
        return

    staff = interaction.user.mention
    canal = interaction.guild.get_channel(CANAL_REGISTRO_ID)
    if not canal:
        if not interaction.response.is_done():
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
            embed.add_field(name="Provas (arquivo)", value=f"[Baixar arquivo]({url})", inline=False)
    elif provas_link:
        embed.add_field(name="Provas (link)", value=f"[Abrir link]({provas_link})", inline=False)
    else:
        embed.add_field(name="Provas", value="Nenhuma enviada.", inline=False)

    embed.set_footer(text=f"Registrado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    await canal.send(embed=embed)
    if not interaction.response.is_done():
        await interaction.response.send_message("✅ Registro de punição enviado com sucesso.", ephemeral=True)

@bot.tree.command(name="anular", description="Anula um registro de punição por nick", guild=discord.Object(id=GUILD_ID))
async def anular(interaction: discord.Interaction, nick: str):
    if interaction.user.id not in WHITELIST_IDS:
        await interaction.response.send_message("Sem permissão.", ephemeral=True)
        return
    canal = interaction.guild.get_channel(CANAL_REGISTRO_ID)
    async for message in canal.history(limit=200):
        if message.embeds:
            embed = message.embeds[0]
            if embed.title == "Registro de Punição":
                campos = {f.name: f.value for f in embed.fields}
                if campos.get("Nick do Player", "").lower() == nick.lower():
                    embed.color = discord.Color.red()
                    embed.title = "❌ Registro de Punição Anulado"
                    embed.add_field(name="Anulado por", value=interaction.user.mention, inline=False)
                    await message.edit(embed=embed)
                    await interaction.response.send_message(f"O registro de `{nick}` foi anulado.", ephemeral=True)
                    return
    await interaction.response.send_message("Nenhum registro encontrado com esse nick.", ephemeral=True)

@bot.tree.command(name="resultados", description="Anunciar aprovados da staff", guild=discord.Object(id=GUILD_ID))
async def resultados(interaction: discord.Interaction, ids: str):
    if interaction.user.id not in WHITELIST_IDS:
        await interaction.response.send_message("Sem permissão.", ephemeral=True)
        return
    canal = interaction.guild.get_channel(EDITAL_CHANNEL_ID)
    if not canal:
        await interaction.response.send_message("Canal não encontrado.", ephemeral=True)
        return
    id_list = ids.split()
    mencoes = []
    for user_id in id_list:
        try:
            mencoes.append(f"<@{int(user_id)}>")
        except:
            mencoes.append(f"`ID inválido: {user_id}`")
    embed = discord.Embed(title="Resultado do Formulário da Staff", color=discord.Color.green())
    embed.add_field(name="✅ Aprovados", value="\n".join(mencoes), inline=False)
    embed.set_footer(text=f"Anunciado por {interaction.user.display_name}")
    await canal.send(embed=embed)
    if not interaction.response.is_done():
        await interaction.response.send_message("Resultados enviados.", ephemeral=True)

@bot.tree.command(name="postar_edital", description="Postar o edital da staff", guild=discord.Object(id=GUILD_ID))
async def postar_edital(interaction: discord.Interaction, link: str):
    if interaction.user.id not in WHITELIST_IDS:
        await interaction.response.send_message("Sem permissão.", ephemeral=True)
        return
    canal = interaction.guild.get_channel(EDITAL_CHANNEL_ID)
    texto = (
        "Olá jogadores!\n\n"
        "O Rio Roleplay acaba de abrir um formulário para adentrar na staff! "
        "Aos que prestarem serão avaliados em: perfil geral, conhecimento técnico, aplicação das regras, ética, postura e capacidade de análise!\n"
        "Mas antes aqui vão algumas regras do formulário:\n"
        "1.1 - Solicitar o resultado antes do prazo acarretará na anulação do formulário.\n"
        "1.2 - O uso de Inteligência Artificial, independentemente do motivo, resultará em desclassificação imediata.\n"
        "1.3 - Os resultados serão divulgados apenas após o encerramento das inscrições.\n"
        "1.4 - Utilize apenas suas próprias palavras; respostas copiadas não serão aceitas.\n\n"
        f"Formulário: {link}"
    )
    await canal.send(texto)
    if not interaction.response.is_done():
        await interaction.response.send_message("Edital postado com sucesso.", ephemeral=True)

@bot.tree.command(name="conferir", description="Verifica punições por nick", guild=discord.Object(id=GUILD_ID))
async def conferir(interaction: discord.Interaction, nick: str):
    canal = interaction.guild.get_channel(CANAL_REGISTRO_ID)
    if not canal:
        await interaction.response.send_message("Canal de registro não encontrado.", ephemeral=True)
        return
            async for message in canal.history(limit=100):
        if message.embeds:
            embed = message.embeds[0]
            if embed.title.startswith("Registro de Punição"):
                campos = {field.name: field.value for field in embed.fields}
                nick_registrado = campos.get("Nick do Player", "").lower()
                if nick_registrado == nick.lower():
                    data_str = embed.footer.text.replace("Registrado em: ", "")
                    try:
                        data_registro = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
                        duracao = campos.get("Punição", "")
                        restante = calcular_tempo_faltando(data_registro, duracao)
                        if restante.total_seconds() <= 0:
                            restante_str = "Punição finalizada."
                        else:
                            horas, resto = divmod(int(restante.total_seconds()), 3600)
                            minutos = resto // 60
                            restante_str = f"Faltam {horas}h {minutos}m."
                        resposta = (
                            f"**Staff:** {campos.get('Staff')}\n"
                            f"**Motivo:** {campos.get('Motivo')}\n"
                            f"**Punição:** {duracao}\n"
                            f"**Tempo restante:** {restante_str}"
                        )
                        if not interaction.response.is_done():
                            await interaction.response.send_message(resposta, ephemeral=True)
                        return
                    except:
                        if not interaction.response.is_done():
                            await interaction.response.send_message("Erro ao calcular tempo restante.", ephemeral=True)
                        return
    if not interaction.response.is_done():
        await interaction.response.send_message("Nenhum registro encontrado com esse nick.", ephemeral=True)

@bot.tree.command(name="perguntar", description="Abrir perguntas frequentes", guild=discord.Object(id=GUILD_ID))
async def perguntar(interaction: discord.Interaction):
    perguntas = {
        "Como faço para entrar em uma FAC?": "Você pode realizar um formulário ou um recrutamento no canal de #recrutamento-fac",
        "Como viro staff?": "Os formulários de staff são abertos em períodos específicos. Fique atento aos anúncios no canal de editais.",
        "Posso ser desbanido?": "Depende da situação. Solicite uma revisão de banimento explicando o motivo no canal de suporte.",
        "Como virar Policial??": "Vá no servidor da corp desejada ou veja #edital-policial.",
        "O que é o RIO RP?": "RIO RP é um servidor de roleplay no Roblox inspirado na cidade do Rio de Janeiro, com foco em realismo e imersão.",
        "Como trabalho com os empregos da prefeitura?": "1°: Vá na prefeitura / 2°: Depois pegue o emprego com o XP requerido e clique em Teleportar"
    }
    options = [discord.SelectOption(label=p, description="Clique para ver a resposta") for p in perguntas]
    select = Select(placeholder="Escolha uma pergunta...", options=options)

    async def select_callback(interaction_select: discord.Interaction):
        await interaction_select.response.send_message(perguntas[select.values[0]], ephemeral=True)

    select.callback = select_callback
    view = View()
    view.add_item(select)
    await interaction.response.send_message("Escolha uma pergunta abaixo:", view=view, ephemeral=True)

@tasks.loop(minutes=5)
async def verificar_punicoes():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    canal = guild.get_channel(CANAL_REGISTRO_ID)
    async for message in canal.history(limit=200):
        if message.id in processed_messages:
            continue
        processed_messages.add(message.id)
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
                except:
                    continue

@bot.event
async def on_ready():
    global synced
    print(f"{bot.user} está online!")

    if not verificar_punicoes.is_running():
        verificar_punicoes.start()

    if not synced:
        bot.tree.clear_commands(guild=discord.Object(id=GUILD_ID))
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        synced = True

bot.run(TOKEN)
