from backend import webui, novelai
import discord
import io
import base64
from discord.ext import commands
from dotenv import load_dotenv
import os
import yaml
import uuid
import random
import aiohttp
import asyncio

load_dotenv()
with open('config.yml', encoding='utf-8') as file:
    config = yaml.safe_load(file)

bot = commands.Bot(command_prefix='nai ', intents=discord.Intents.all())
nai = novelai.NovelAI()
use_webui = config['USE_WEBUI']
use_novelai = config['USE_NOVELAI']
admin_ids = config['ADMIN_IDS']
allowed_guild_ids = config['ALLOWED_GUILD_IDS']
default_negative_prompt = config['DEFAULT_NEGATIVE_PROMPT']


def save_image(binary, filename:str):
    dir = config['GENERATED_IMAGE_OUTDIR']
    with open(f'{dir}/{filename}.jpg', 'wb') as f:
        f.write(binary)

def parse_prompt(prompt: tuple):
    n = (lambda x : x.index('-u') if '-u' in x else -1)(prompt)
    if n >= len(prompt)-1:
        raise ValueError("パラメーターが不正です。")
    negative_prompt = ' '.join("" if n == -1 else prompt[n+1:])
    positive_prompt = ' '.join(prompt if n == -1 else prompt[:n])
    return positive_prompt, negative_prompt

def log_command(ctx, image_filename):
    if(ctx.guild is None):
        print(f'{ctx.author}({ctx.author.id}) {ctx.command} {image_filename}')
    else:
        print(f'{ctx.author}({ctx.author.id}) {ctx.command} in {ctx.guild}({ctx.guild.id}) {image_filename}')

def log_prompt(p, n):
    print(f'positive_prompt: {p}')
    print(f'negative_prompt: {n}')

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

if use_webui:
    # WebUIを使用する場合
    ui = webui.WebUI(config['WEBUI_URI'], 'v1')
    @bot.command(name='sd')
    async def generate_with_sd(ctx, *prompt):
        """NSFWチャンネルのみsd [positive_prompt] -u [negative_prompt]"""
        if ctx.author.id not in admin_ids:
            # サーバー内でのみ使用可能
            if ctx.guild is None:
                await ctx.send("このコマンドは紫式部サーバー内でのみ使用できます。")
                return
            # サーバーが許可されているかどうかを確認
            if ctx.guild.id not in allowed_guild_ids:
                await ctx.send("このコマンドはこのサーバーで使用できません。")
                return
            # チャンネルがNSFWチャンネルかどうかを確認
            if not ctx.channel.is_nsfw():
                await ctx.send("このコマンドはNSFWチャンネルでのみ使用できます。")
                return
        await ctx.send(random.choice(config["RESPONSE_MESSAGE"]))
        positive_prompt, negative_prompt = parse_prompt(prompt)
        response = await ui.generate_image(
            positive_prompt, (512, 768), default_negative_prompt+negative_prompt, steps=20)
        b64_image = response["images"][0]
        image_data = base64.b64decode(b64_image)
        image_filename = str(uuid.uuid4())
        save_image(image_data, image_filename)
        log_command(ctx, image_filename)
        log_prompt(positive_prompt, negative_prompt)
        file = discord.File(io.BytesIO(image_data), filename="image.jpg")
        await ctx.send(file=file)

if use_novelai:
    # NovelAIを使用する
    @bot.command(name='sfw')
    async def generate_with_nai(ctx, *prompt):
        """SFWな画像を生成します sfw [positive_prompt] -u [negative_prompt]"""
        if ctx.author.id not in admin_ids:
            # サーバー内でのみ使用可能
            if ctx.guild is None:
                await ctx.send("このコマンドは紫式部サーバー内でのみ使用できます。")
                return
            # サーバーが許可されているかどうかを確認
            if ctx.guild.id not in allowed_guild_ids:
                await ctx.send("このコマンドはこのサーバーで使用できません。")
                return
        await ctx.send(random.choice(config["RESPONSE_MESSAGE"]))
        positive_prompt, negative_prompt = parse_prompt(prompt)
        image_data = await nai.generate(positive_prompt, (512, 768), negative_prompt, True)
        image_filename = str(uuid.uuid4())
        save_image(image_data, image_filename)
        log_command(ctx, image_filename)
        log_prompt(positive_prompt, negative_prompt)
        file = discord.File(io.BytesIO(image_data), filename="image.jpg")
        await ctx.send(file=file)

    @bot.command(name='nsfw')
    async def generate_with_nai(ctx, *prompt):
        """NSFWチャンネルのみ nsfw [positive_prompt] -u [negative_prompt]"""
        if ctx.author.id not in admin_ids:
            # サーバー内でのみ使用可能
            if ctx.guild is None:
                await ctx.send("このコマンドは紫式部サーバー内でのみ使用できます。")
                return
            # サーバーが許可されているかどうかを確認
            if ctx.guild.id not in allowed_guild_ids:
                await ctx.send("このコマンドはこのサーバーで使用できません。")
                return
            # チャンネルがNSFWチャンネルかどうかを確認
            if not ctx.channel.is_nsfw():
                await ctx.send("このコマンドはNSFWチャンネルでのみ使用できます。")
                return
        await ctx.send(random.choice(config["RESPONSE_MESSAGE"]))
        positive_prompt, negative_prompt = parse_prompt(prompt)
        image_data = await nai.generate(positive_prompt, (512, 768), negative_prompt, False)
        image_filename = str(uuid.uuid4())
        save_image(image_data, image_filename)
        log_command(ctx, image_filename)
        log_prompt(positive_prompt, negative_prompt)
        file = discord.File(io.BytesIO(image_data), filename="image.jpg")
        await ctx.send(file=file)

if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
