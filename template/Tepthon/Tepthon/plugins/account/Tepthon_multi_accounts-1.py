# -*- coding: utf-8 -*-

"""
Tepthon Multi Accounts
======================

الأوامر:
.تنصيب
.تنصيب SESSION
.حسابات
.حذف حساب account1

مهم:
الحسابات الإضافية تعمل عبر Telethon مباشرة،
ولا يتم تشغيل python -m Tepthon للحساب الإضافي،
ولا يتم استيراد Tepthon داخل العملية الفرعية.

هذا يمنع تشغيل tgbot والحساب الأساسي مرة أخرى.
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from .. import JmdB, Tepthon_cmd, LOGS


# =========================================================
# إعدادات
# =========================================================

CHILD_FLAG = "TEPTHON_MULTI_ACCOUNT_CHILD"

ACCOUNTS_FILE = (
    Path("database")
    / "extra_accounts.json"
)

LOG_DIR = (
    Path("database")
    / "extra_accounts_logs"
)

ACCOUNTS_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

_children = {}


# =========================================================
# رسالة التحميل
# =========================================================

if os.getenv(CHILD_FLAG) != "1":

    try:

        LOGS.info(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

        LOGS.info(
            "✅ تم تحميل Tepthon_multi_accounts-1.py"
        )

        LOGS.info(
            "✅ Multi Accounts جاهز"
        )

        LOGS.info(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    except Exception:
        pass


# =========================================================
# الكود الرئيسي فقط
# =========================================================

if os.getenv(CHILD_FLAG) != "1":

    # =====================================================
    # قراءة الحسابات
    # =====================================================

    def _load_accounts():

        try:

            if not ACCOUNTS_FILE.exists():
                return {}

            data = json.loads(
                ACCOUNTS_FILE.read_text(
                    encoding="utf-8"
                )
            )

            if isinstance(data, dict):
                return data

        except Exception as exc:

            LOGS.error(
                f"❌ خطأ قراءة الحسابات: {exc}"
            )

        return {}


    # =====================================================
    # حفظ الحسابات
    # =====================================================

    def _save_accounts(data):

        ACCOUNTS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        temp = ACCOUNTS_FILE.with_suffix(
            ".tmp"
        )

        temp.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        temp.replace(
            ACCOUNTS_FILE
        )


    # =====================================================
    # المالك
    # =====================================================

    def _is_owner(event):

        try:

            owner = JmdB.get_key(
                "OWNER_ID"
            )

            if owner is None:
                return False

            return (
                int(owner)
                == int(event.sender_id)
            )

        except Exception:

            return False


    # =====================================================
    # API
    # =====================================================

    def _get_api():

        api_id = None
        api_hash = None

        # -------------------------------------------------
        # الطريقة الأولى:
        # Tepthon.config
        # -------------------------------------------------

        try:

            from Tepthon.config import Var

            api_id = getattr(
                Var,
                "API_ID",
                None
            )

            api_hash = getattr(
                Var,
                "API_HASH",
                None
            )

        except Exception as exc:

            LOGS.warning(
                f"⚠️ تعذر قراءة API من Tepthon.config: {exc}"
            )


        # -------------------------------------------------
        # الطريقة الثانية:
        # Environment
        # -------------------------------------------------

        if not api_id:

            api_id = os.getenv(
                "API_ID"
            )

        if not api_hash:

            api_hash = os.getenv(
                "API_HASH"
            )


        if not api_id:

            raise RuntimeError(
                "API_ID غير موجود"
            )

        if not api_hash:

            raise RuntimeError(
                "API_HASH غير موجود"
            )


        try:

            api_id = int(api_id)

        except Exception:

            raise RuntimeError(
                "API_ID غير صالح"
            )


        return (
            api_id,
            str(api_hash)
        )


    # =====================================================
    # التحقق من Session
    # =====================================================

    def _valid_session(session):

        session = (
            session or ""
        ).strip()

        if not session:
            return False

        # StringSession تبدأ غالبًا بـ 1
        # ولا نعتمد على طول ثابت لأن Telethon
        # قد تختلف إصداراته.

        if len(session) < 100:
            return False

        # منع المسافات والأسطر داخل Session
        if any(
            char.isspace()
            for char in session
        ):
            return False

        return True


    # =====================================================
    # Log
    # =====================================================

    def _log_path(name):

        return (
            LOG_DIR
            / f"{name}.log"
        )


    # =====================================================
    # كود الحساب الفرعي
    # =====================================================

    def _build_child_script():

        return r'''
# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import traceback

from telethon import TelegramClient
from telethon.sessions import StringSession


async def main():

    name = os.getenv(
        "TEPTHON_ACCOUNT_NAME",
        "account"
    )

    api_id_raw = os.getenv(
        "TEPTHON_API_ID",
        ""
    )

    api_hash = os.getenv(
        "TEPTHON_API_HASH",
        ""
    )

    session = os.getenv(
        "TEPTHON_SESSION",
        ""
    ).strip()


    print(
        "",
        flush=True
    )

    print(
        "==========================================",
        flush=True
    )

    print(
        f"🚀 [{name}] بدء تشغيل الحساب الإضافي",
        flush=True
    )

    print(
        "==========================================",
        flush=True
    )


    # =====================================================
    # التحقق
    # =====================================================

    if not api_id_raw:

        print(
            f"❌ [{name}] API_ID غير موجود",
            flush=True
        )

        return 10


    if not api_hash:

        print(
            f"❌ [{name}] API_HASH غير موجود",
            flush=True
        )

        return 11


    if not session:

        print(
            f"❌ [{name}] Session غير موجودة",
            flush=True
        )

        return 12


    try:

        api_id = int(
            api_id_raw
        )

    except Exception:

        print(
            f"❌ [{name}] API_ID غير صالح",
            flush=True
        )

        return 13


    # =====================================================
    # إنشاء Client مباشر
    # =====================================================

    try:

        print(
            f"🔌 [{name}] إنشاء Telethon Client...",
            flush=True
        )


        client = TelegramClient(
            StringSession(session),
            api_id,
            api_hash,

            device_model="Tepthon Multi Account",

            system_version="Linux",

            app_version="1.0.0",

            lang_code="ar",

            system_lang_code="ar"
        )


    except Exception as exc:

        print(
            f"❌ [{name}] فشل إنشاء Client",
            flush=True
        )

        print(
            f"{type(exc).__name__}: {exc}",
            flush=True
        )

        traceback.print_exc()

        return 20


    # =====================================================
    # الاتصال
    # =====================================================

    try:

        print(
            f"🔌 [{name}] جاري الاتصال بتليجرام...",
            flush=True
        )


        await client.connect()


        print(
            f"✅ [{name}] تم الاتصال",
            flush=True
        )


    except Exception as exc:

        print(
            f"❌ [{name}] فشل الاتصال",
            flush=True
        )

        print(
            f"{type(exc).__name__}: {exc}",
            flush=True
        )

        traceback.print_exc()

        try:
            await client.disconnect()
        except Exception:
            pass

        return 21


    # =====================================================
    # التحقق من Session
    # =====================================================

    try:

        authorized = (
            await client.is_user_authorized()
        )


        if not authorized:

            print(
                f"❌ [{name}] Session غير مصرح بها",
                flush=True
            )

            await client.disconnect()

            return 22


    except Exception as exc:

        print(
            f"❌ [{name}] فشل التحقق من Session",
            flush=True
        )

        print(
            f"{type(exc).__name__}: {exc}",
            flush=True
        )

        traceback.print_exc()

        try:
            await client.disconnect()
        except Exception:
            pass

        return 23


    # =====================================================
    # جلب الحساب
    # =====================================================

    try:

        me = await client.get_me()


        if not me:

            print(
                f"❌ [{name}] لم يتم العثور على الحساب",
                flush=True
            )

            await client.disconnect()

            return 24


        username = (
            f"@{me.username}"
            if me.username
            else "بدون username"
        )


        first_name = (
            me.first_name
            or ""
        )


        print(
            "",
            flush=True
        )

        print(
            "==========================================",
            flush=True
        )

        print(
            f"✅ [{name}] تم تسجيل الدخول بنجاح",
            flush=True
        )

        print(
            f"الاسم: {first_name}",
            flush=True
        )

        print(
            f"المعرف: {username}",
            flush=True
        )

        print(
            f"ID: {me.id}",
            flush=True
        )

        print(
            "==========================================",
            flush=True
        )


    except Exception as exc:

        print(
            f"❌ [{name}] فشل قراءة الحساب",
            flush=True
        )

        print(
            f"{type(exc).__name__}: {exc}",
            flush=True
        )

        traceback.print_exc()

        try:
            await client.disconnect()
        except Exception:
            pass

        return 25


    # =====================================================
    # نظام الحساب الإضافي
    # =====================================================

    print(
        "",
        flush=True
    )

    print(
        f"🟢 [{name}] الحساب الإضافي يعمل الآن",
        flush=True
    )

    print(
        f"🟢 [{name}] Telethon Client متصل",
        flush=True
    )


    # =====================================================
    # إبقاء الحساب متصل
    # =====================================================

    try:

        await client.run_until_disconnected()


    except KeyboardInterrupt:

        print(
            f"⚠️ [{name}] تم إيقاف الحساب",
            flush=True
        )


    except Exception as exc:

        print(
            f"❌ [{name}] توقف الحساب",
            flush=True
        )

        print(
            f"{type(exc).__name__}: {exc}",
            flush=True
        )

        traceback.print_exc()

        return 30


    finally:

        try:
            await client.disconnect()
        except Exception:
            pass


    return 0


# =====================================================
# التشغيل
# =====================================================

if __name__ == "__main__":

    try:

        code = asyncio.run(
            main()
        )

        sys.exit(
            code
        )

    except KeyboardInterrupt:

        sys.exit(0)

    except Exception as exc:

        print(
            "==========================================",
            flush=True
        )

        print(
            "❌ FATAL ERROR",
            flush=True
        )

        print(
            f"{type(exc).__name__}: {exc}",
            flush=True
        )

        print(
            "==========================================",
            flush=True
        )

        traceback.print_exc()

        sys.exit(99)
'''


    # =====================================================
    # تشغيل الحساب
    # =====================================================

    def _start_account(
        name,
        session
    ):

        api_id, api_hash = (
            _get_api()
        )


        env = os.environ.copy()


        # -------------------------------------------------
        # معلومات الحساب الإضافي
        # -------------------------------------------------

        env[
            "TEPTHON_API_ID"
        ] = str(api_id)


        env[
            "TEPTHON_API_HASH"
        ] = str(api_hash)


        env[
            "TEPTHON_SESSION"
        ] = session


        env[
            "TEPTHON_ACCOUNT_NAME"
        ] = name


        env[
            CHILD_FLAG
        ] = "1"


        # -------------------------------------------------
        # Log
        # -------------------------------------------------

        log_file = _log_path(
            name
        )


        log_handle = open(
            log_file,
            "a",
            encoding="utf-8",
            buffering=1
        )


        log_handle.write(
            "\n\n"
            "==========================================\n"
            f"START ACCOUNT: {name}\n"
            "==========================================\n"
        )


        try:

            proc = subprocess.Popen(

                [
                    sys.executable,
                    "-u",
                    "-c",
                    _build_child_script()
                ],

                cwd=os.getcwd(),

                env=env,

                stdin=subprocess.DEVNULL,

                stdout=log_handle,

                stderr=subprocess.STDOUT,

                start_new_session=True
            )


        except Exception:

            try:
                log_handle.close()
            except Exception:
                pass

            raise


        _children[name] = (
            proc,
            log_handle
        )


        LOGS.info(
            f"🚀 تم تشغيل {name}"
        )


        return proc


    # =====================================================
    # إيقاف الحساب
    # =====================================================

    def _stop_account(name):

        value = _children.pop(
            name,
            None
        )


        if not value:
            return


        proc, log_handle = value


        if proc.poll() is None:

            try:

                os.killpg(
                    proc.pid,
                    signal.SIGTERM
                )

            except Exception:

                try:
                    proc.terminate()
                except Exception:
                    pass


        try:
            log_handle.close()
        except Exception:
            pass


    # =====================================================
    # حالة الحساب
    # =====================================================

    def _child_state(name):

        value = _children.get(
            name
        )


        if not value:

            return "🟡 محفوظ"


        proc = value[0]

        code = proc.poll()


        if code is None:

            return "🟢 العملية تعمل"


        return (
            f"🔴 متوقف (exit={code})"
        )


    # =====================================================
    # طلب Session
    # =====================================================

    async def _ask_for_session(event):

        future = (
            event.client.loop.create_future()
        )


        async def receive(
            reply_event
        ):

            if (
                reply_event.sender_id
                != event.sender_id
            ):
                return


            if (
                reply_event.chat_id
                != event.chat_id
            ):
                return


            text = (
                reply_event.raw_text
                or ""
            ).strip()


            if not future.done():

                future.set_result(
                    (
                        text,
                        reply_event
                    )
                )


        event.client.add_event_handler(
            receive,

            events.NewMessage(
                chats=event.chat_id,
                from_users=event.sender_id
            )
        )


        try:

            await event.eor(
                "**⎆ أرسل Session String للحساب الجديد الآن.**\n\n"
                "بعد الإرسال سيتم تشغيل الحساب مباشرة.\n\n"
                "⚠️ استخدم Session لحساب تملكه فقط."
            )


            text, reply_event = (
                await asyncio.wait_for(
                    future,
                    timeout=120
                )
            )


            try:
                await reply_event.delete()
            except Exception:
                pass


            return text


        except asyncio.TimeoutError:

            return None


        finally:

            event.client.remove_event_handler(
                receive
            )


    # =====================================================
    # تنصيب
    # =====================================================

    @Tepthon_cmd(
        pattern=r"تنصيب(?:\s+([\s\S]+))?$"
    )
    async def install_account(event):

        if not _is_owner(event):
            return


        session = (
            event.pattern_match.group(1)
            or ""
        ).strip()


        if not session:

            session = await _ask_for_session(
                event
            )


        if not session:

            return await event.eor(
                "**⎆ انتهى وقت انتظار الـSession ❌**"
            )


        if not _valid_session(
            session
        ):

            return await event.eor(
                "**⎆ الـSession غير صحيحة ❌**"
            )


        accounts = _load_accounts()


        # =================================================
        # منع التكرار
        # =================================================

        for item in accounts.values():

            if not isinstance(
                item,
                dict
            ):
                continue


            if (
                item.get("session")
                == session
            ):

                return await event.eor(
                    "**⎆ هذا الحساب مثبت مسبقاً.**"
                )


        # =================================================
        # اسم الحساب
        # =================================================

        index = 1

        while (
            f"account{index}"
            in accounts
        ):

            index += 1


        name = (
            f"account{index}"
        )


        # =================================================
        # حفظ
        # =================================================

        accounts[name] = {
            "session": session
        }


        _save_accounts(
            accounts
        )


        status = await event.eor(
            f"**⎆ جاري تشغيل `{name}` 🚀**\n\n"
            "⏳ جاري الاتصال بالحساب..."
        )


        try:

            proc = _start_account(
                name,
                session
            )


            # -------------------------------------------------
            # انتظار 20 ثانية لمعرفة هل العملية انهارت
            # -------------------------------------------------

            for _ in range(20):

                await asyncio.sleep(
                    1
                )


                if proc.poll() is not None:

                    break


            code = proc.poll()


            if code is not None:

                return await status.edit(
                    f"**⎆ `{name}` توقف ❌**\n\n"
                    f"Exit: `{code}`\n\n"
                    f"📄 Log:\n"
                    f"`{_log_path(name)}`"
                )


            return await status.edit(
                f"**⎆ `{name}` يعمل الآن 🟢**\n\n"
                "تم الاتصال بالحساب الإضافي بنجاح.\n\n"
                f"📄 Log:\n"
                f"`{_log_path(name)}`"
            )


        except Exception as exc:

            _stop_account(
                name
            )


            accounts.pop(
                name,
                None
            )


            _save_accounts(
                accounts
            )


            return await status.edit(
                "**⎆ فشل تشغيل الحساب ❌**\n\n"
                f"النوع: `{type(exc).__name__}`\n"
                f"الخطأ: `{exc}`"
            )


    # =====================================================
    # الحسابات
    # =====================================================

    @Tepthon_cmd(
        pattern=r"حسابات$"
    )
    async def list_accounts(event):

        if not _is_owner(event):
            return


        accounts = _load_accounts()


        if not accounts:

            return await event.eor(
                "**⎆ لا توجد حسابات إضافية.**"
            )


        lines = [
            "**⎆ الحسابات الإضافية:**",
            ""
        ]


        for name in accounts:

            lines.append(
                f"• `{name}` — "
                f"{_child_state(name)}"
            )


        await event.eor(
            "\n".join(lines)
        )


    # =====================================================
    # حذف الحساب
    # =====================================================

    @Tepthon_cmd(
        pattern=r"حذف حساب(?:\s+(\S+))?$"
    )
    async def remove_account(event):

        if not _is_owner(event):
            return


        name = (
            event.pattern_match.group(1)
            or ""
        ).strip()


        accounts = _load_accounts()


        if (
            not name
            or name not in accounts
        ):

            return await event.eor(
                "**⎆ الاستخدام:**\n"
                "`.حذف حساب account1`"
            )


        _stop_account(
            name
        )


        accounts.pop(
            name,
            None
        )


        _save_accounts(
            accounts
        )


        await event.eor(
            f"**⎆ تم حذف `{name}` وإيقافه ✅**"
        )


    # =====================================================
    # التشغيل التلقائي
    # =====================================================

    async def _auto_start():

        await asyncio.sleep(
            10
        )


        LOGS.info(
            "🔄 بدء فحص الحسابات الإضافية..."
        )


        accounts = _load_accounts()


        for name, data in list(
            accounts.items()
        ):


            if not isinstance(
                data,
                dict
            ):
                continue


            session = data.get(
                "session"
            )


            if not session:
                continue


            if name in _children:
                continue


            if not _valid_session(
                session
            ):

                LOGS.error(
                    f"❌ Session غير صالحة للحساب {name}"
                )

                continue


            try:

                LOGS.info(
                    f"🚀 تشغيل الحساب المحفوظ: {name}"
                )


                proc = _start_account(
                    name,
                    session
                )


                await asyncio.sleep(
                    5
                )


                if proc.poll() is None:

                    LOGS.info(
                        f"🟢 الحساب {name} يعمل"
                    )

                else:

                    LOGS.error(
                        f"❌ الحساب {name} توقف "
                        f"(exit={proc.poll()})"
                    )


            except Exception as exc:

                LOGS.error(
                    f"❌ فشل تشغيل {name}: {exc}"
                )


        LOGS.info(
            "✅ انتهى فحص الحسابات الإضافية"
        )


    # =====================================================
    # مراقبة الحسابات
    # =====================================================

    async def _monitor():

        while True:

            await asyncio.sleep(
                30
            )


            for name, value in list(
                _children.items()
            ):


                proc, log_handle = value

                code = proc.poll()


                if code is None:
                    continue


                LOGS.warning(
                    f"⚠️ الحساب {name} توقف "
                    f"(exit={code})"
                )


                try:
                    log_handle.close()
                except Exception:
                    pass


                _children.pop(
                    name,
                    None
                )


    # =====================================================
    # تشغيل النظام
    # =====================================================

    try:

        loop = asyncio.get_event_loop()


        loop.create_task(
            _auto_start()
        )


        loop.create_task(
            _monitor()
        )


        LOGS.info(
            "✅ تم تشغيل نظام الحسابات الإضافية"
        )


    except Exception as exc:

        LOGS.error(
            f"❌ فشل تشغيل نظام الحسابات الإضافية: {exc}"
        )
