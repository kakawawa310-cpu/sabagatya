import discord
from discord import app_commands
import random
import os
import asyncio
from flask import Flask
from threading import Thread

# --- Flaskの設定 ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# --- ボットのクラス定義 ---
class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.gacha_list = [] 

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    # 起動時に参加中のサーバーをリストに追加
    bot.gacha_list = [guild.id for guild in bot.guilds]

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if "フリスク" in message.content:
        await message.channel.send("😑 (Stay determined!)")

@bot.tree.command(name="add", description="このサーバーをガチャに追加します")
@app_commands.checks.has_permissions(administrator=True)
async def add(interaction: discord.Interaction):
    if interaction.guild_id not in bot.gacha_list:
        bot.gacha_list.append(interaction.guild_id)
        await interaction.response.send_message(f"✅ {interaction.guild.name} を追加！", ephemeral=True)
    else:
        await interaction.response.send_message("既に追加されています。", ephemeral=True)

@bot.tree.command(name="gacha", description="サーバーガチャを引きます")
async def gacha(interaction: discord.Interaction):
    if not bot.gacha_list:
        await interaction.response.send_message("サーバーがありません。", ephemeral=True)
        return
    
    valid_guilds = [bot.get_guild(gid) for gid in bot.gacha_list if bot.get_guild(gid)]
    if not valid_guilds:
        await interaction.response.send_message("有効なサーバーが見つかりません。", ephemeral=True)
        return

    target_guild = random.choice(valid_guilds)
    try:
        target_channel = None
        if target_guild.system_channel and target_guild.system_channel.permissions_for(target_guild.me).create_instant_invite:
            target_channel = target_guild.system_channel
        else:
            for channel in target_guild.text_channels:
                if channel.permissions_for(target_guild.me).create_instant_invite:
                    target_channel = channel
                    break
        
        if target_channel:
            invite = await target_channel.create_invite(max_age=300, max_uses=1)
            await interaction.response.send_message(f"✨ **{target_guild.name}**\n{invite}")
        else:
            await interaction.response.send_message("招待作成権限がありません。", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"エラー: {e}", ephemeral=True)

# --- 実行部分の修正 ---
def run_bot():
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("DISCORD_TOKEN is not set.")

if __name__ == "__main__":
    # 1. ボットを別スレッドで開始
    t = Thread(target=run_bot)
    t.start()
    
    # 2. Flaskをメインスレッドで開始（Renderのポート監視に確実に答えるため）
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
