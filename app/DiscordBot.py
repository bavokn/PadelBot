import discord
import os
from dotenv import load_dotenv
import datetime
from discord.ext import commands, tasks
import asyncio
import nest_asyncio
from PadelBot import PadelBot

nest_asyncio.apply()

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())
        self.padelBot = PadelBot()

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.padelchecker.start()

    @tasks.loop(minutes=30)  # task runs every 30 mins
    async def padelchecker(self):
      channel = self.get_channel(1054019553413304413)  # channel ID goes here
      self.padelBot.refresh()
      while not self.padelBot.messageQueue.empty():
        message = self.padelBot.messageQueue.get()
        await channel.send(message) 

    @padelchecker.before_loop
    async def before_my_task(self):
      await self.wait_until_ready()  # wait until the bot logs in

bot = Bot()
TOKEN = 'MTA1NDAxODk4MTM4MTU1ODMyMw.Gpqzi4.h5KasBSIjjlGp3ZOXUZKrwiQFJObHJkR2U7ONY'
bot.run(TOKEN)