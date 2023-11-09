from config.load_config import config
import discord
from discord.ext import commands

from logging import getLogger, StreamHandler, DEBUG, Formatter
import os
import asyncio

COGS = [
    "cogs.locale",
    "cogs.help",
    "cogs.reaction",
    "cogs.test",
]

bot = commands.Bot(command_prefix="", help_command=None, intents=discord.Intents.all())

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
formatter = Formatter("%(asctime)s : %(levelname)s : %(name)s : %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False


@bot.event
async def on_ready():
    logger.info("We have logged in as {0.user}".format(bot))


# コマンドが存在しない場合にエラーを出さない
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error


if __name__ == "__main__":

    async def main():
        for cog in COGS:
            await bot.load_extension(cog)
        if config["USE_WEBUI"]:
            await bot.load_extension("cogs.sd")
            await bot.load_extension("cogs.link_expand")
        if config["USE_NOVELAI"]:
            await bot.load_extension("cogs.nai")
        await bot.start(os.getenv("DISCORD_TOKEN"))

    asyncio.run(main())
