# bot url = https://discordapp.com/oauth2/authorize?client_id=509991584067223571&permissions=206848&scope=bot

import discord
import asyncio
from discord.ext.commands import Bot
import time
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
from Crypto import Random
from Crypto.Random import random
import hashlib
import hmac
import base64 

style.use("fivethirtyeight")

client = discord.Client()
token = open("token.txt", "r").read()
bot_id = 509991584067223571
guild = client.get_guild(509992354543960064)


num_ports = {21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", # List of ports
         53: "DNS", 67: "DHCP Server", 68: "DHCP Client",
         80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",                # Need both for the port search later.
         }
text_ports = {v: k for k, v in num_ports.items()} # Reversed list of ports


def community_report(guild):
    online = 0
    idle = 0
    offline = 0

    for member in guild.members: # Go through members in the server
        if str(member.status) == "online":
            online += 1
        if str(member.status) == "offline":
            offline += 1
        elif str(member.status) == "idle" or str(member.status) == "dnd":
            idle += 1

    return online, idle, offline


async def user_metrics_background_task():
    await client.wait_until_ready()
    guild = client.get_guild(509992354543960064)

    while not client.is_closed():
        try:
            online, idle, offline = community_report(guild) # Get the data
            with open("usermetrics.csv","a") as f:
                f.write(f"{int(time.time())},{online},{idle},{offline}\n") # Put data in CSV file

            plt.clf()
            df = pd.read_csv("usermetrics.csv", names = ['time', 'online', 'idle', 'offline']) # Read CSV file
            df['date'] = pd.to_datetime(df['time'],unit = 's')
            df['total'] = df['online'] + df['offline'] + df['idle']
            df.drop("time", 1,  inplace = True)
            df.set_index("date", inplace = True)
            df['online'].plot(), df['offline'].plot(), df['idle'].plot() # Map data onto the grapgh
            plt.legend()
            plt.savefig("online.png") # Save graph as image

            await asyncio.sleep(30)

        except Exception as e:
            print(str(e))
            await asyncio.sleep(5)

        
class BotCrypto: # Massive shoutout to @Nanibongwa on Discord/nsk89 on git for this implementation.
    def generate_password(self, length):
        # generate random bytes and hash returned data
        password = self.hash_data(Random.get_random_bytes(length))
        secret = self.hash_data(Random.get_random_bytes(length))
        # create secure hmac'd hash password
        hmac_pass = base64.b64encode(hmac.new(password, secret, hashlib.sha3_384).digest())

        return self.symbol_insert(hmac_pass[:length].decode())

    def symbol_insert(self, passphrase):
        # list of symbols to choose from
        symbol_list = ['!', '@', '#', '$', '%', '^', '&' '*', '(', ')', '+', '=', '_']
        # define the amount of symbols to use in a given string based on length >= 8
        symbol_count = round(len(passphrase) / 4)
        count = 0
        while count < symbol_count:  # pick random symbols based on int chosen and append it to passphrase
            rand_int = random.randrange(0, len(symbol_list))
            passphrase += symbol_list[rand_int]
            count += 1

        passphrase = [char for char in passphrase]  # no delimiter, no .split(). list comprehension to split characters
        random.shuffle(passphrase)  # Pycrypdome shuffle, shuffle the list elements around
        passphrase = ''.join(passphrase)  # rejoin the list into the passphrase string

        return passphrase

    def hash_data(self, data):  # convert data to hash
        data = self.check_for_bytes(data)
        hasher = hashlib.new('sha3_384')
        hasher.update(data)

        return self.check_for_bytes(hasher.hexdigest())

    def check_for_bytes(self, data):  # verify incoming data is in byte form
        if type(data) != bytes:
            data = bytes(data, 'utf-8')
            return data
        else:
            return data


@client.event
async def on_ready(): # Connection confirmation.
    print(f"We have logged in as {client.user}.")


@client.event # Event wrapper.
async def on_message(message, *args):
    print(f"New message in {message.channel}:") # Outputs message in the terminal.
    print(f"    Author: {message.author} / {message.author.id}\n    Screen name: {message.author.name}\n    Message: {message.content}\n    Date: {message.created_at}\n")

    guild = client.get_guild(509992354543960064)

    if f"<@{bot_id}>" == message.content: # If bot is tagged.
        await message.channel.send(f"Hello, <@!{message.author.id}>. Use !help to get a list of my commands.")


    elif "!help" == message.content.lower(): # Command to list commands
        await message.channel.send("```\
    !help - Show this message\n\
    !clear - Delete channel messages up to 14 days old.\n\
    !passgen x - Password generator between 8 - 32 chars (x being the length you want the password)\n\
    !user_info - Get user count.\n\
    !ports - Show a list of common ports.\n\
    !user_analysis - Show a graph of activity.```")


    elif "!ports" == message.content.lower(): # Shows a list of common ports. Going to make it into a search.
        await message.channel.send(f"```py\nCommon Ports: \n{pd.DataFrame.from_dict(text_ports, orient = 'index')}```")


    elif message.content.startswith("!passgen"): # Password generator
        args = message.content.split(" ")[1]

        try:
            length = int(args) # Check if input is an int

        except ValueError:
            await message.channel.send("Error, not a valid input!")

        
        if length < 8 or length > 32: # Control length
            await message.channel.send("Error, not a valid input!")

        else: # Create password and send it as a private message
            crypto = BotCrypto()
            password = crypto.generate_password(length)

            await message.author.create_dm()
            await message.author.send(f'Your password is: {password}')


    elif "!clear" == message.content.lower(): # Delete all messages (Need to implement number of messages to delete)
        counter = 0
        messages = []
        channel = message.channel

        # Need to add date check

        async for message in message.channel.history(): # Go through messages in channel
            counter += 1
            messages.append(message) # Add message to list

        await channel.delete_messages(messages) # Delete messages from list

        clear_end = await message.channel.send(f"I deleted {counter} messages.")
        messages.append(clear_end)

        time.sleep(1)

        await channel.delete_messages(messages) # delete the bot message


    elif "!user_info" == message.content.lower(): # Gives server info
        online, idle, offline = community_report(guild)
        await message.channel.send(f"```py\nTotal Users: {guild.member_count}\n    Online: {online}\n    Idle/busy/dnd: {idle}\n    Offline: {offline}```")


    elif "!user_analysis" == message.content.lower(): # Sends a graph of user activity
        file = discord.File("online.png", filename = "online.png")
        await message.channel.send("User Analysis", file = file)


client.loop.create_task(user_metrics_background_task())
client.run(token)
