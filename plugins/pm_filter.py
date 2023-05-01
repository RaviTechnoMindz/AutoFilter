# Kanged From @TechnoMindz
import asyncio
import re
import ast
import math
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, P_TTI_SHOW_OFF, IMDB, \
    SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}


@Client.on_message((filters.group | filters.private) & filters.text & filters.incoming)
async def give_filter(client, message):
    k = await manual_filters(client, message)
    if k == False:
        await auto_filter(client, message)


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("Check Your Own Request 😤", show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You Are Using My Old Messages🥲,Try Asking Again 🤠.", show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    settings = await get_settings(query.message.chat.id)
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"♨️[{get_size(file.file_size)}]{file.file_name}", callback_data=f'files#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}", callback_data=f'files#{file.file_id}'
                ),
                InlineKeyboardButton(
                    text=f"♨️[{get_size(file.file_size)}]",
                    callback_data=f'files_#{file.file_id}',
                ),
            ]
            for file in files
        ]

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"📃 Pages {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    btn.insert(0,
            [
                InlineKeyboardButton("彡[ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ]彡", url="https://t.me/TMmainchannel")
            ])

    btn.insert(0, [
        InlineKeyboardButton("🤖𓂀ℍ𝕆𝕎 𝕋𝕆 𝔻𝕆𝕎ℕ𝕃𝕆𝔸𝔻𓂀🤖", url="https://t.me/tmmainchannel/4")
    ])
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer("Check Your Own Requests Buddy 😤", show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movies = SPELL_CHECK.get(query.message.reply_to_message.id)
    if not movies:
        return await query.answer("You are clicking on an old button which is expired.", show_alert=True)
    movie = movies[(int(movie_))]
    await query.answer('Checking for Movie in my database...')
    k = await manual_filters(bot, query.message, text=movie)
    if k == False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
        else:
            one_button = InlineKeyboardMarkup([[InlineKeyboardButton("🥲 𝗢𝗪𝗡𝗘𝗥 🔥", url="https://t.me/TechnoKillerBot"), InlineKeyboardButton("🤕 𝗚𝗢𝗢𝗚𝗟𝗘 🤒", url="https://www.google.com/")]])
            k = await msg.reply_video(video="https://telegra.ph//file/d90256b1575c7aaadccc5.mp4", caption="Hey, 𝐒𝐨𝐫𝐫𝐲, 𝐍𝐨 𝐌𝐨𝐯𝐢𝐞/𝐒𝐞𝐫𝐢𝐞𝐬 𝐑𝐞𝐥𝐚𝐭𝐞𝐝 𝐓𝐨 𝐓𝐡𝐞 𝐆𝐢𝐯𝐞𝐧 𝐖𝐨𝐫𝐝 𝐖𝐚𝐬 𝐅𝐨𝐮𝐧𝐝 🥺\n\n𝙿𝚘𝚜𝚜𝚒𝚋𝚕𝚎 𝙲𝚊𝚞𝚜𝚎𝚜 : 🤔\n\n⭕️ 𝐍𝐨𝐭 𝐑𝐞𝐥𝐞𝐚𝐬𝐞𝐝 𝐘𝐞𝐭\n⭕️ 𝐈𝐧𝐜𝐨𝐫𝐫𝐞𝐜𝐭 𝐒𝐩𝐞𝐥𝐥𝐢𝐧𝐠\n⭕ 𝐍𝐨𝐭 𝐔𝐩𝐥𝐨𝐚𝐝𝐞𝐝 𝐁𝐲 𝐎𝐰𝐧𝐞𝐫\n\n👉Contact To My Owner👇", reply_markup = one_button)
            await asyncio.sleep(20)
            await k.delete()
            await msg.delete()


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer('⏳Loading...')
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer('⏳Loading...')

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('⏳Loading...')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that -_- !", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("That's not for you!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer('⏳Loading...')
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer('⏳Loading...')
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('⏳Loading...')
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('⏳Loading...')
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer('⏳Loading...')
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
        buttons = [
            [
                InlineKeyboardButton('彡[ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ]彡', url='https://t.me/tmmainchannel')
            ],
            [
                InlineKeyboardButton('🤖𓂀ℍ𝕆𝕎 𝕋𝕆 𝔻𝕆𝕎ℕ𝕃𝕆𝔸𝔻𓂀🤖', url=f'https://t.me/tmmainchannel/4')
            ]
            ]

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            elif settings['botpm']:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                tm1 = await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    protect_content=True if ident == "filep" else False,
                    reply_markup=InlineKeyboardMarkup(
                        [
                         [
                          InlineKeyboardButton('𝐌𝐚𝐢𝐧 𝐂𝐡𝐚𝐧𝐧𝐞𝐥', url='https://t.me/TmMainChannel'),
                          InlineKeyboardButton('𝐒𝐔𝐏𝐏𝐎𝐑𝐓', url='https://t.me/TechnoMindzChat')
                       ],[
                          InlineKeyboardButton("𝑅𝑒𝓆𝓊𝑒𝓈𝓉 𝒶𝑔𝒶𝒾𝓃", url="https://t.me/technomoviescollection")
                       ],[
                          InlineKeyboardButton("𝕆𝕨𝕟𝕖𝕣", url="t.me/technomindzyt")
                         ]
                        ]
                    )
                )
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn 😑!', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("I Like Your Smartness, But Don't Be Oversmart 😒", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        buttons = [
            [
                InlineKeyboardButton('彡[ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ]彡', url='https://t.me/tmmainchannel')
            ],
            [
                InlineKeyboardButton('🤖𓂀 ℍ𝕆𝕎 𝕋𝕆 𝔻𝕆𝕎ℕ𝕃𝕆𝔸𝔻 𓂀🤖', url=f'https://t.me/tmmainchannel/4')
            ]
            ]
        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False
        )
    elif query.data == "pages":
        await query.answer()
    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('𐂷𐤠ƊƊ 𐒄Ƹ ƬⰙ ƳⰙꓴⱤ ƓⱤⰙꓴꝒ𐂷', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('📢 𝐉𝐨𝐢𝐧 𝐌𝐚𝐢𝐧 𝐂𝐡𝐚𝐧𝐧𝐞𝐥', url='https://t.me/TmMainChannel')
            ],[
            InlineKeyboardButton('♥ﮩ٨ـﮩ му♡gяσυρ ﮩـ٨ﮩ♥', url='https://t.me/technomindzchat')
            ],[
            InlineKeyboardButton('🆘 𝐒𝐔𝐏𝐏𝐎𝐑𝐓', url='https://t.me/Technomindzchat')
            ],[
            InlineKeyboardButton('༺ 𝓓𝓔𝓥𝓔𝓛𝓞𝓟𝓔𝓡 ༻', url='https://t.me/TechnomindzYt'),
            InlineKeyboardButton('𓂀 𝒮𝒪𝒰𝑅𝒞𝐸 𓂀', url='https://t.me/technomindzchat')
            ],[      
            InlineKeyboardButton('♻️ HΞLᎮ ♻️', callback_data='help'),
            InlineKeyboardButton('♻️ ΛBOUT ♻️', callback_data='about')
            ],[
            InlineKeyboardButton('✅ SUBSCᏒIBΞ  ✅', url='https://www.youtube.com/c/TechnoMindz')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer('🏠Home...')
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('𝙼𝙰𝙽𝚄𝙴𝙻 𝙵𝙸𝙻𝚃𝙴𝚁', callback_data='manuelfilter'),
            InlineKeyboardButton('𝙰𝚄𝚃𝙾 𝙵𝙸𝙻𝚃𝙴𝚁', callback_data='autofilter')
        ], [
            InlineKeyboardButton('𝙲𝙾𝙽𝙽𝙴𝙲𝚃𝙸𝙾𝙽𝚂', callback_data='coct'),
            InlineKeyboardButton('𝙴𝚇𝚃𝚁𝙰', callback_data='extra')
        ], [
            ],[
            InlineKeyboardButton('𝙷𝙾𝚆 𝚃𝙾 𝙳𝙴𝙿𝙻𝙾𝚈..?', url='https://youtu.be/mWWxKxNP8ls'),
            InlineKeyboardButton('🔮𝚂𝚃𝙰𝚃𝚄𝚂', callback_data='stats')
            ],[
            InlineKeyboardButton('⚚ 𝙱𝙰𝙲𝙺 ⚚', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("𝖶𝖾𝗅𝖼𝗈𝗆𝖾 𝗍𝗈 𝗆𝗒 𝖧𝖾𝗅𝗉 𝗆𝗈𝖽𝗎𝗅𝖾")
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('𐂷 𐤠ƊƊ 𐒄Ƹ ƬⰙ ƳⰙꓴⱤ ƓⱤⰙꓴꝒ 𐂷', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('📢 𝐉𝐨𝐢𝐧 𝐌𝐚𝐢𝐧 𝐂𝐡𝐚𝐧𝐧𝐞𝐥', url='https://t.me/TmMainChannel')
            ],[
            InlineKeyboardButton('♥ﮩ٨ـﮩ му♡gяσυρ ﮩـ٨ﮩ♥', url='https://t.me/technomindzchat')
            ],[
            InlineKeyboardButton('🆘 𝐒𝐔𝐏𝐏𝐎𝐑𝐓', url='https://t.me/Technomindzchat'),
            InlineKeyboardButton('sᴇᴀʀᴄʜ🔎', switch_inline_query_current_chat='')
            ],[
            InlineKeyboardButton('༺ 𝓓𝓔𝓥𝓔𝓛𝓞𝓟𝓔𝓡 ༻', url='https://t.me/TechnomindzYt'),
            InlineKeyboardButton('𓂀 𝒮𝒪𝒰𝑅𝒞𝐸 𓂀', url='https://t.me/technomindzchat')
            ],[
            InlineKeyboardButton('🏠𝐇𝐎𝐌𝐄', callback_data='start'),
            InlineKeyboardButton('❌𝙲𝙻𝙾𝚂𝙴❌', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("Check About Me 😉")
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='about')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("My Source 🤔")
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='help'),
            InlineKeyboardButton('⏹️ Buttons', callback_data='button')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("Loading Manual Filter...")
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MANUELFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "button":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='manuelfilter')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("Loading Buttons Module...")
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='help')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("Loading AutoFilter...")
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='help')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        
        await n.delete()
        await query.answer("Check My Connections Mondule...")
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "extra":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='help'),
            InlineKeyboardButton('👮‍♂️ Admin', callback_data='admin')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("Extars...")
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.EXTRAMOD_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "admin":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='extra')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("Admin Commands ...")
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ADMIN_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='help'),
            InlineKeyboardButton('♻️REFRESH', callback_data='rfrsh')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("Checking My Status...")
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "rfrsh":
        await query.answer("Refreshing...")
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='help'),
            InlineKeyboardButton('♻️REFRESH', callback_data='rfrsh')
        ]]
        r=await query.message.reply_text('▣▣▢▢▢▢')
        a=await r.edit('▣▣▣▢▢▢')
        v=await a.edit('▣▣▣▣▢▢')
        i=await v.edit('▣▣▣▣▣▢')
        n=await i.edit('▣▣▣▣▣▣')
        await asyncio.sleep(1)
        await n.delete()
        await query.answer("Loading...")
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Your Active Connection Has Been Changed. Go To /settings.")
            return await query.answer('✅Changed...')

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('𝐅𝐈𝐋𝐓𝐄𝐑 𝐁𝐔𝐓𝐓𝐎𝐍',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('𝐒𝐈𝐍𝐆𝐋𝐄' if settings["button"] else '𝐃𝐎𝐔𝐁𝐋𝐄',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝐁𝐎𝐓 𝐏𝐌', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["botpm"] else '🗑️ 𝐍𝐎',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝐅𝐈𝐋𝐄 𝐒𝐄𝐂𝐔𝐑𝐄',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["file_secure"] else '🗑️ 𝐍𝐎',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝐈𝐌𝐃𝐁', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["imdb"] else '🗑️ 𝐍𝐎',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝐒𝐏𝐄𝐋𝐋 𝐂𝐇𝐄𝐂𝐊',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["spell_check"] else '🗑️ 𝐍𝐎',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝐖𝐄𝐋𝐂𝐎𝐌𝐄', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["welcome"] else '🗑️ 𝐍𝐎',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer('⏳Loading...')


async def auto_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                if settings["spell_check"]:
                    return await advantage_spell_chok(msg)
                else:
                    return
        else:
            return
    else:
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
    pre = 'filep' if settings['file_secure'] else 'file'
    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"💫[{get_size(file.file_size)}] {file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}",
                    callback_data=f'{pre}#{file.file_id}',
                ),
                InlineKeyboardButton(
                    text=f"💫[{get_size(file.file_size)}]",
                    callback_data=f'{pre}#{file.file_id}',
                ),
            ]
            for file in files
        ]

    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="NEXT ⏩", callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🗓 1/1", callback_data="pages"),
             InlineKeyboardButton(text="Chatting", url="https://t.me/technomindzchat")]
        )

    btn.insert(0, [
        InlineKeyboardButton("𓂀𝕄𝕆𝕍𝕀𝔼𝕊𓂀", url="https://t.me/technomoviescollection"),
        InlineKeyboardButton("彡ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ]彡", url="https://t.me/tmmainchannel")
    ])
    btn.insert(0, [
        InlineKeyboardButton("🤖𓂀ℍ𝕆𝕎 𝕋𝕆 𝔻𝕆𝕎ℕ𝕃𝕆𝔸𝔻𓂀🤖", url="https://t.me/tmmainchannel/4")
    ])
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            mention_bot=temp.MENTION,
            mention_user=message.from_user.mention if message.from_user else message.sender_chat.title,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"<b>Hi 👋 {message.from_user.mention}</b>\n\n<b>💖 <STRONG>{search}</STRONG> 💝\n𝗨𝗣𝗟𝗢𝗔𝗗𝗘𝗗 𝗕𝗬 ♪♪\n✨@TechnoMoviesCollection\n\n⚙️ Nᴏᴛᴇ:→𝗧𝗵𝗶𝘀 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝗪𝗶𝗹𝗹 𝗕𝗲 𝗔𝘂𝘁𝗼-𝗗𝗲𝗹𝗲𝘁𝗲𝗱 𝗔𝗳𝘁𝗲𝗿 5 𝗠𝗶𝗻𝘂𝘁𝗲 𝗧𝗼 𝗔𝘃𝗼𝗶𝗱 𝗖𝗼𝗽𝘆𝗿𝗶𝗴𝗵𝘁 𝗜𝘀𝘀𝘂𝗲𝘀.\n\n➥ 𝗝𝗼𝗶𝗻 ➼ 🔗@TmMainChannel</b> "
    if imdb and imdb.get('poster'):
        try:
            fmsg = await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024],#Imdb Poster Code
                                      reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            fmsg = await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))#Imdb Poster Code
        except Exception as e:
            logger.exception(e)
            fmsg = await message.reply_photo(photo='https://telegra.ph/file/95909c55bee8db79f7b9a.jpg', caption=cap, reply_markup=InlineKeyboardMarkup(btn))# fmsg = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn)) Use This code if you need only caption
    else:
        fmsg = await message.reply_photo(photo='https://telegra.ph/file/95909c55bee8db79f7b9a.jpg', caption=cap, reply_markup=InlineKeyboardMarkup(btn))# fmsg = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn)) Use This code if you need only caption
    
    await asyncio.sleep(300)
    await fmsg.delete()
    await client.send_video(
                chat_id=message.chat.id,
                video="https://telegra.ph/file/0cddf1c687a0dbc256313.mp4",
                caption=f"📢 ⚙️ Fɪʟᴛᴇʀ Fᴏʀ <code>{search}</code> \nBʏ <spoiler>{message.from_user.mention}</spoiler> \nIs Now Cʟᴏꜱᴇᴅ 🗑️\n\n@TmMainChannel",
                reply_to_message_id=message.id
            )
    

    if spoll:
        await msg.message.delete()



async def advantage_spell_chok(msg):
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)  # plis contribute some common words
    query = query.strip() + " movie"
    g_s = await search_gagala(query)
    g_s += await search_gagala(msg.text)
    gs_parsed = []
    if not g_s:
        k = await msg.reply_video(video="https://telegra.ph//file/d90256b1575c7aaadccc5.mp4", caption="<b>Hey, 𝐒𝐨𝐫𝐫𝐲, 𝐍𝐨 𝐌𝐨𝐯𝐢𝐞/𝐒𝐞𝐫𝐢𝐞𝐬 𝐑𝐞𝐥𝐚𝐭𝐞𝐝 𝐓𝐨 𝐓𝐡𝐞 𝐆𝐢𝐯𝐞𝐧 𝐖𝐨𝐫𝐝 𝐖𝐚𝐬 𝐅𝐨𝐮𝐧𝐝 🥺</b>\n\n<b>𝙿𝚘𝚜𝚜𝚒𝚋𝚕𝚎 𝙲𝚊𝚞𝚜𝚎𝚜 : 🤔</b>\n\n<b>⭕️ 𝐍𝐨𝐭 𝐑𝐞𝐥𝐞𝐚𝐬𝐞𝐝 𝐘𝐞𝐭\n⭕️ 𝐈𝐧𝐜𝐨𝐫𝐫𝐞𝐜𝐭 𝐒𝐩𝐞𝐥𝐥𝐢𝐧𝐠\n⭕ 𝐍𝐨𝐭 𝐔𝐩𝐥𝐨𝐚𝐝𝐞𝐝 𝐁𝐲 𝐎𝐰𝐧𝐞𝐫\n\n<b>👉Contact To My Owner👇</b>\n\n<b>@TechnoKillerBot 🌴</b>")
        await asyncio.sleep(20)
        await k.delete()
        return
    regex = re.compile(r".*(imdb|wikipedia).*", re.IGNORECASE)  # look for imdb / wiki results
    gs = list(filter(regex.match, g_s))
    gs_parsed = [re.sub(
        r'\b(\-([a-zA-Z-\s])\-\simdb|(\-\s)?imdb|(\-\s)?wikipedia|\(|\)|\-|reviews|full|all|episode(s)?|film|movie|series)',
        '', i, flags=re.IGNORECASE) for i in gs]
    if not gs_parsed:
        reg = re.compile(r"watch(\s[a-zA-Z0-9_\s\-\(\)]*)*\|.*",
                         re.IGNORECASE)  # match something like Watch Niram | Amazon Prime
        for mv in g_s:
            match = reg.match(mv)
            if match:
                gs_parsed.append(match.group(1))
    user = msg.from_user.id if msg.from_user else 0
    movielist = []
    gs_parsed = list(dict.fromkeys(gs_parsed))  # removing duplicates https://stackoverflow.com/a/7961425
    if len(gs_parsed) > 3:
        gs_parsed = gs_parsed[:3]
    if gs_parsed:
        for mov in gs_parsed:
            imdb_s = await get_poster(mov.strip(), bulk=True)  # searching each keyword in imdb
            if imdb_s:
                movielist += [movie.get('title') for movie in imdb_s]
    movielist += [(re.sub(r'(\-|\(|\)|_)', '', i, flags=re.IGNORECASE)).strip() for i in gs_parsed]
    movielist = list(dict.fromkeys(movielist))  # removing duplicates
    if not movielist:
        one_button = InlineKeyboardMarkup([[InlineKeyboardButton("🥲 𝗢𝗪𝗡𝗘𝗥 🔥", url="https://t.me/TechnoKillerBot"), InlineKeyboardButton("🤕 𝗚𝗢𝗢𝗚𝗟𝗘 🤒", url="https://www.google.com/")]])
        k = await msg.reply_video(video="https://telegra.ph//file/d90256b1575c7aaadccc5.mp4", caption="Hey, 𝐒𝐨𝐫𝐫𝐲, 𝐍𝐨 𝐌𝐨𝐯𝐢𝐞/𝐒𝐞𝐫𝐢𝐞𝐬 𝐑𝐞𝐥𝐚𝐭𝐞𝐝 𝐓𝐨 𝐓𝐡𝐞 𝐆𝐢𝐯𝐞𝐧 𝐖𝐨𝐫𝐝 𝐖𝐚𝐬 𝐅𝐨𝐮𝐧𝐝 🥺\n\n𝙿𝚘𝚜𝚜𝚒𝚋𝚕𝚎 𝙲𝚊𝚞𝚜𝚎𝚜 : 🤔\n\n⭕️ 𝐍𝐨𝐭 𝐑𝐞𝐥𝐞𝐚𝐬𝐞𝐝 𝐘𝐞𝐭\n⭕️ 𝐈𝐧𝐜𝐨𝐫𝐫𝐞𝐜𝐭 𝐒𝐩𝐞𝐥𝐥𝐢𝐧𝐠\n⭕ 𝐍𝐨𝐭 𝐔𝐩𝐥𝐨𝐚𝐝𝐞𝐝 𝐁𝐲 𝐎𝐰𝐧𝐞𝐫\n\n👉Contact To My Owner👇", reply_markup = one_button)
        await asyncio.sleep(20)
        await k.delete()
        await msg.delete()
        return
    SPELL_CHECK[msg.id] = movielist
    btn = [[
        InlineKeyboardButton(
            text=movie.strip(),
            callback_data=f"spolling#{user}#{k}",
        )
    ] for k, movie in enumerate(movielist)]
    btn.append([InlineKeyboardButton(text="Close", callback_data=f'spolling#{user}#close_spellcheck')])
    one_button = InlineKeyboardMarkup([[InlineKeyboardButton("🥲 𝗢𝗪𝗡𝗘𝗥 🔥", url="https://t.me/TechnoKillerBot"), InlineKeyboardButton("🤕 𝗚𝗢𝗢𝗚𝗟𝗘 🤒", url="https://www.google.com/")]])
    k = await msg.reply_video(video="https://telegra.ph//file/d90256b1575c7aaadccc5.mp4", caption="Hey, 𝐒𝐨𝐫𝐫𝐲, 𝐍𝐨 𝐌𝐨𝐯𝐢𝐞/𝐒𝐞𝐫𝐢𝐞𝐬 𝐑𝐞𝐥𝐚𝐭𝐞𝐝 𝐓𝐨 𝐓𝐡𝐞 𝐆𝐢𝐯𝐞𝐧 𝐖𝐨𝐫𝐝 𝐖𝐚𝐬 𝐅𝐨𝐮𝐧𝐝 🥺\n\n𝙿𝚘𝚜𝚜𝚒𝚋𝚕𝚎 𝙲𝚊𝚞𝚜𝚎𝚜 : 🤔\n\n⭕️ 𝐍𝐨𝐭 𝐑𝐞𝐥𝐞𝐚𝐬𝐞𝐝 𝐘𝐞𝐭\n⭕️ 𝐈𝐧𝐜𝐨𝐫𝐫𝐞𝐜𝐭 𝐒𝐩𝐞𝐥𝐥𝐢𝐧𝐠\n⭕ 𝐍𝐨𝐭 𝐔𝐩𝐥𝐨𝐚𝐝𝐞𝐝 𝐁𝐲 𝐎𝐰𝐧𝐞𝐫\n\n👉Contact To My Owner👇", reply_markup = one_button)
    await asyncio.sleep(20)
    await k.delete()
    await msg.delete()


async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                    elif btn == "[]":
                        await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False

  #Techno Mindz
