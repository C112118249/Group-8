import discord
from discord.ext import commands
import asyncio

# 讀取 bot token
def get_token():
    with open("token.txt", "r") as f:
        return f.read().strip()  # 去除多餘空白字符

# 初始化 bot
intents = discord.Intents.default()
intents.message_content = True  # 允許讀取訊息內容

bot = commands.Bot(command_prefix="&", intents=intents)

# 當 bot 準備好時
@bot.event
async def on_ready():
    print(f"✅ 登入成功：{bot.user}")
    try:
        # 載入 music_cog
        await bot.load_extension('music_cog')
        print("MusicCog 加載成功！")
    except Exception as e:
        print(f"加載 MusicCog 時發生錯誤: {e}")

    try:
        # 載入 meeting_cog
        await bot.load_extension('meeting_cog')
        print("MeetingCog 加載成功！")
    except Exception as e:
        print(f"加載 MeetingCog 時發生錯誤: {e}")
    print("機器人已經準備好，可以使用命令了！")

# 捕捉 command 錯誤
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ 無效的指令！請使用 `&說明` 查看所有可用指令。")
    else:
        await ctx.send(f"❌ 指令執行時發生錯誤：{error}")

# 啟動 bot
if __name__ == "__main__":
    token = get_token()
    if not token:
        print("❌ 請確認 token.txt 中有正確的 Bot Token")
    else:
        bot.run(token)

