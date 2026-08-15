import asyncio
import sys
from random import randint

from telethon.errors import (
    ChannelsTooMuchError,
    ChatAdminRequiredError,
    UserNotParticipantError,
)

from telethon.tl.functions.channels import (
    CreateChannelRequest,
    EditAdminRequest,
    EditPhotoRequest,
    InviteToChannelRequest,
)
from telethon.tl.functions.contacts import UnblockRequest
from telethon import Button
from telethon.tl.types import (
    ChatAdminRights,
    ChatPhotoEmpty,
    InputChatUploadedPhoto
)
from telethon.utils import get_peer_id
from Tepthon.helper import inline_mention#, check_update
from Tepthon import LOGS

async def inline_on():
    from .. import tgbot, JmdB, jmubot

    try:
        username = tgbot.me.username
        if not username:
            LOGS.error("❌ البوت المساعد لا يملك username.")
            return

        bot = "BotFather"

        # تفعيل Inline تلقائيًا عند كل تشغيل/تنصيب
        await jmubot.send_message(bot, "/setinline")
        await asyncio.sleep(2)

        await jmubot.send_message(bot, f"@{username}")
        await asyncio.sleep(2)

        await jmubot.send_message(bot, "Search")
        await asyncio.sleep(2)

        await jmubot.send_read_acknowledge(bot)

        JmdB.set_key("INLINE_SET", True)
        LOGS.info(f"✅ تم طلب تفعيل Inline للبوت @{username}")

    except Exception as er:
        LOGS.error(f"❌ فشل تفعيل Inline للبوت: {er}")

async def notify():
    from .. import tgbot, JmdB, jmubot
    chat_id = JmdB.get_key("LOG_CHAT")
    spam_sent, BTTS = None, None
    
    if not JmdB.get_key("FIRST_DEPLOY"):
        MSG = f"🎇 **مرحبًا بك في سورس النسرالاسود اكتمل التنصيب بنجاح** \n\n✨ **استعد لاستكشاف الميزات الجديدة!**  \n💭 إليك بعض الخيارات التي ستساعدك في التعرف على سورس تيبثون واستخدامه بفعالية:  \n   - تعلم كيفية استخدام الأوامر الأساسية.  \n   - استكشاف الوظائف المختلفة المتاحة.  \n   - الانضمام إلى مجموعة الدعم للحصول على المساعدة والتوجيه.  \n\n📩 نحن هنا لدعمك، فلا تتردد في طرح أي سؤال أو استفسار!"
        PHOTO = "resources/Tepthon.jpg"
        BTTS = Button.inline("◙ اضغط هنـا للبدأ ◙", "initft_2")
        JmdB.set_key("FIRST_DEPLOY", True)
    else:
        MSG = f"🌟 تنصيب سورس النسرالاسود اكتمل بنجاح! ☑️\n\n👤 **حساب المالك:** {inline_mention(jmubot.me)}\n🤖 **البوت المساعد:** @{tgbot.me.username}\n\n📩 نرحب بك في مجموعتنا! إذا كان لديك أي استفسارات فلا تتردد في السؤال!\n💬 **مجموعة المساعدة:** @SSSTlFd"
        BTTS, PHOTO = None, None

        if prev_spam := JmdB.get_key("LAST_UPDATE_LOG_SPAM"):
            try:
                await tgbot.delete_messages(chat_id, int(prev_spam))
            except Exception:
                pass
    try:
        spam_sent = await tgbot.send_message(chat_id, MSG, file=PHOTO, buttons=BTTS)
    except Exception as el:
        LOGS.exception(el)
        try:
            spam_sent = await jmubot.send_message(chat_id, MSG)
        except Exception as ef:
            LOGS.exception(ef)
    if spam_sent:
        JmdB.set_key("LAST_UPDATE_LOG_SPAM", spam_sent.id)


async def group_ub():
    from .. import tgbot, jmdB, jmubot

    log_chat = jmdB.get_key("LOG_CHAT")
    new_channel = None
    if log_chat:
        try:
            chat = await jmubot.get_entity(log_chat)
        except BaseException as err:
            LOGS.exception(err)
            jmdB.del_key("LOG_CHAT")
            log_chat = None
    if not log_chat:
        async def _save(exc):
            jmdB._cache["LOG_CHAT"] = jmubot.me.id
            await tgbot.send_message(
                jmubot.me.id, f"حدث خطأ في إنشاء مجموعة الحفظ الخطأ: {exc}.\n حاليًّا الرسائل المحفوظة هي بديل مجموعة الحفظ."
            )
        LOGS.info("⎆ جــاري صنع مجموعـة الحفـظ انتظر 🧸♥️...")
        try:
            group_id = await jmubot(
                CreateChannelRequest(
                    title="مجموعـة الحفـظ - النسر الاسود ",
                    about="- هذه هي مجموعـة حفظ الأحـداث والسجلات التي قد تتلقاها- @SSSTlFd .",
                    megagroup=True,
                ),
            )
        except ChannelsTooMuchError as er:
            LOGS.critical(
                "⎆ لديـك العديـد من القنوات والمجموعات قم بتصفية حسابك من عدد قليل من القنوات والمجموعات ثم عد.."
            )
            return await _save(str(er))
        except BaseException as er:
            LOGS.exception(er)
            LOGS.info(
                "لقد حدث خطأ ما يرجى صنع مجموعة و وضع الأيدي الخاص بها مع المتغير LOG_CHAT."
            )

            return await _save(str(er))
        new_channel = True
        chat = group_id.chats[0]
        log_chat = get_peer_id(chat)
        jmdB.set_key("LOG_CHAT", log_chat)
    assistant = True
    try:
        await jmubot.get_permissions(int(log_chat), tgbot.me.username)
    except UserNotParticipantError:
        try:
            await jmubot(InviteToChannelRequest(int(log_chat), [tgbot.me.username]))
        except BaseException as er:
            LOGS.info("حدث خطأ في إضافة البوت المساعد ...!!!")
            LOGS.exception(er)
            assistant = False
    except BaseException as er:
        assistant = False
        LOGS.exception(er)
    if assistant and new_channel:
        try:
            achat = await tgbot.get_entity(int(log_chat))
        except BaseException as er:
            achat = None
            LOGS.info("حدث خطـأ: لم يتعرف البوت المساعد على مجموعة الحفظ...")
            LOGS.exception(er)
        if achat and not achat.admin_rights:
            rights = ChatAdminRights(
                add_admins=True,
                invite_users=True,
                change_info=True,
                ban_users=True,
                delete_messages=True,
                pin_messages=True,
                anonymous=False,
                manage_call=True,
            )
            try:
                await jmubot(
                    EditAdminRequest(
                        int(log_chat), tgbot.me.username, rights, "البوت المساعد"
                    )
                )
            except ChatAdminRequiredError:
                LOGS.info(
                    "خطأ: تعذر رفع البوت المساعد مشرف ....'"
                )
            except BaseException as er:
                LOGS.info("لقد حدث خطأ أثناء رفع البوت المساعد في مجموعة الحفظ..")
                LOGS.exception(er)
    if isinstance(chat.photo, ChatPhotoEmpty):
        pic = await jmubot.upload_file(file="resources/Tepthon.jpg")
        try:
            await jmubot(EditPhotoRequest(int(log_chat), pic))
        except BaseException as er:
            LOGS.exception(er)



async def tag_chat():
    from .. import tgbot, jmdB, jmubot

    tag_chat = jmdB.get_key("TAG_CHAT")
    new_tag = None
    if tag_chat:
        try:
            chat = await jmubot.get_entity(tag_chat)
        except BaseException as err:
            LOGS.exception(err)
            jmdB.del_key("TAG_CHAT")
            tag_chat = None
    if not tag_chat:
        LOGS.info("جـاري صنع مجموعة التخزين يرجى الانتظار ...")
        try:
            group_id = await jmubot(
                CreateChannelRequest(
                    title="مجموعة التخزين - النسر الاسود ",
                    about="مجموعة تخزين الرسائل الخاصة بك\n\n انضم لقناة السورس @SSSTlFd",
                    megagroup=True,
                ),
            )
        except ChannelsTooMuchError as er:
            LOGS.critical(
                "لديك العديد من القنوات والمجموعات غادر منها وأعد تشغيل السورس"
            )
        except BaseException as er:
            LOGS.exception(er)
            LOGS.info(
                "لقد حدث خطأ ما يرجى صنع مجموعة و وضع الأيدي الخاص بها مع المتغير TAG_CHAT."
            )

        new_tag = True
        chat = group_id.chats[0]
        tag_chat = get_peer_id(chat)
        jmdB.set_key("TAG_CHAT", tag_chat)
    assistant = True
    try:
        await jmubot.get_permissions(int(tag_chat), tgbot.me.username)
    except UserNotParticipantError:
        try:
            await jmubot(InviteToChannelRequest(int(tag_chat), [tgbot.me.username]))
        except BaseException as er:
            LOGS.info("حدث خطـأ: تعذر إضافة البوت المساعد إلى المجموعة")
            LOGS.exception(er)
            assistant = False
    except BaseException as er:
        assistant = False
        LOGS.exception(er)
    if assistant and new_tag:
        try:
            achat = await tgbot.get_entity(int(tag_chat))
        except BaseException as er:
            achat = None
            LOGS.info("حدث خطـأ: لم يتعرف البوت المساعد على المجموعة")
            LOGS.exception(er)
        if achat and not achat.admin_rights:
            rights = ChatAdminRights(
                add_admins=True,
                invite_users=True,
                change_info=True,
                ban_users=True,
                delete_messages=True,
                pin_messages=True,
                anonymous=False,
                manage_call=True,
            )
            try:
                await jmubot(
                    EditAdminRequest(
                        int(tag_chat), tgbot.me.username, rights, "البوت المساعد"
                    )
                )
            except ChatAdminRequiredError:
                LOGS.info(
                    "تعذر رفع البوت المساعد مشرفًا يبدو أنه ليست لديك الصلاحيات الكافية'"
                )
            except BaseException as er:
                LOGS.info("لقد حدث خطأ أثناء رفع البوت المساعد في مجموعة التخزين..")
                LOGS.exception(er)
    if isinstance(chat.photo, ChatPhotoEmpty):
        pic = await jmubot.upload_file(file="resources/Tepthon.jpg")
        try:
            await jmubot(EditPhotoRequest(int(tag_chat), pic))
        except BaseException as er:
            LOGS.exception(er)


async def main_process():
    await inline_on()
    await group_ub()
    await tag_chat()
    await notify()
