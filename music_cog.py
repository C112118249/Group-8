import discord
from discord.ext import commands
import yt_dlp
import asyncio
import logging

log = logging.getLogger(__name__)

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc: discord.VoiceClient | None = None
        self.current_player: discord.PCMVolumeTransformer | None = None
        self.playlist = []
        self.history = []
        self.current_title = None
        self.current_url = None
        self.is_playing = False
        self.skip_requested = False
        self.loop_enabled = False  # 單曲循環

    async def extract_audio_url(self, url: str):
        """抓取音訊串流 URL (ffmpeg 可播放)"""
        ydl_opts = {
            "format": "bestaudio",
            "quiet": True,
            "no_warnings": True,
            "default_search": "ytsearch",
            "noplaylist": True,
        }

        loop = asyncio.get_event_loop()

        def run_ydl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if "entries" in info:
                    info = info["entries"][0]
                return info

        info = await loop.run_in_executor(None, run_ydl)
        audio_url = info["url"]
        title = info["title"]
        return title, audio_url

    async def play_next(self, ctx):
        if self.current_title and self.loop_enabled:
            self.playlist.insert(0, (self.current_title, self.current_url))

        if not self.playlist:
            self.is_playing = False
            self.current_title = None
            self.current_url = None
            await ctx.send("🎶 播放列表已結束。")
            if self.vc and self.vc.is_connected():
                await self.vc.disconnect()
            return

        title, audio_url = self.playlist.pop(0)

        if self.current_title and self.current_url and not self.loop_enabled:
            self.history.append((self.current_title, self.current_url))

        self.current_title = title
        self.current_url = audio_url

        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn"
        }

        self.current_player = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(
                audio_url,
                executable=r"C:\Users\User\Discord Music Bot\ffmpeg.exe",
                **ffmpeg_options
            ),
            volume=0.5
        )

        if self.vc.is_playing():
            self.vc.stop()

        def after_play(error):
            if error:
                log.error(f"[MusicCog] 播放錯誤: {error}")
            asyncio.run_coroutine_threadsafe(self._after_play_task(ctx), self.bot.loop)

        self.vc.play(self.current_player, after=after_play)
        await ctx.send(f"🎶 正在播放：**{title}**" + (" 🔁(單曲循環)" if self.loop_enabled else ""))

    async def _after_play_task(self, ctx):
        if self.skip_requested:
            self.skip_requested = False
            return
        if self.loop_enabled or self.playlist:
            await self.play_next(ctx)
        else:
            self.is_playing = False
            self.current_title = None
            self.current_url = None

    # ---------------- 音樂指令 ----------------
    @commands.command(name="播放")
    async def 播放(self, ctx, *, url: str = None):
        if not ctx.author.voice:
            return await ctx.send("❌ 你需要先加入語音頻道！")
        if not self.vc or not self.vc.is_connected():
            self.vc = await ctx.author.voice.channel.connect()
        if not url:
            return await ctx.send("請輸入 YouTube 連結，例如：`&播放 <網址>`")
        try:
            title, audio_url = await self.extract_audio_url(url)
            self.playlist.append((title, audio_url))
            if not self.is_playing:
                self.is_playing = True
                await self.play_next(ctx)
            else:
                await ctx.send(f"🎵 **{title}** 已加入播放列表")
        except Exception as e:
            log.error(f"[MusicCog] 播放失敗: {e}", exc_info=True)
            await ctx.send(f"❌ 播放失敗：{str(e)}\n💡 嘗試更新 yt-dlp：`python -m pip install -U yt-dlp`")

    @commands.command(name="跳過")
    async def 跳過(self, ctx):
        if self.vc and self.vc.is_playing():
            self.skip_requested = True
            await ctx.send("⏭ 跳過當前音樂")
            self.vc.stop()
        else:
            await ctx.send("❌ 沒有正在播放的音樂！")

    @commands.command(name="上一首")
    async def 上一首(self, ctx):
        if not self.history:
            return await ctx.send("❌ 沒有上一首可以播放！")
        prev_title, prev_url = self.history.pop()
        if self.current_title and self.current_url:
            self.playlist.insert(0, (self.current_title, self.current_url))
        self.playlist.insert(0, (prev_title, prev_url))
        self.skip_requested = True
        if self.vc.is_playing():
            self.vc.stop()
        await self.play_next(ctx)

    @commands.command(name="暫停")
    async def 暫停(self, ctx):
        if self.vc and self.vc.is_playing():
            self.vc.pause()
            await ctx.send("⏸ 已暫停播放")
        else:
            await ctx.send("❌ 沒有正在播放的音樂！")

    @commands.command(name="恢復")
    async def 恢復(self, ctx):
        if self.vc and self.vc.is_paused():
            self.vc.resume()
            await ctx.send("▶ 已恢復播放")
        else:
            await ctx.send("❌ 沒有音樂可以恢復播放！")

    @commands.command(name="停止")
    async def 停止(self, ctx):
        if self.vc and self.vc.is_connected():
            self.vc.stop()
            self.playlist.clear()
            self.is_playing = False
            self.loop_enabled = False
            await ctx.send("⏹ 已停止播放，並清空播放列表。")

    @commands.command(name="離開")
    async def 離開(self, ctx):
        if self.vc and self.vc.is_connected():
            self.vc.stop()
            self.playlist.clear()
            self.is_playing = False
            self.loop_enabled = False
            await self.vc.disconnect()
            await ctx.send("🚶‍♂️ 已離開語音頻道。")

    @commands.command(name="循環")
    async def 循環(self, ctx):
        self.loop_enabled = not self.loop_enabled
        status = "✅ 已開啟單曲循環" if self.loop_enabled else "❌ 已關閉單曲循環"
        await ctx.send(f"🔁 {status}")

    @commands.command(name="歷史")
    async def 歷史(self, ctx):
        if self.history:
            history_list = "\n".join([f"{i+1}. {song[0]}" for i, song in enumerate(self.history[-10:])])
            await ctx.send(f"📜 最近播放紀錄：\n{history_list}")
        else:
            await ctx.send("❌ 沒有播放紀錄！")

    @commands.command(name="播放列表")
    async def 播放列表(self, ctx):
        if self.playlist:
            queue_list = "\n".join([f"{i+1}. {song[0]}" for i, song in enumerate(self.playlist)])
            await ctx.send(f"🎶 播放列表：\n{queue_list}")
        else:
            await ctx.send("❌ 播放列表為空！")

    @commands.command(name="正在播放")
    async def 正在播放(self, ctx):
        if self.is_playing and self.vc and self.vc.is_playing() and self.current_title:
            await ctx.send(f"🎶 正在播放：**{self.current_title}**" + (" 🔁(單曲循環)" if self.loop_enabled else ""))
        else:
            await ctx.send("❌ 目前沒有正在播放的音樂！")

    @commands.command(name="說明")
    async def 說明(self, ctx):
        help_text = (
            "🎵 **音樂機器人指令列表**\n"
            "`&播放 <網址>` - 播放音樂\n"
            "`&跳過` - 跳過目前音樂\n"
            "`&上一首` - 播放上一首\n"
            "`&歷史` - 查看最近播放紀錄\n"
            "`&循環` - 開啟/關閉單曲循環\n"
            "`&正在播放` - 顯示目前播放的歌曲\n"
            "`&播放列表` - 查看待播清單\n"
            "`&暫停` - 暫停播放\n"
            "`&恢復` - 恢復播放\n"
            "`&停止` - 停止播放並清空清單\n"
            "`&離開` - 離開語音頻道"
        )
        await ctx.send(help_text)

async def setup(bot):
    await bot.add_cog(MusicCog(bot))

