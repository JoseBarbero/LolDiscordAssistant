from riotwatcher import RiotWatcher as rw
import pandas as pd
from discord.ext.commands import Bot
from discord.ext import commands
import discord
import os
import requests
from requests import HTTPError
from texttable import Texttable
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 

prefix="!"
invite_link="https://discordapp.com/oauth2/authorize?client_id=425635422874370058&scope=bot"
client = Bot(description="League of Legends assistant bot for discord. Developed by SowlJBA. \n If you want to use this bot in your own server, please use this link: "+invite_link, command_prefix=prefix, pm_help = False)
my_region = 'EUW1'
watcher = rw(os.environ['LOL_KEY'])
df_champs = pd.DataFrame()
formatted_champs = {}

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
    try:
        summonerId = watcher.summoner.by_name(my_region, summonerName)["id"]
        game = watcher.spectator.by_summoner(my_region, summonerId)
    except HTTPError as err:
        return 'Probably this summoner is not currently in a game or his name is wrong.'
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
            try:
                line.append("Mastery "+str(watcher.champion_mastery.by_summoner_by_champion(my_region, p["summonerId"], p["championId"])["championLevel"]))
            except HTTPError as err:
                line.append("Mastery 0")
            line.append("\t|\t")
            line.append("LVL "+str(user["summonerLevel"]))
            line.append("\t|\t")

            #Don't judge me for this, I have no time
            if (len(ranked_data) == 0):
                line.append("W/L: NODATA")
                line.append("\t|\t")
                line.append("NODATA")
            elif (len(ranked_data) == 1):
                if ranked_data[0]["queueType"]=="RANKED_SOLO_5x5":
                    line.append("W/L: "+str(ranked_data[0]["wins"])+"/"+str(ranked_data[0]["losses"]))
                    line.append("\t|\t")
                    line.append(ranked_data[0]["tier"]+" "+ranked_data[0]["rank"])
                else:
                    line.append("W/L: NODATA")
                    line.append("\t|\t")
                    line.append("NODATA")
            elif (len(ranked_data) == 2):
                if ranked_data[0]["queueType"]=="RANKED_SOLO_5x5":
                    line.append("W/L: "+str(ranked_data[0]["wins"])+"/"+str(ranked_data[0]["losses"]))
                    line.append("\t|\t")
                    line.append(ranked_data[0]["tier"]+" "+ranked_data[0]["rank"])
                elif ranked_data[1]["queueType"]=="RANKED_SOLO_5x5":
                    line.append("W/L: "+str(ranked_data[1]["wins"])+"/"+str(ranked_data[1]["losses"]))
                    line.append("\t|\t")
                    line.append(ranked_data[1]["tier"]+" "+ranked_data[1]["rank"])
                else:
                    line.append("W/L: NODATA")
                    line.append("\t|\t")
                    line.append("NODATA")
            else:
                line.append("W/L: NODATA")
                line.append("\t|\t")
                line.append("NODATA")
            line.append("\t|\t")
            line.append(p["summonerName"])
            line.append("\n")
            ret_str.append(''.join(line))
        ret_str.append("\n\n")
    return "".join(ret_str)

def gotChest(my_region, sum_name, champ_name):
    try:
        sum_id = watcher.summoner.by_name(my_region, sum_name)["id"]
    except HTTPError as err:
        print('Wrong summoner name.')
        return None
    try:
        champ_id = df_champs.loc[df_champs.name.str.lower() == champ_name.lower(), "id"].values[0]
    except:
        print('Wrong champion name.')
        return None
    sum_id = watcher.summoner.by_name(my_region, sum_name)["id"]
    champ_id = df_champs.loc[df_champs.name.str.lower() == champ_name.lower(), "id"].values[0]
    return watcher.champion_mastery.by_summoner_by_champion(my_region, sum_id, champ_id)["chestGranted"]

def nameToUrlFormat(name):
    new_name = name.replace("'","")
    new_name = new_name.replace(". ","-")
    new_name = new_name.replace(" ","-")
    new_name = new_name.lower()
    return new_name

def getCounters (champion):
    counters = {}
    page = requests.get('https://www.counterstats.net/league-of-legends/'+nameToUrlFormat(champion))
    soup = BeautifulSoup(page.text, 'html.parser')
    position_boxes = soup.find(class_="champ-box__wrap")
    champion_box = soup.find_all(class_='champ-box ALL')
    
    for box in champion_box:
        if box.find("em").text == "Best Picks":
            worst_picks = box    
            break
    try:
        for champ in worst_picks.find_all("a"):
            for perc in champ.find_all(class_ = "percentage"):
                if float(perc.text[:-1]) > 55:
                    counters[champ["href"].split("/")[3][3:]] = float(perc.text[:-1])
        for champ in worst_picks.find_all(class_= "champ-box__row"):
            for bar in champ.find_all(class_="bar-div"):
                for perc in bar.find("b"):
                    if float(perc[:-1]) > 55:
                        counters[champ["href"].split("/")[3][3:]] = float(perc[:-1])
    except:
        return None
    return counters

def getCountereds (champion):
    page = requests.get('https://www.counterstats.net/league-of-legends/'+nameToUrlFormat(champion))
    soup = BeautifulSoup(page.text, 'html.parser')
    position_boxes = soup.find(class_="champ-box__wrap")
    champion_box = soup.find_all(class_='champ-box ALL')
    countereds = {}
    for box in champion_box:
        if box.find("em").text == "Worst Picks":
            worst_picks = box
            break #This gets the most played position
    try:
        for champ in worst_picks.find_all("a"):
            for perc in champ.find_all(class_ = "percentage"):
                if float(perc.text[:-1]) < 45:
                    countereds[champ["href"].split("/")[3][3:]] = float(perc.text[:-1])
        for champ in worst_picks.find_all(class_= "champ-box__row"):
            for bar in champ.find_all(class_="bar-div"):
                for perc in bar.find("b"):
                    if float(perc[:-1]) < 45:
                        countereds[champ["href"].split("/")[3][3:]] = float(perc[:-1])
    except:
        return None
    return countereds

def formatChamps (champs, formatted_champs):
    f_champs = []
    for champ in champs:
        f_champs.append(formatted_champs[champ])
    return f_champs

def getRunes(champion, pos):
    images = []
    page = requests.get(f'http://euw.op.gg/champion/{champion}/statistics/{pos}')
    soup = BeautifulSoup(page.text, 'html.parser')
    runes_boxes = soup.find(class_="perk-page-wrap")
    for rune_page in runes_boxes.find_all(class_="perk-page"):
        rune_page_list = []
        for rune_row in rune_page.find_all(class_="perk-page__row"):
            img_row = []
            for img in rune_row.find_all("img"):
                img_row.append("http:"+img["src"])
            rune_page_list.append(img_row)
        images.append(rune_page_list)
    
    x_dim = 0
    y_dim = 0
    for rune_page in images:
        if len(rune_page)>y_dim:
            y_dim = len(rune_page)
        for rune_row in rune_page:
            if len(rune_row) > x_dim:
                x_dim = len(rune_row)
                
    total_width = x_dim*275
    total_heigth = y_dim*110
    new_im = Image.new('RGBA', (total_width, total_heigth))
    p = 0
    for rune_page in images:
        y = 25
        col_width = total_width / 2
        for row in rune_page:
            c = 0
            x_pos = range(0, int(col_width), int(col_width/(len(row)+1)))
            for image in row:
                r = requests.get(image)
                b = BytesIO(r.content)
                size = 100, 100
                img = Image.open(b)
                img = img.convert('RGBA')
                img.thumbnail(size)
                if y==25:
                    new_im.paste(img, (x_pos[c+1]-50+p, y))
                else:
                    new_im.paste(img, (x_pos[c+1]-75+p, y))
                c+=1
            y += 100
        p+=x_dim*125
    return new_im

def getSummoners(champion, pos):
    summoners = []

    page = requests.get(f'http://euw.op.gg/champion/{champion}/statistics/{pos}')
    soup = BeautifulSoup(page.text, 'html.parser')
    
    #Summoners
    champ = soup.find(class_="champion-overview__table champion-overview__table--summonerspell")
    summs_block = champ.find("tbody")
    for sum_row in summs_block.find_all(class_="champion-overview__data"):
        row = []
        for item in sum_row.find_all(class_="champion-stats__list__item"):
            row.append("http:"+item.find("img")["src"])
        summoners.append(row)
    return summoners

def getSkills(champion, pos):
    skills = []
    order = []
    
    page = requests.get(f'http://euw.op.gg/champion/{champion}/statistics/{pos}')
    soup = BeautifulSoup(page.text, 'html.parser')
    
    #Summoners
    champ = soup.find(class_="champion-overview__table champion-overview__table--summonerspell")
    summs_block = champ.find_all("tbody")[1]

    for item in summs_block.find_all(class_="champion-stats__list__item"):
        skills.append(("http:"+item.find("img")["src"], item.find("span").text))
    
    skill_table = summs_block.find(class_="champion-skill-build__table")
    skill_row = skill_table.find_all("tr")[1] #We take the second row
    for cell in skill_row.find_all("td"):
        order.append(cell.text.replace('\n', '').replace('\t', ''))
    return skills, order

def getBuild(champion, pos):
    
    inits = []
    builds = []
    boots = []
    
    page = requests.get(f'http://euw.op.gg/champion/{champion}/statistics/{pos}')
    soup = BeautifulSoup(page.text, 'html.parser')
    
    #Summoners
    n_group = 0
    champ = soup.find_all(class_="champion-overview__table")[1] #Second table
    for items_row in champ.find_all(class_="champion-overview__row"):
        row = []
        for item in items_row.find_all(class_="champion-stats__list__item"):
            row.append("http:"+item.find("img")["src"])
            
        title = items_row.find(class_="champion-overview__sub-header")
        if title != None:
            n_group += 1
        if n_group == 1: #So that we only get the first group (init items)
            inits.append(row)
        elif n_group == 2: #Core build
            builds.append(row)
        elif n_group == 3: #Boots
            boots.append(row)            
            
    return inits, builds, boots

def getRunes(champion, pos):
    images = []
    page = requests.get(f'http://euw.op.gg/champion/{champion}/statistics/{pos}')
    soup = BeautifulSoup(page.text, 'html.parser')
    runes_boxes = soup.find(class_="perk-page-wrap")
    for rune_page in runes_boxes.find_all(class_="perk-page"):
        rune_page_list = []
        for rune_row in rune_page.find_all(class_="perk-page__row"):
            img_row = []
            for img in rune_row.find_all("img"):
                img_row.append("http:"+img["src"])
            rune_page_list.append(img_row)
        images.append(rune_page_list)
    
    x_dim = 0
    y_dim = 0
    for rune_page in images:
        if len(rune_page)>y_dim:
            y_dim = len(rune_page)
        for rune_row in rune_page:
            if len(rune_row) > x_dim:
                x_dim = len(rune_row)
                
    total_width = x_dim*275
    total_heigth = y_dim*110
    new_im = Image.new('RGBA', (total_width, total_heigth))
    p = 0
    for rune_page in images:
        y = 25
        col_width = total_width / 2
        for row in rune_page:
            c = 0
            x_pos = range(0, int(col_width), int(col_width/(len(row)+1)))
            for image in row:
                r = requests.get(image)
                b = BytesIO(r.content)
                size = 100, 100
                img = Image.open(b)
                img = img.convert('RGBA')
                img.thumbnail(size)
                if y==25:
                    new_im.paste(img, (x_pos[c+1]-50+p, y))
                else:
                    new_im.paste(img, (x_pos[c+1]-75+p, y))
                c+=1
            y += 100
        p+=x_dim*125
    return new_im

def getBuilds(chamion, pos):
    summs = getSummoners(chamion, pos)
    skills = getSkills(chamion, pos)
    inits = getBuild(chamion, pos)[0]
    build = getBuild(chamion, pos)[1]
    boots = getBuild(chamion, pos)[2]
    
    arrow = "https://opgg-static.akamaized.net/images/site/champion/blet.png"
    
    y_dim = len(max([summs, skills, inits, build], key=len))
    
    total_width = 1200
    total_heigth = y_dim*100
    new_im = Image.new('RGBA', (total_width, total_heigth))
    
    #Summs and skills
    p = 25
    y = 100
    
    draw = ImageDraw.Draw(new_im)
    font = ImageFont.truetype("fonts/arial.ttf", 32)
    draw.text((25, 50), "Summoner spells", (200,200,200), font=font)
    
    for row in summs:
        x = p
        for image in row:
            r = requests.get(image)
            b = BytesIO(r.content)
            size = 100, 100
            img = Image.open(b)
            img = img.convert('RGBA')
            img.thumbnail(size)
            new_im.paste(img, (x+25, y))
            x += 75
        y += 75
    
    x = p
    y += 25
    
    draw.text((x, y), "Skill order", (200,200,200), font=font)
    
    y += 75
    i = 1
    for image, letter in skills[0]:
        r = requests.get(image)
        b = BytesIO(r.content)
        size = 100, 100
        img = Image.open(b)
        img = img.convert('RGBA')
        img.thumbnail(size)
        new_im.paste(img, (x+p, y))
        draw.text((x+p+5, y+5), letter, (225,225,225), font=font)
        
        x += 75
        
        if i < len(skills[0]):
            r = requests.get(arrow)
            b = BytesIO(r.content)
            size = 100, 100
            img = Image.open(b)
            img = img.convert('RGBA')
            img.thumbnail(size)
            new_im.paste(img, (x+5, y+15))
        i += 1
    y += 75
    x = p
    skill_font = ImageFont.truetype("fonts/arial.ttf", 20)
    draw.text((x, y), '-'.join(skills[1]), (200,200,200), font=skill_font)
    
    #Inits and boots
    p = int(total_width/3)
    y = 100
    draw.text((p, 50), "Starting items", (200,200,200), font=font)
    
    for row in inits:
        x = p
        i = 1
        for image in row:
            r = requests.get(image)
            b = BytesIO(r.content)
            size = 100, 100
            img = Image.open(b)
            img = img.convert('RGBA')
            img.thumbnail(size)
            new_im.paste(img, (x+25, y))
            x += 75
            if i < len(row):
                r = requests.get(arrow)
                b = BytesIO(r.content)
                size = 100, 100
                img = Image.open(b)
                img = img.convert('RGBA')
                img.thumbnail(size)
                new_im.paste(img, (x+5, y+15))
            i += 1
        y += 75
    
    x = p
    y += 25
    
    draw.text((p, y), "Boots", (200,200,200), font=font)
    
    y += 75
    
    for row in boots:
        for image in row:
            r = requests.get(image)
            b = BytesIO(r.content)
            size = 100, 100
            img = Image.open(b)
            img = img.convert('RGBA')
            img.thumbnail(size)
            new_im.paste(img, (x+25, y))
            x += 75
    
    
    
    #Core build
    p = int(total_width/3)*2
    y = 100
    draw.text((p, 50), "Core items", (200,200,200), font=font)
    for row in build:
        x = p
        i = 1
        for image in row:
            r = requests.get(image)
            b = BytesIO(r.content)
            size = 100, 100
            img = Image.open(b)
            img = img.convert('RGBA')
            img.thumbnail(size)
            new_im.paste(img, (x+25, y))
            x += 75
            
            if i < len(row):
                r = requests.get(arrow)
                b = BytesIO(r.content)
                size = 100, 100
                img = Image.open(b)
                img = img.convert('RGBA')
                img.thumbnail(size)
                new_im.paste(img, (x+5, y+15))
                
            i += 1
            
        y += 75
        
    return new_im


@client.event
async def on_ready():
    print(f'Logged in as {client.user.name} (ID:{client.user.id}) | Connected to {str(len(client.servers))} servers | Connected to {str(len(set(client.get_all_members())))} users')
    champs = watcher.static_data.champions(my_region)['data']
    global df_champs
    df_champs = pd.DataFrame.from_dict(list(champs.values()))
    #Formatting champ names to correspond with the url of https://www.counterstats.net/league-of-legends/miss-fortune
    global formatted_champs
    for champ in list(df_champs['name']):
        new_name = champ.replace("'","")
        new_name = new_name.replace(". ","-")
        new_name = new_name.replace(" ","-")
        new_name = new_name.lower()
        formatted_champs[new_name] = champ
    return await client.change_presence(game=discord.Game(name='Ready'))

@client.command(pass_context=True)
async def game(ctx, summoner="empty"):
    """Sends the current game info."""
    if summoner == "empty":
        await client.say("Plase, enter a correct summoner name.")
    else:
        await client.say("Loading... Please wait.")
        await client.say(getCurrentGameData(summoner))

@client.command(pass_context=True)
async def canchest(ctx, summoner="empty", champion="empty"):
    """Tells if the given summoner can get a chest with the given champion."""
    if summoner == "empty" or champion=="empty":
        await client.say("Plase, enter a correct summoner name and a correct champion.")
    else:
        res = gotChest(my_region, summoner, champion)
        if res is not None:
            if res:
                await client.say(f"No, sorry. You already got an S with {champion}.")
            else:
                await client.say(f"Yes, you don't have a chest with {champion} yet.")
        else:
            await client.say("Plase, enter a correct summoner name and a correct champion.")

@client.command(pass_context=True)
async def counter(ctx, champ="empty"):
    """Gets counter and countered champs for a given champion"""
    if champ == "empty":
        await client.say("Please, introduce a correct champion name.")
    else:
        await client.say("Working on it...")
        counters = getCounters(champ)
        countereds = getCountereds(champ)
        message = []
        await client.purge_from(ctx.message.channel, limit=1, check=lambda m: (m.author == ctx.message.author) or m.content.startswith("Working"))
        if counters == None or countereds == None:
            await client.say("Please, introduce a correct champion name.")
        else:
            message.append("WEAK VS:")
            if len(counters) > 0:
                for counter, winrate in counters.items():
                    message.append(f"    {formatted_champs[nameToUrlFormat(champ)]}'s winrate vs {formatted_champs[counter]} is {round(100-winrate, 2)}%")     
            else:
                message.append(f"    There are no champs with more than 55% winrate vs {formatted_champs[nameToUrlFormat(champ)]}")
            message.append("\nSTRONG VS:")
            if len(countereds) > 0:
                for countered, winrate in countereds.items():
                    message.append(f"    {formatted_champs[nameToUrlFormat(champ)]}'s winrate vs {formatted_champs[countered]} is {round(100-winrate, 2)}%")
            else:
                message.append(f"    There are no champs with less than 45% winrate vs {formatted_champs[nameToUrlFormat(champ)]}")
            await client.say('\n'.join(message))

@client.command(pass_context=True)
async def clear(ctx):
    """ Clears every bot message from the channel. """
    await client.purge_from(ctx.message.channel, limit=200, check=lambda m: (m.author == client.user) or m.content.startswith(prefix))

@client.command(pass_context=True)
async def invitelink(ctx):
    """ Send the invitation link to use this bot in your own server. """
    await client.say("If you want to use this bot in you own server, use this link: \n"+invite_link)

@client.command(pass_context=True)
async def runes(ctx, champ, pos):
    """ Send the recommended runes for a given champ and position. """
    if champ == None or pos == None:
        await client.say("Please, introduce a correct champion name.")
    else:
        await client.say("Working on it...")
        filename = "temp.png"
        try:
            getRunes(champ, pos).save(filename,"PNG")
            await client.send_file(ctx.message.channel, filename)
        except:
            await client.say("Please, introduce a correct champion name.")
        await client.purge_from(ctx.message.channel, limit=2, check=lambda m: (m.author == ctx.message.author) or m.content.startswith("Working"))

@client.command(pass_context=True)
async def build(ctx, champ, pos):
    """ Send the recommended bluids for a given champ and position. """
    if champ == None or pos == None:
        await client.say("Please, introduce a correct champion name.")
    else:
        await client.say("Working on it...")
        filename = "temp.png"
        try:
            getBuilds(champ, pos).save(filename,"PNG")
            await client.send_file(ctx.message.channel, filename)
        except:
            await client.say("Please, introduce a correct champion name.")
        await client.purge_from(ctx.message.channel, limit=2, check=lambda m: (m.author == ctx.message.author) or m.content.startswith("Working"))
        try:
            os.remove(filename)
        except OSError:
            pass

client.run(os.environ['DISCORD_KEY'])
