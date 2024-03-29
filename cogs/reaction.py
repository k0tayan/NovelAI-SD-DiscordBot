from discord.ext import commands

from config.load_config import config


class Reaction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # リアクションしたのが自分だったら無視
        if payload.user_id == self.bot.user.id:
            return
        if payload.emoji.name == config["REACTION"]["DELETE"]:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            if message.author == self.bot.user:
                await message.delete()


async def setup(bot):
    await bot.add_cog(Reaction(bot))
