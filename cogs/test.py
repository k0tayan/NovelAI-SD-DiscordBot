from discord.ext import commands

from utils.logger import MyLogger


class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = MyLogger(__name__)

    @commands.command(name="test")
    @MyLogger.log_command
    async def test(self, ctx: commands.Context, *args):
        """Test command."""

        await ctx.reply("test")


async def setup(bot):
    await bot.add_cog(Test(bot))
