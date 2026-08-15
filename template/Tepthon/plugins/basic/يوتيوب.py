"""
◙ `{i}يوت` <اسم المقطع>

مثال:
.يوت سورة الكهف
.يوت احبك

يتم البحث عن المقطع عبر:
@lN_3_Obot

ثم إرسال الصوت مباشرة.

حقوق:
@SSSTlF
"""

import asyncio

from .. import Tepthon_cmd, LOGS


# =========================================================
# بوت البحث
# =========================================================

SEARCH_BOT = "@lN_3_Obot"


# =========================================================
# حقوق السورس
# =========================================================

OWNER_USERNAME = "@SSSTlF"
OWNER_URL = "https://t.me/SSSTlF"


# =========================================================
# أمر البحث
#
# .يوت سورة الكهف
# =========================================================

@Tepthon_cmd(pattern=r"يوت(?:\s+(.+))?$")
async def youtube_search(event):

    query = (
        event.pattern_match.group(1)
        or ""
    ).strip()

    # =====================================================
    # التحقق من وجود بحث
    # =====================================================

    if not query:

        return await event.eor(
            "<b>╭─「 يــوت 」─╮</b>\n\n"
            "<b>اكتب اسم المقطع بعد الأمر</b>\n\n"
            "<b>مثال:</b>\n"
            "<b>.يوت سورة الكهف</b>\n"
            "<b>.يوت احبك</b>\n\n"
            f'<b>╰─ <a href="{OWNER_URL}">{OWNER_USERNAME}</a> ─╯</b>',
            parse_mode="html"
        )

    # =====================================================
    # رسالة البحث
    # =====================================================

    status = await event.eor(
        "<b>╭─「 يــوت 」─╮</b>\n\n"
        "<b>⌕ جاري البحث عن المقطع</b>\n\n"
        f"<b>♪ {query}</b>\n\n"
        "<b>⏳ انتظر قليلًا...</b>\n\n"
        f'<b>╰─ <a href="{OWNER_URL}">{OWNER_USERNAME}</a> ─╯</b>',
        parse_mode="html"
    )

    sent = None

    try:

        # =================================================
        # الحصول على بوت البحث
        # =================================================

        bot = await event.client.get_entity(
            SEARCH_BOT
        )

        # =================================================
        # إرسال البحث للبوت
        # =================================================

        sent = await event.client.send_message(
            bot,
            f"بحث {query}"
        )

        # =================================================
        # انتظار الصوت
        # =================================================

        audio_message = None

        for _ in range(40):

            await asyncio.sleep(1)

            messages = await event.client.get_messages(
                bot,
                limit=10
            )

            for message in messages:

                # تجاهل رسالة البحث
                if sent and message.id == sent.id:
                    continue

                # =================================================
                # رسالة صوت
                # =================================================

                if message.audio:

                    audio_message = message
                    break

                # =================================================
                # ملف صوتي
                # =================================================

                if (
                    message.document
                    and message.file
                    and message.file.mime_type
                    and message.file.mime_type.startswith(
                        "audio/"
                    )
                ):

                    audio_message = message
                    break

            if audio_message:
                break

        # =====================================================
        # إذا لم يصل الصوت
        # =====================================================

        if not audio_message:

            return await status.eor(
                "<b>╭─「 يــوت 」─╮</b>\n\n"
                "<b>❌ لم يتم العثور على المقطع</b>\n\n"
                "<b>حاول كتابة اسم الأغنية بشكل أوضح.</b>\n\n"
                f'<b>╰─ <a href="{OWNER_URL}">{OWNER_USERNAME}</a> ─╯</b>',
                parse_mode="html"
            )

        # =====================================================
        # إرسال الصوت للمستخدم
        # =====================================================

        await event.client.send_file(
            event.chat_id,
            audio_message.media,
            caption=(
                "<b>🎵 تم العثور على المقطع</b>\n\n"
                f"<b>♪ {query}</b>\n\n"
                f'<b>© <a href="{OWNER_URL}">{OWNER_USERNAME}</a></b>'
            ),
            parse_mode="html",
            voice_note=False,
            supports_streaming=True,
        )

        # =====================================================
        # حذف رسالة "جاري البحث"
        # بعد نجاح إرسال الصوت
        # =====================================================

        try:
            await status.delete()
        except BaseException:
            pass

        # =====================================================
        # حذف رسالة البحث من الخاص
        # =====================================================

        if sent:

            try:
                await event.client.delete_messages(
                    bot,
                    sent.id
                )
            except BaseException:
                pass

    except Exception as er:

        LOGS.exception(er)

        try:

            await status.eor(
                "<b>╭─「 يــوت 」─╮</b>\n\n"
                "<b>❌ حدث خطأ أثناء البحث</b>\n\n"
                f"<b><code>{er}</code></b>\n\n"
                f'<b>╰─ <a href="{OWNER_URL}">{OWNER_USERNAME}</a> ─╯</b>',
                parse_mode="html"
            )

        except BaseException:

            pass
