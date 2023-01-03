import os
import math
import logging
import logging.config
from aiohttp import web
from CYNITE import web_server

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

from pyrogram.errors import BadRequest, Unauthorized
from datetime import datetime
from pytz import timezone
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR, LOG_CHANNEL, PORT, CHANNELS, UPDATES_CHANNEL_USERNAME,BOT_USERNAME, BOT_SESSION_NAME  
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
LOGGER = logging.getLogger(__name__)
TIMEZONE = (os.environ.get("TIMEZONE", "Asia/Kolkata"))

class Bot(Client):

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "CYNITE"},
            sleep_threshold=5,
        )

    async def start(self):
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()
        await Media.ensure_indexes()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        temp.B_LINK = me.mention
        self.username = '@' + me.username
        curr = datetime.now(timezone(TIMEZONE))
        date = curr.strftime('%d %B, %Y')
        time = curr.strftime('%I:%M:%S %p')
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()
        logging.info(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
        logging.info(LOG_STR)
        if LOG_CHANNEL:
            try:
                await self.send_message(LOG_CHANNEL, text=f"<b>{me.mention} Rᴇsᴛᴀʀᴛᴇᴅ !!\n\n📅 Dᴀᴛᴇ : <code>{date}</code>\n⏰ Tɪᴍᴇ : <code>{time}</code>\n🌐 Tɪᴍᴇᴢᴏɴᴇ : <code>{TIMEZONE}</code>\n\n🉐 Vᴇʀsɪᴏɴ : <code>v{__version__}</code></b>")
            except Unauthorized:
                LOGGER.warning("Bot isn't able to send message to LOG_CHANNEL")
            except BadRequest as e:
                LOGGER.error(e)

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")

    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        """Iterate through a chat sequentially.
        This convenience method does the same as repeatedly calling :meth:`~pyrogram.Client.get_messages` in a loop, thus saving
        you from the hassle of setting up boilerplate code. It is useful for getting the whole chat messages with a
        single call.
        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).
                
            limit (``int``):
                Identifier of the last message to be returned.
                
            offset (``int``, *optional*):
                Identifier of the first message to be returned.
                Defaults to 0.
        Returns:
            ``Generator``: A generator yielding :obj:`~pyrogram.types.Message` objects.
        Example:
            .. code-block:: python
                for message in app.iter_messages("pyrogram", 1, 15000):
                    print(message.text)
        """
        
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current +=1
      
    async def message_handler(event):
        try:
            if event.message.post:
                return

        # if event.is_channel:return
            if event.text.startswith("/"):return

            print("\n")
            print("Message Received: " + event.text)

        # Force Subscription
            if  not await get_user_join(event.sender_id):
                haha = await event.reply(f'''**Hey! {event.sender.first_name} 😃**
**You Have To Join Our Update Channel To Use Me ✅**
**Click Below Button To Join Now.👇🏻**''', buttons=Button.url('🍿Updates Channel🍿', f'https://t.me/{UPDATES_CHANNEL_USERNAME}'))
                await asyncio.sleep(DELETE_TIME)
                return await haha.delete()

            args = event.text
            args = await validate_q(args)

            print("Search Query: {args}".format(args=args))
            print("\n")

            if not args:
                return

            txt = await event.reply('**Printing Links For "{}" 🔍**'.format(event.text))



            search = []
            if event.is_group or event.is_channel:
                group_info = await db.get_group(str(event.chat_id).replace("-100", ""))

                if group_info["has_access"] and group_info["db_channel"] and await db.is_group_verified(str(event.chat_id).replace("-100", "")):
                    CHANNELS = group_info["db_channel"]
                else:
                    CHANNELS = CHANNELS
            else:
                CHANNELS = CHANNELS


            async for i in AsyncIter(re.sub("__|\*", "", args).split()):
                if len(i) > 2:
               
                    search_msg = client.iter_messages(CHANNELS, limit=5, search=i)
                    search.append(search_msg)

            username = UPDATES_CHANNEL_USERNAME 
            answer = f'**Join** [@{username}](https://telegram.me/{username}) \n\n'

            c = 0

            async for msg_list in AsyncIter(search):
                async for msg in msg_list:
                    c += 1
                    f_text = re.sub("__|\*", "", msg.text)

                    f_text = await link_to_hyperlink(f_text)
                    answer += f'\n\n\n✅ PAGE {c}:\n\n━━━━━━━━━\n\n' + '' + f_text.split("\n", 1)[0] + '' + '\n\n' + '' + f_text.split("\n", 2)[
                    -1] + "\n\n"
                
            # break
            finalsearch = []
            async for msg in AsyncIter(search):
                finalsearch.append(msg)

            if c <= 0:
                answer = f'''** Sorry {event.sender.first_name} No Results Found For {event.text}**
**Please check the spelling on** [Google](http://www.google.com/search?q={event.text.replace(' ', '%20')}%20Movie) 🔍
**Click On The Help To Know How To Watch**
    '''

                newbutton = [Button.url('Help🙋',
                                    f'https://t.me/postsearchbot?start=Watch')]

                await txt.delete()
                result = await event.reply(answer, buttons=newbutton, link_preview=False)
                await asyncio.sleep(DELETE_TIME)
                await event.delete()
                return await result.delete()
            else:
                pass

            answer += f"\n\n**Uploaded By @{UPDATES_CHANNEL_USERNAME }**"
            answer = await replace_username(answer)
            html_content = await markdown_to_html(answer)
            html_content = await make_bold(html_content)
        
            tgraph_result = await telegraph_handler(
                html=html_content,
                title=event.text,
                author=BOT_USERNAME
            )
            message = f'**Click Here 👇 For "{event.text}"**\n\n[🍿🎬 {str(event.text).upper()}\n🍿🎬 {str("Click me for results").upper()}]({tgraph_result})'

            newbutton = [Button.url('How To Watch ❓',
                                    f'https://t.me/postsearchbot?start=Watch')]

            await txt.delete()
            await asyncio.sleep(0.5)
            result = await event.reply(message, buttons=newbutton, link_preview=False)
            await asyncio.sleep(DELETE_TIME)
        # await event.delete()
            return await result.delete()

        except Exception as e:
            print(e)
            await txt.delete()
            result = await event.reply("I am Unable Search,Please Search In @PostSearchBOT🙏")
            await asyncio.sleep(DELETE_TIME)
            await event.delete() 
            return await result.delete()


    async def escape_url(str):
        escape_url = urllib.parse.quote(str)
        return escape_url

# Bot Client for Inline Search
    Bot = Client(
        session_name=BOT_SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        plugins=dict(root="plugins")
    )
                
                
app = Bot()
app.run()
