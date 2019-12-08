import os
import yaml
import datetime

import re
from discord.ext import commands
from discord.ext.commands import Bot, has_role

from list import SlotList, get_list, get_member, get_channel_author

''' --- onLoad ----'''
client = Bot(command_prefix="!", case_insensitive=True)

client.remove_command("help")

path = os.path.dirname(os.path.abspath(__file__))


#load conf
if os.path.isfile(path + '/config.yml'):
    with open(path + "/config.yml", 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
else:
    print("Please add config.yml to the dir")
    exit()

if not cfg["token"] and cfg["role"] and cfg["language"]:
    print("No valid token in config.yml")
    exit()


#load lang

if os.path.isfile(path + f'/msg_conf/{cfg["language"]}.yml'):
    with open(path + f'/msg_conf/{cfg["language"]}.yml') as ymlfile:
        lang = yaml.safe_load(ymlfile)
else:
    print("Language File missing")
    exit()

#load log

TODAY = datetime.date.today()

if not os.path.isfile(path + f'/logs/{TODAY}.log'):
    LOG_FILE = open(path + f"/logs/{TODAY}.log", "w+")
    LOG_FILE.write(f"---- Created: {datetime.datetime.now()} ----\n\n")
    LOG_FILE.close()


''' ---        ----'''


@client.event
async def on_command_error(ctx, error):
    if(ctx.message.channel != "DMChannel" and ctx.message.channel != "GroupChannel"):
        await ctx.message.delete()

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(ctx.message.author.mention + " " +str(error), delete_after=error.retry_after + 1)
    else:
        await ctx.send(ctx.message.author.mention + " Command not found! Check **!help** for all commands", delete_after=5)

    f = open(path + f"/logs/{TODAY}.log", "a")
    log =  str(datetime.datetime.now()) +                     "\t"
    log += "User: " + str(ctx.message.author).ljust(20) +    "\t"
    log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
    log += "Command: " + str(ctx.message.content) + "\t"
    log += str(error) + "\n"
    f.write(log)
    f.close()

    raise error

''' --- User Commands --- '''

@client.command(hidden = False, description= "[number] slots the author of the message in the slot")
@commands.cooldown(1,0.5, commands.BucketType.channel)
@commands.guild_only()
async def slot(ctx, num=""):
    channel = ctx.message.channel
    channel_author = await get_channel_author(ctx.channel)

    author = ctx.message.author

    instructor = ctx.guild.get_member(cfg["arma3"])
    if not instructor:
        instructor = ctx.guild.get_member(cfg['backup'])

    backup = ctx.guild.get_member(cfg['backup'])

    if not ("ArmA3-Rudelkrieger" in [x.name for x in ctx.message.author.roles]): #TODO: STATIC


        # User-Message
        await author.send(lang["slot"]["new_user"]["user"].format(instructor.display_name).replace('\\n', '\n'))
        # Channel-Message
        await channel_author.send(lang["slot"]["new_user"]["channel"].format(author, author.display_name , channel.name, num))
        # Instructor-Message
        await instructor.send(lang["slot"]["new_user"]["instructor"].format(author, author.display_name , channel.name, num))
        # Assign-Rule
        await author.add_roles([x for x in ctx.guild.roles if x.name == "ArmA3-Rudelanwärter"][0])

    elif num:
        liste, x = await get_list(ctx, client)

        list = SlotList(liste, message = x)

        if(list.enter(ctx.message.author.display_name, num)):
            await list.write()
            await author.send(lang["slot"]["slot"]["success"]["user"].format('/'.join(ctx.channel.name.split('-')[:-1])))
            try:
                await backup.send(lang["slot"]["slot"]["success"]["channel_author"].format(author, ctx.message.author.display_name, channel.name, num))
                await channel_author.send(lang["slot"]["slot"]["success"]["channel_author"].format(author, ctx.message.author.display_name, channel.name, num))
            except:
                pass

            f = open(path + f"/logs/{ctx.message.channel.name}.log", "a")
            log = str(datetime.datetime.now()) + "\t"
            log += f"Slot {num} \n"
            f.write(log)
            f.close()

        else:
            await channel.send(author.mention + " " + lang["slot"]["slot"]["error"]["general"]["channel"], delete_after=5)

        del list

    else:
        await channel.send(ctx.message.author.mention + " " + lang["slot"]["slot"]["error"]["number_missing"]["channel"], delete_after=5)

    await ctx.message.delete()


@client.command(hidden = False, description="unslot the author of the message")
@commands.cooldown(1, 0.5, commands.BucketType.channel)
@commands.guild_only()
async def unslot(ctx):
    channel = ctx.message.channel

    liste, x = await get_list(ctx, client)
    list = SlotList(liste, message = x)

    backup = ctx.guild.get_member(cfg['backup'])
    index = list.exit(ctx.message.author.display_name)
    if index:
        await list.write()
        del list
        await ctx.message.author.send(lang["unslot"]["success"]["user"].format('/'.join(ctx.channel.name.split('-')[:-1])))
        if str(TODAY) == ("-").join(channel.name.split("-")[:-1]):
            try:
                await (await get_channel_author(ctx.channel)).send(
                    lang["unslot"]["success"]["channel_author_date"].format(ctx.message.author, ctx.message.author.display_name, channel.name, index))
            except:
                pass
        else:
            try:
                await backup.send(lang["unslot"]["success"]["channel_author"].format(ctx.message.author, ctx.message.author.display_name, channel.name, index))
                await (await get_channel_author(ctx.channel)).send(lang["unslot"]["success"]["channel_author"].format(ctx.message.author, ctx.message.author.display_name, channel.name, index))
            except:
                pass

        f = open(path + f"/logs/{ctx.message.channel.name}.log", "a")
        log = str(datetime.datetime.now()) + "\t"
        log += f"Unslot \n"
        f.write(log)
        f.close()

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " " + lang["unslot"]["error"]["general"]["channel"], delete_after=5)
        await ctx.message.delete()

@client.command()
async def help(ctx):
    output = "My commands are:\n```yaml\n"

    for element in client.commands:
        if(element != help and not element.hidden):
            output += f"{element}:".ljust(20) + f"{element.description}\n"

    if (cfg['role'] in [x.name for x in ctx.message.author.roles]):
        output += "\n#Admin Commands:\n"
        for element in client.commands:
            if (element != help and element.hidden):
                output += f"{element}:".ljust(20) + f"{element.description}\n"


    output += "```"

    await ctx.message.author.send(output)
    await ctx.message.delete()

''' --- Admin Commands --- '''

@client.command(hidden = True, description= "Initialize the slotlist")
@has_role(cfg["role"])
@commands.guild_only()
async def create(ctx):                          #makes the slotlist editable for the bot
    channel = ctx.message.channel
    out = []

    async for x in channel.history(limit=1000):
        msg = x.content
        if re.search("Slotliste", msg):
            await x.delete()  #await (await channel.send(msg)).pin()

            out.append("Slotlist")

            liste = SlotList(msg, channel=channel)

            await liste.write()
            del liste

            break

    if "Slotlist" in out:
        await ctx.message.author.send(lang["create"]["success"]["user"])

        if not os.path.isfile(path + f'/logs/{ctx.message.channel.name}.log'):
            LOG_FILE = open(path + f"/logs/{ctx.message.channel.name}.log", "w+")
            LOG_FILE.write(f"---- Created: {datetime.datetime.now()} ----\n\n")
            LOG_FILE.close()

    else:
        await ctx.message.author.send(lang["create"]["error"]["general"]["user"])

    await ctx.message.delete()


@client.command(hidden = True, description="[Number] [User] Slots an User in a Slot")
@has_role(cfg["role"])
@commands.cooldown(1,0.5, commands.BucketType.channel)
@commands.guild_only()
async def forceSlot(ctx):      # [Admin Function] slots an user
    channel = ctx.message.channel

    argv = ctx.message.content.split(" ")

    if not len(argv) >= 2:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["forceSlot"]["error"]["arg_error"]["channel"], delete_after=5)
        return


    num = argv[1]
    player = argv[2:]

    if not player:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["forceSlot"]["error"]["missing_target"]["channel"], delete_after=5)
        return

    seperator = " "
    player = seperator.join(player)


    liste, x = await get_list(ctx, client)

    list = SlotList(liste, message = x)

    if (list.enter(player, num)):
        await list.write()
        del list
        await channel.send(ctx.message.author.mention + " " + lang["forceSlot"]["success"]["channel"], delete_after=5)



        try:
            member = get_member(ctx.guild, player)
            await member.send(lang["forceSlot"]["success"]["target"].format(str(ctx.message.author.display_name), '/'.join( ctx.channel.name.split('-')[:-1])))
        except:
            pass

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " " + lang["forceSlot"]["error"]["general"]["channel"], delete_after=5)
        await ctx.message.delete()

@client.command(hidden = True, description="[User] Unslots an User")
@has_role(cfg["role"])
@commands.cooldown(1,0.5, commands.BucketType.channel)
@commands.guild_only()
async def forceUnslot(ctx):           # [Admin Function] unslots an user
    channel = ctx.message.channel

    player = ctx.message.content.split(" ")[1:]
    if not player:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["forceUnslot"]["error"]["missing_target"]["channel"], delete_after=5)
        return

    seperator  = " "
    player = seperator.join(player)

    liste, x = await get_list(ctx, client)
    list = SlotList(liste, message = x)

    if list.exit(player):
        await list.write()
        await channel.send(ctx.message.author.mention + " " + lang["forceUnslot"]["success"]["channel"].format(player), delete_after=5)
        await ctx.message.delete()

        try:
            member = get_member(ctx.guild, player)
            await member.send(lang["forceUnslot"]["success"]["target"].format(ctx.channel.name))
        except:
            pass

    else:
        await channel.send(ctx.message.author.mention + " " + lang["forceUnslot"]["error"]["general"]["channel"].format(player), delete_after=5)
        await ctx.message.delete()

    del list


@client.command(hidden = True, description="[Number] [Group] [Description] Adds a Slot to the list")
@has_role(cfg["role"])
@commands.cooldown(1,2, commands.BucketType.channel)
@commands.guild_only()
async def addslot(ctx):
    channel = ctx.message.channel
    argv = ctx.message.content.split(" ")

    if not len(argv) >= 3:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["addslot"]["error"]["arg_error"]["channel"], delete_after=5)
        return


    slot = argv[1]
    group = argv[2]
    desc = " ".join(argv[3:])

    liste, x = await get_list(ctx, client)
    list = SlotList(liste, message=x)

    if(list.add(slot, group, desc)):
        await list.write()
        del list

        await channel.send(ctx.message.author.mention + " " + lang["addslot"]["success"]["channel"], delete_after=5)

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " " + lang["addslot"]["error"]["general"]["channel"], delete_after=5)
        await ctx.message.delete()



@client.command(hidden = True, description="[Number] [Description] Deletes a Slot from the list")
@has_role(cfg["role"])
@commands.cooldown(1,2, commands.BucketType.channel)
@commands.guild_only()
async def delslot(ctx, slot):
    channel = ctx.message.channel
    liste, x = await get_list(ctx, client)
    list = SlotList(liste, message=x)

    if list.delete(slot):
        await list.write()
        del list

        await channel.send(ctx.message.author.mention + " " + lang["delslot"]["success"]["channel"], delete_after=5)

        await ctx.message.delete()

    else:
        await channel.send(ctx.message.author.mention + " " + lang["delslot"]["error"]["general"]["channel"], delete_after=5)
        await ctx.message.delete()

@client.command(hidden = True, description="[Number] [Description] Edits a Slot")
@has_role(cfg["role"])
@commands.cooldown(1,2, commands.BucketType.channel)
@commands.guild_only()
async def editslot(ctx):
    channel = ctx.message.channel
    argv = ctx.message.content.split(" ")

    if not len(argv) >= 2:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["editslot"]["error"]["arg_error"]["channel"], delete_after=5)
        return


    slot = argv[1]
    desc = " ".join(argv[2:])


    liste, x = await get_list(ctx, client)
    list = SlotList(liste, message=x)

    if(list.edit(slot, desc)):
        await list.write()
        del list

        await channel.send(ctx.message.author.mention + " " + lang["editslot"]["success"]["channel"], delete_after=5)

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " " + lang["editslot"]["error"]["general"]["channel"], delete_after=5)
        await ctx.message.delete()


@client.command(hidden=True, description="[Begin] [End] [optional name] Adds a group to the list")
@has_role(cfg["role"])
@commands.cooldown(1, 2, commands.BucketType.channel)
@commands.guild_only()
async def addgroup(ctx):
    channel = ctx.message.channel
    argv = ctx.message.content.split(" ")

    if not len(argv) >= 2:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["addgroup"]["error"]["arg_error"]["channel"],
                           delete_after=5)
        return

    begin = argv[1]
    end = argv[2]
    if len(argv) > 3:
        name = " ".join(argv[3:])
    else:
        name = ""

    liste, x = await get_list(ctx, client)
    list = SlotList(liste, message=x)

    if (list.group_add(begin, end, name)):
        await list.write()
        del list

        await channel.send(ctx.message.author.mention + " " + lang["addgroup"]["success"]["channel"], delete_after=5)

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " " + lang["addgroup"]["error"]["general"]["channel"],
                           delete_after=5)
        await ctx.message.delete()

@client.command(hidden=True, description="[Begin] [End] [optional name] Adds a group to the list")
@has_role(cfg["role"])
@commands.cooldown(1, 2, commands.BucketType.channel)
@commands.guild_only()
async def delgroup(ctx):
    channel = ctx.message.channel
    argv = ctx.message.content.split(" ")

    if not len(argv) >= 2:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["delgroup"]["error"]["arg_error"]["channel"], #Todo:
                           delete_after=5)
        return

    if len(argv) > 1:
        name = " ".join(argv[1:])
    else:
        name = ""

    liste, x = await get_list(ctx, client)
    list = SlotList(liste, message=x)

    if (list.group_delete(name)):
        await list.write()
        del list

        await channel.send(ctx.message.author.mention + " " + lang["delgroup"]["success"]["channel"], delete_after=5) #Todo

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " " + lang["delgroup"]["error"]["general"]["channel"],
                           delete_after=5)
        await ctx.message.delete()



''' ---        --- '''

client.run(cfg['token'])
