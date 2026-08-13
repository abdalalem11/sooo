import asyncio
import time
from datetime import datetime

from telethon import TelegramClient, events, Button

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    OWNER_ID,
    ACCOUNTS_DIR,
    TEMPLATE_DIR,
    DB_PATH,
    ALLOW_USERS,
    DEFAULT_DAYS,
    MAX_DAYS,
)

from database import Database
from manager.sessions import SessionManager
from manager.processes import ProcessManager


bot = TelegramClient(
    "data/factory_bot",
    API_ID,
    API_HASH
)

db = Database(DB_PATH)
sessions = SessionManager(ACCOUNTS_DIR)
processes = ProcessManager(
    ACCOUNTS_DIR,
    TEMPLATE_DIR
)

states = {}


def is_owner(user_id):
    return user_id == OWNER_ID


def menu():
    buttons = [
        [
            Button.inline("➕ تنصيب", b"install"),
            Button.inline("📋 تنصيباتي", b"my")
        ]
    ]

    if is_owner(OWNER_ID):
        buttons.append([
            Button.inline("👨‍💻 لوحة المطور", b"admin")
        ])

    return buttons


def admin_menu():
    return [
        [
            Button.inline("📋 كل التنصيبات", b"admin_list")
        ],
        [
            Button.inline("🎁 منح مجاني", b"admin_free"),
            Button.inline("♾️ غير محدود", b"admin_unlimited")
        ],
        [
            Button.inline("▶️ تشغيل", b"admin_start"),
            Button.inline("⛔ إيقاف", b"admin_stop")
        ],
    ]


@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    if not ALLOW_USERS and not is_owner(event.sender_id):
        await event.reply("❌ المصنع مغلق.")
        return

    await event.reply(
        "🤖 <b>MSNA Tepthon Factory</b>\n\n"
        "اختر العملية:",
        buttons=menu(),
        parse_mode="html"
    )


@bot.on(events.CallbackQuery(data=b"install"))
async def install(event):
    if not ALLOW_USERS and not is_owner(event.sender_id):
        await event.answer("المصنع مغلق.", alert=True)
        return

    states[event.sender_id] = {
        "step": "name"
    }

    await event.edit(
        "➕ <b>تنصيب جديد</b>\n\n"
        "أرسل اسم النسخة:",
        parse_mode="html"
    )


@bot.on(events.CallbackQuery(data=b"my"))
async def my_installs(event):
    rows = db.user(event.sender_id)

    if not rows:
        await event.answer(
            "لا توجد تنصيبات.",
            alert=True
        )
        return

    text = "📋 <b>تنصيباتك:</b>\n\n"

    for row in rows:
        if row["unlimited"]:
            expiry = "♾️ غير محدود"
        elif row["expires_at"]:
            expiry = datetime.fromtimestamp(
                row["expires_at"]
            ).strftime("%Y-%m-%d")
        else:
            expiry = "غير محدد"

        text += (
            f"#{row['id']} — {row['name']}\n"
            f"الحالة: {row['status']}\n"
            f"الانتهاء: {expiry}\n\n"
        )

    await event.edit(
        text,
        parse_mode="html"
    )


@bot.on(events.CallbackQuery(data=b"admin"))
async def admin(event):
    if not is_owner(event.sender_id):
        await event.answer(
            "للمطور فقط.",
            alert=True
        )
        return

    await event.edit(
        "👨‍💻 <b>لوحة المطور</b>\n\n"
        "اختر العملية:",
        buttons=admin_menu(),
        parse_mode="html"
    )


@bot.on(events.CallbackQuery(data=b"admin_list"))
async def admin_list(event):
    if not is_owner(event.sender_id):
        return

    rows = db.all()

    if not rows:
        await event.answer(
            "لا توجد تنصيبات.",
            alert=True
        )
        return

    text = "📋 <b>كل التنصيبات:</b>\n\n"

    for r in rows:
        text += (
            f"#{r['id']} | "
            f"{r['name']} | "
            f"user={r['user_id']} | "
            f"{r['status']}\n"
        )

    await event.edit(
        text,
        parse_mode="html"
    )


@bot.on(events.CallbackQuery(data=b"admin_free"))
async def admin_free(event):
    if not is_owner(event.sender_id):
        return

    states[event.sender_id] = {
        "step": "free_user"
    }

    await event.edit(
        "🎁 أرسل Telegram User ID للشخص الذي تريد فتح "
        "التنصيب له مجانًا."
    )


@bot.on(events.CallbackQuery(data=b"admin_unlimited"))
async def admin_unlimited(event):
    if not is_owner(event.sender_id):
        return

    states[event.sender_id] = {
        "step": "unlimited_install"
    }

    await event.edit(
        "♾️ أرسل رقم التنصيب INSTALL ID."
    )


@bot.on(events.CallbackQuery(data=b"admin_start"))
async def admin_start(event):
    if not is_owner(event.sender_id):
        return

    states[event.sender_id] = {
        "step": "start_install"
    }

    await event.edit(
        "▶️ أرسل INSTALL ID للتشغيل."
    )


@bot.on(events.CallbackQuery(data=b"admin_stop"))
async def admin_stop(event):
    if not is_owner(event.sender_id):
        return

    states[event.sender_id] = {
        "step": "stop_install"
    }

    await event.edit(
        "⛔ أرسل INSTALL ID للإيقاف."
    )


@bot.on(events.NewMessage)
async def messages(event):
    if not event.is_private:
        return

    if event.raw_text.startswith("/"):
        return

    uid = event.sender_id

    if uid not in states:
        return

    state = states[uid]
    step = state["step"]
    text = event.raw_text.strip()

    # اسم التنصيب
    if step == "name":
        state["name"] = text

        await event.reply(
            "اختر طريقة تسجيل الحساب:",
            buttons=[
                [
                    Button.inline(
                        "📱 رقم الهاتف",
                        b"login_phone"
                    )
                ],
                [
                    Button.inline(
                        "🔑 Session String",
                        b"login_session"
                    )
                ]
            ]
        )

        state["step"] = "method"
        return

    # رقم الهاتف
    if step == "phone":
        state["phone"] = text

        try:
            await sessions.send_code(
                text,
                API_ID,
                API_HASH
            )

            state["step"] = "code"

            await event.reply(
                "📩 تم إرسال كود Telegram.\n"
                "أرسله هنا."
            )

        except Exception as e:
            await event.reply(
                f"❌ فشل إرسال الكود:\n{e}"
            )

        return

    # كود Telegram
    if step == "code":
        state["code"] = text
        state["step"] = "password"

        await event.reply(
            "إذا كان الحساب محميًا بـ 2FA، "
            "أرسل كلمة المرور.\n\n"
            "إذا لا يوجد 2FA أرسل:\n"
            "<code>لا</code>",
            parse_mode="html"
        )

        return

    # 2FA
    if step == "password":
        password = None if text == "لا" else text

        try:
            iid = await create_install(
                uid,
                state["name"]
            )

            path = await sessions.login_code(
                iid,
                state["phone"],
                state["code"],
                API_ID,
                API_HASH,
                password
            )

            db.session(
                iid,
                path,
                state["phone"]
            )

            pid = processes.start(iid)

            db.status(iid, "running")

            await event.reply(
                f"✅ <b>تم التنصيب</b>\n\n"
                f"ID: <code>{iid}</code>\n"
                f"PID: <code>{pid}</code>",
                parse_mode="html"
            )

            states.pop(uid, None)

        except Exception as e:
            await event.reply(
                f"❌ فشل التنصيب:\n{e}"
            )

        return

    # Session String
    if step == "session":
        try:
            iid = await create_install(
                uid,
                state["name"]
            )

            path = await sessions.from_string(
                iid,
                text,
                API_ID,
                API_HASH
            )

            db.session(iid, path)

            pid = processes.start(iid)

            db.status(iid, "running")

            await event.reply(
                f"✅ <b>تم التنصيب</b>\n\n"
                f"ID: <code>{iid}</code>\n"
                f"PID: <code>{pid}</code>",
                parse_mode="html"
            )

            states.pop(uid, None)

        except Exception as e:
            await event.reply(
                f"❌ فشل التنصيب:\n{e}"
            )

        return

    # المطور يمنح مستخدمًا صلاحية مجانية
    if step == "free_user":
        if not is_owner(uid):
            return

        try:
            target = int(text)

            # سجل صلاحية مجانية دائمة.
            iid = db.create(
                target,
                "free-access",
                unlimited=True
            )

            await event.reply(
                f"🎁 تم فتح تنصيب مجاني للمستخدم:\n"
                f"<code>{target}</code>\n\n"
                f"Install ID: <code>{iid}</code>\n"
                f"المدة: ♾️ غير محدود",
                parse_mode="html"
            )

            states.pop(uid, None)

        except ValueError:
            await event.reply("أرسل User ID صحيح.")

        return

    # المطور يجعل تنصيبًا غير محدود
    if step == "unlimited_install":
        if not is_owner(uid):
            return

        try:
            iid = int(text)

            if not db.get(iid):
                await event.reply("❌ التنصيب غير موجود.")
                return

            db.unlimited(iid)

            await event.reply(
                f"♾️ تم جعل التنصيب #{iid} "
                "غير محدود."
            )

            states.pop(uid, None)

        except ValueError:
            await event.reply("أرسل INSTALL ID صحيح.")

        return

    if step == "start_install":
        if not is_owner(uid):
            return

        try:
            iid = int(text)
            row = db.get(iid)

            if not row:
                await event.reply("❌ غير موجود.")
                return

            pid = processes.start(iid)
            db.status(iid, "running")

            await event.reply(
                f"▶️ تم التشغيل.\nPID: {pid}"
            )

            states.pop(uid, None)

        except Exception as e:
            await event.reply(f"❌ {e}")

        return

    if step == "stop_install":
        if not is_owner(uid):
            return

        try:
            iid = int(text)

            processes.stop(iid)
            db.status(iid, "stopped")

            await event.reply(
                f"⛔ تم إيقاف #{iid}"
            )

            states.pop(uid, None)

        except Exception as e:
            await event.reply(f"❌ {e}")


@bot.on(events.CallbackQuery(data=b"login_phone"))
async def login_phone(event):
    uid = event.sender_id

    if uid not in states:
        return

    states[uid]["step"] = "phone"

    await event.edit(
        "📱 أرسل رقم الهاتف بصيغة دولية.\n\n"
        "مثال:\n"
        "<code>+9665xxxxxxxx</code>",
        parse_mode="html"
    )


@bot.on(events.CallbackQuery(data=b"login_session"))
async def login_session(event):
    uid = event.sender_id

    if uid not in states:
        return

    states[uid]["step"] = "session"

    await event.edit(
        "🔑 أرسل Session String."
    )


async def create_install(user_id, name):
    # افتراضيًا تنصيب المستخدم يكون بالمدة المحددة.
    # التنصيبات التي يفتحها المطور تكون غير محدودة.
    expires = time.time() + DEFAULT_DAYS * 86400

    iid = db.create(
        user_id,
        name,
        expires_at=expires,
        unlimited=False
    )

    processes.create(iid)

    return iid


async def expiry_worker():
    while True:
        now = time.time()

        for row in db.all():

            if row["unlimited"]:
                continue

            if (
                row["expires_at"]
                and row["expires_at"] <= now
                and row["status"] == "running"
            ):
                processes.stop(row["id"])
                db.status(
                    row["id"],
                    "expired"
                )

        await asyncio.sleep(60)


async def main():
    await bot.start(
        bot_token=BOT_TOKEN
    )

    print("=" * 40)
    print("MSNA Factory started")
    print("Telethon:", __import__("telethon").__version__)
    print("=" * 40)

    asyncio.create_task(expiry_worker())

    await bot.run_until_disconnected()
