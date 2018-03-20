from riotwatcher import RiotWatcher as rw
import pandas as pd
from discord.ext.commands import Bot
from discord.ext import commands
import discord
import os

prefix="!"
client = Bot(description="Fate bot for discord.", command_prefix=prefix, pm_help = False)
my_region = 'EUW1'
watcher = rw(os.environ['LOL_KEY'])
df_champs = pd.DataFrame()

def getCurrentGamePlayers(game):
    blueSide = []
    redSide = []
    for player in game["participants"]:
        p = {}
        p["championId"] = player["championId"]
        p["summonerId"] = player["summonerId"]
        p["summonerName"] = player["summonerName"]
        if player["teamId"] == 100:
            blueSide.append(p)
        else:
            redSide.append(p)
    return blueSide, redSide

def getCurrentGameData(summonerName):
    ret_str = []
    summonerId = watcher.summoner.by_name(my_region, summonerName)["id"]
    game = watcher.spectator.by_summoner(my_region, summonerId)
    sides = getCurrentGamePlayers(game)
    sideNames = ["Blue", "Red"]
    for i in range(len(["Blue", "Red"])):
        ret_str.append(sideNames[i]+" side:\n")
        for p in sides[i]:
            line = []
            user = watcher.summoner.by_name(my_region, p["summonerName"])
            ranked_data = watcher.league.positions_by_summoner(my_region, user["id"])
            line.append(df_champs.loc[df_champs.id == p["championId"],"name"].values[0])
            line.append("\t|\t")
            line.append("Mastery "+str(watcher.champion_mastery.by_summoner_by_champion(my_region, p["summonerId"], p["championId"])["championLevel"]))
            line.append("\t|\t")
            line.append("LVL "+str(user["summonerLevel"]))
            line.append("\t|\t")
            #Hay gente que no tiene datos de ranked
            if (len(ranked_data) > 0):
                line.append("W/L: "+str(ranked_data[0]["wins"])+"/"+str(ranked_data[0]["losses"]))
                line.append("\t|\t")
                line.append(ranked_data[0]["tier"]+" "+ranked_data[0]["rank"])
            else:
                line.append("W/L: NODATA")
                line.append("\t|\t")
                line.append("NODATA")
            line.append("\n")
            ret_str.append(''.join(line))
        ret_str.append("\n\n")
    return "".join(ret_str)


@client.event
async def on_ready():
    print(f'Logged in as {client.user.name} (ID:{client.user.id}) | Connected to {str(len(client.servers))} servers | Connected to {str(len(set(client.get_all_members())))} users')
    champs = watcher.static_data.champions(my_region)['data']
    global df_champs
    df_champs = pd.DataFrame.from_dict(list(champs.values()))
    return await client.change_presence(game=discord.Game(name='Ready'))

@client.command(pass_context=True)
async def game(ctx, summoner="empty"):
    """Sends a predefined number of dices."""
    if summoner == "empty":
        await client.say("Plase, enter a correct summoner name.")
    else:
        await client.say("Loading... Please wait.")
        await client.say(getCurrentGameData(summoner))

@client.command(pass_context=True)
async def clear(ctx):
    """ Clears every bot message from the channel. """
    await client.purge_from(ctx.message.channel, limit=200, check=lambda m: (m.author == client.user) or m.content.startswith(prefix))

#def set_picture(url):
client.run(os.environ['DISCORD_KEY'])
