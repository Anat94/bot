import sqlite3
import discord
from discord.ext import commands, tasks
import asyncio
import youtube_dl
import random
import os
from functools import wraps


TOKEN = os.environ["TOKEN"]
PREFIX = '!'
MESSAGE = 'Message à mettre ✅ 💯 🇨🇵 😉 😱 😍 ❌ 😜 🍀 '  # dans l'ordre :white_check_mark: :100:  :flag_mf:  :wink::scream::heart_eyes::x::stuck_out_tongue_winking_eye::four_leaf_clover:


intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


conn = sqlite3.connect("my_config.sq3")
cur = conn.cursor()

try:
    cur.execute("CREATE TABLE guilds (guild INTEGER, chann_bienvenue INTEGER, chann_log INTEGER, role_perm INTEGER)")
except sqlite3.OperationalError:
    pass


def has_perm_role(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = args[0]

        cur.execute(f"SELECT role_perm FROM guilds WHERE guild = {ctx.guild.id}")
        role = cur.fetchone()[0]
        roles = [r.id for r in ctx.author.roles]

        if role in roles:
            return await func(*args, **kwargs)
        else:
            await ctx.send("Vous n'avez pas les perms !")

    return wrapper

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Vous n'avez pas les perms !")

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    changeStatus.start()
    print("Bot is ready")


@bot.event
async def on_member_join(member):
    cur.execute(f"SELECT chann_bienvenue FROM guilds WHERE guild = {member.guild.id}")
    channel = cur.fetchone()[0]

    try:
        embed = discord.Embed(
            title=f'{member.name} a rejoint le serveur !',
            colour=discord.Colour.green()
        )
        channel = int(channel)
        await bot.get_channel(channel).send(embed=embed)

    except:
        pass


@bot.command()
async def send_mp(ctx):
    all_members = ctx.guild.members
    for member in all_members:
        if not member.bot and member.id != 433547967140462592:
            await member.send(MESSAGE)


@bot.command()
@has_perm_role
async def clear(ctx, nb=20):
    if int(nb) > 20:
        nb = 20
    await ctx.channel.purge(limit=nb)

    embed = discord.Embed(
        title=f'{nb} messages ont été supprimés',
        colour=discord.Colour.green()
    )
    await ctx.send(embed=embed)


@bot.command()
@has_perm_role
async def kick(ctx, member: discord.Member, *reason):
    embed = discord.Embed(
        title=f"{member.name} a été expulsé par {ctx.message.author.name} : {' '.join(i for i in reason) if reason else 'aucune raison spécifiée'}",
        colour=discord.Colour.red()
    )
    await ctx.send(embed=embed)

    embed = discord.Embed(
        title=f"Vous avez été expulsé par {ctx.message.author.name} : {' '.join(i for i in reason) if reason else 'aucune raison spécifiée'}",
        colour=discord.Colour.red()
    )

    await member.send(embed=embed)

    await ctx.guild.kick(member)


@bot.command()
@has_perm_role
async def ban(ctx, member: discord.Member, *reason):
    embed = discord.Embed(
        title=f"{member.name} a été banni par {ctx.message.author.name} : {' '.join(i for i in reason) if reason else 'aucune raison spécifiée'}",
        colour=discord.Colour.red()
    )
    await ctx.send(embed=embed)

    embed = discord.Embed(
        title=f"Vous avez été banni par {ctx.message.author.name} : {' '.join(i for i in reason) if reason else 'aucune raison spécifiée'}",
        colour=discord.Colour.red()
    )

    await member.send(embed=embed)

    await ctx.guild.ban(member, delete_message_days=0)


@bot.command()
@has_perm_role
async def unban(ctx, user, *reason):
    reason = " ".join(reason)
    userName, userId = user.split("#")
    bannedUsers = await ctx.guild.bans()
    for i in bannedUsers:
        if i.user.name == userName and i.user.discriminator == userId:
            await ctx.guild.unban(i.user, reason=reason)
            await ctx.send(f"{user} à été unban.")
            return
    await ctx.send(f"L'utilisateur {user} n'est pas dans la liste des bans")


@bot.command()
@has_perm_role
async def banId(ctx):
    ids = []
    bans = await ctx.guild.bans()
    for i in bans:
        ids.append(str(i.user.id))
    await ctx.send("La liste des id des utilisateurs bannis du serveur est :")
    await ctx.send("\n".join(ids))


async def createMutedRole(ctx):
    mutedRole = await ctx.guild.create_role(name="Muted",
                                            permissions=discord.Permissions(
                                                send_messages=False,
                                                speak=False),
                                            reason="Creation du role Muted pour mute des gens.")
    for channel in ctx.guild.channels:
        await channel.set_permissions(mutedRole, send_messages=False, speak=False)
    return mutedRole


async def getMutedRole(ctx):
    roles = ctx.guild.roles
    for role in roles:
        if role.name == "Muted":
            return role

    return await createMutedRole(ctx)


@bot.command()
@has_perm_role
async def mute(ctx, member: discord.Member, *, reason="Aucune raison n'a été renseigné"):
    mutedRole = await getMutedRole(ctx)
    await member.add_roles(mutedRole, reason=reason)
    await ctx.send(f"{member.mention} a été mute !")


@bot.command()
@has_perm_role
async def unmute(ctx, member: discord.Member, *, reason="Aucune raison n'a été renseigné"):
    mutedRole = await getMutedRole(ctx)
    await member.remove_roles(mutedRole, reason=reason)
    await ctx.send(f"{member.mention} a été unmute !")


@bot.command()
async def serveur_info(ctx):
    server = ctx.guild
    numberOfTextChannels = len(server.text_channels)
    numberOfVoiceChannels = len(server.voice_channels)
    serverDescription = server.description
    numberOfPerson = server.member_count
    serverName = server.name
    message = f"Le serveur **{serverName}** contient *{numberOfPerson}* personnes ! \nLa description du serveur est {serverDescription}. \nCe serveur possède {numberOfTextChannels} salons écrit et {numberOfVoiceChannels} salon vocaux."
    await ctx.send(message)


# await ctx.message.delete() pour supprimer

@bot.command()
@has_perm_role
async def Tirage_au_sort(ctx):
    await ctx.send("Le tirage commencera dans 10 secondes. Envoyez \"moi\" dans ce channel pour y participer.")

    players = []

    def check(message):
        return message.channel == ctx.message.channel and message.author not in players and message.content == "moi"

    try:
        while True:
            participation = await bot.wait_for('message', timeout=10, check=check)
            players.append(participation.author)
            print("Nouveau participant : ")
            print(participation)
            await ctx.send(f"**{participation.author.name}** participe au tirage ! Le tirage commence dans 10 secondes")
    except:  # Timeout
        print("Demarrage du tirrage")

    gagner = ["voiture"]

    await ctx.send("Le tirage va commencer dans 3...")
    await asyncio.sleep(1)
    await ctx.send("2")
    await asyncio.sleep(1)
    await ctx.send("1")
    await asyncio.sleep(1)
    winner = random.choice(players)
    price = random.choice(gagner)
    await ctx.send(f"La personne qui a gagnée une {price} est...")
    await asyncio.sleep(1)
    await ctx.send("**" + winner.name + "**" + " !")


@bot.command()
@has_perm_role
async def say(ctx, number, *texte):
    for i in range(int(number)):
        await ctx.send(" ".join(texte))


@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title=f"Descriptifs des commandes",
        description=f"ban -> bannir une personne \nunban -> débannir une personne\nbanId -> pour voir la liste des ban\nkick -> kick une personne,\nmute -> mute une personne\nunmute -> démute une personne\nclear x -> pour supprimer x messages\nserveur_info -> avoir toutes les infos sur le serveur\nsay x -> pour envoyer x fois une phrase\nsend_mp-> envoyer un message a tous les membres du serveur",
        colour=0x00FF00
    )
    await ctx.send(embed=embed)
    embed1 = discord.Embed(
        title=f"Descriptifs des commandes musicales",
        description=f"play -> jouer une vidéo\npause -> mettre une musique en pause\nresume -> reprendre la musique\nleave -> le bot quitte le vocal\nskip ->passage a la chanson suivante ",
        color=0x00FF00
    )
    await ctx.send(embed=embed1)


# ------------------------------------------------------------------------------------ERREURE-----------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------LOG-----------------------------------------------------------------------------------------------
@bot.event
async def on_message_delete(message):
    cur.execute(f"SELECT chann_log FROM guilds WHERE guild = {message.guild.id}")
    channel = cur.fetchone()[0]

    try:
        channel = int(channel)

        embed = discord.Embed(
            title=f"Le message de {message.author} a été supprimé \n> {message.content}",
            coulor=discord.Colour.blue()
        )
        await bot.get_channel(channel).send(embed=embed)

    except:
        pass


@bot.event
async def on_message_edit(before, after):
    embed = discord.Embed(
        title=f"{before.author} a édité son message :\nAvant -> {before.content}\nAprès -> {after.content}",
        colour=discord.Colour.blue()
    )


@bot.event
async def on_reaction_add(reaction, user):
    await reaction.message.add_reaction(reaction.emoji)


# ------------------------------------------------------------------------------------STATUS-----------------------------------------------------------------------------------------------
status = ["!help",
          " A proxima roleplay",
          "A votre service"]


# @bot.command()
# async def start(ctx, secondes = 5):
#	changeStatus.change_interval(seconds = secondes)

@tasks.loop(seconds=5)
async def changeStatus():
    game = discord.Game(random.choice(status))
    await bot.change_presence(status=discord.Status.dnd, activity=game)


# ------------------------------------------------------------------------------------LIRE MUSIQUE-----------------------------------------------------------------------------------------------
musics = {}
ytdl = youtube_dl.YoutubeDL()


class Video:
    def __init__(self, link):
        video = ytdl.extract_info(link, download=False)
        video_format = video["formats"][0]
        self.url = video["webpage_url"]
        self.stream_url = video_format["url"]


@bot.command()
async def leave(ctx):
    client = ctx.guild.voice_client
    await client.disconnect()
    musics[ctx.guild] = []


@bot.command()
async def resume(ctx):
    client = ctx.guild.voice_client
    if client.is_paused():
        client.resume()


@bot.command()
async def pause(ctx):
    client = ctx.guild.voice_client
    if not client.is_paused():
        client.pause()


@bot.command()
async def skip(ctx):
    client = ctx.guild.voice_client
    client.stop()


def play_song(client, queue, song):
    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song.stream_url
                                                                 ,
                                                                 before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"))

    def next(_):
        if len(queue) > 0:
            new_song = queue[0]
            del queue[0]
            play_song(client, queue, new_song)
        else:
            asyncio.run_coroutine_threadsafe(client.disconnect(), bot.loop)

    client.play(source, after=next)


@bot.command()
async def play(ctx, url):
    print("play")
    client = ctx.guild.voice_client

    if client and client.channel:
        video = Video(url)
        musics[ctx.guild].append(video)
    else:
        channel = ctx.author.voice.channel
        video = Video(url)
        musics[ctx.guild] = []
        client = await channel.connect()
        await ctx.send(f"Je lance : {video.url}")
        play_song(client, musics[ctx.guild], video)

#-------------------------------------------------------------------------------CONFIG BDD/BOT------------------------------------------------------------------------------------
@commands.has_permissions(administrator=True)
@bot.command()
async def set_guild(ctx):
    cur.execute(f"INSERT INTO guilds(guild) VALUES({ctx.guild.id})")
    conn.commit()
    embed = discord.Embed(
        title=f"Le serveur a bien été ajouté a la base de donnée",
        colour=0x00FF00
    )
    await ctx.send(embed=embed)

@bot.command()
@has_perm_role
async def channel_bienvenue(ctx, channel):
    cur.execute(f"UPDATE guilds SET chann_bienvenue = {channel} WHERE guild = {ctx.guild.id}")
    conn.commit()
    embed = discord.Embed(
        title=f"Le channel bienvenue a été ajouté a la base de donnée",
        colour=0x00FF00
    )
    await ctx.send(embed=embed)       


@commands.has_permissions(administrator=True)
@bot.command()
async def role_perm(ctx, role):
    cur.execute(f"UPDATE guilds SET role_perm = {role} WHERE guild = {ctx.guild.id}")
    conn.commit()
    embed = discord.Embed(
        title=f"Très bien, maintenant, certaines commandes ne sont utilisables que par les utilisateurs ayant ce role",
        colour=0x00FF00
    )
    await ctx.send(embed=embed)    
    


@bot.command()
@has_perm_role
async def channel_log(ctx, channel):
    cur.execute(f"UPDATE guilds SET chann_log = {channel} WHERE guild = {ctx.guild.id}")
    conn.commit()
    embed = discord.Embed(
        title=f"Le channel LOG a été ajouté a la base de donnée",
        colour=0x00FF00
    )
    await ctx.send(embed=embed)

bot.run(TOKEN)
