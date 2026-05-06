import discord
from discord import app_commands
import random
import os
from flask import Flask
from threading import Thread

# --- Renderでの常時起動用設定 ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    # Renderのポート番号を取得（デフォルトは10000）
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# --- ボットのクラス定義 ---
class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # フリスク反応用
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.gacha_list = [] # サーバーIDを保存するリスト

    async def setup_hook(self):
        # スラッシュコマンドをDiscordに同期
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

# 「フリスク」への反応
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    # 「フリスク」という文字が含まれていたら反応
    if "フリスク" in message.content:
        await message.channel.send("😑 (Stay determined!)")

# サーバーをガチャに追加するコマンド
@bot.tree.command(name="add", description="このサーバーをガチャに追加します（管理者のみ）")
@app_commands.checks.has_permissions(administrator=True)
async def add(interaction: discord.Interaction):
    if interaction.guild_id not in bot.gacha_list:
        bot.gacha_list.append(interaction.guild_id)
        await interaction.response.send_message(f"✅ **{interaction.guild.name}** をガチャに追加しました！", ephemeral=True)
    else:
        await interaction.response.send_message("このサーバーは既に追加されています。", ephemeral=True)

# ガチャを引くコマンド
@bot.tree.command(name="gacha", description="登録されたサーバーからランダムに招待を送ります")
async def gacha(interaction: discord.Interaction):
    if not bot.gacha_list:
        await interaction.response.send_message("現在、ガチャに追加されているサーバーがありません。", ephemeral=True)
        return

    target_id = random.choice(bot.gacha_list)
    target_guild = bot.get_guild(target_id)

    if target_guild:
        try:
            # 招待作成権限がある最初のチャンネルを探す
            target_channel = None
            for channel in target_guild.text_channels:
                if channel.permissions_for(target_guild.me).create_instant_invite:
                    target_channel = channel
                    break
            
            if target_channel:
                invite = await target_channel.create_invite(max_age=300, max_uses=1)
                await interaction.response.send_message(f"✨ **当たりのサーバー：{target_guild.name}**\n{invite}")
            else:
                await interaction.response.send_message("招待リンクを作成できるチャンネルが見つかりませんでした。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"エラーが発生しました: {e}", ephemeral=True)
    else:
        await interaction.response.send_message("サーバーが見つかりませんでした。ボットがそのサーバーにいない可能性があります。", ephemeral=True)

# 実行
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("エラー: 環境変数 DISCORD_TOKEN が設定されていません。")
