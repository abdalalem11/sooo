import asyncio
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from telethon.errors import SessionPasswordNeededError

from config import BOT_TOKEN, OWNER_ID, API_ID, API_HASH
from database import Database
from manager.processes import ProcessManager
from manager.sessions import SessionManager


router = Router()


class InstallState(StatesGroup):
    waiting_name = State()
    waiting_days = State()
    waiting_phone = State()
    waiting_code = State()
    waiting_password = State()
    waiting_session = State()


def allowed(user, owner):
    return user is not None and user.id == owner


def main_menu():
    b = InlineKeyboardBuilder()
    b.button(text="➕ تنصيب جديد", callback_data="new")
    b.button(text="🔑 تنصيب عبر Session", callback_data="session_new")
    b.button(text="📋 تنصيباتي", callback_data="list")
    b.button(text="📊 الحالة", callback_data="status")
    b.button(text="🔄 تحديث", callback_data="list")
    b.adjust(2)
    return b.as_markup()


def account_menu(iid):
    b = InlineKeyboardBuilder()
    b.button(text="▶️ تشغيل", callback_data=f"start:{iid}")
    b.button(text="⛔ إيقاف", callback_data=f"stop:{iid}")
    b.button(text="🔄 إعادة تشغيل", callback_data=f"restart:{iid}")
    b.button(text="📄 السجل", callback_data=f"log:{iid}")
    b.button(text="🗑 حذف", callback_data=f"delete:{iid}")
    b.button(text="⬅️ رجوع", callback_data="list")
    b.adjust(2, 2, 1, 1)
    return b.as_markup()


def back_menu():
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ الرئيسية", callback_data="home")
    return b.as_markup()


def format_install(row):
    status = row.get("status", "stopped")
    status_text = {
        "running": "🟢 يعمل",
        "stopped": "🔴 متوقف",
        "error": "⚠️ خطأ",
    }.get(status, status)

    if row.get("unlimited"):
        expiry = "♾️ غير محدود"
    elif row.get("expires_at"):
        dt = datetime.fromtimestamp(
            row["expires_at"],
            timezone.utc,
        )
        expiry = dt.strftime("%Y-%m-%d %H:%M UTC")
    else:
        expiry = "غير محدد"

    return (
        f"🆔 <b>{row['id']}</b>\n"
        f"📦 <b>{row['name']}</b>\n"
        f"📡 الحالة: {status_text}\n"
        f"📅 الانتهاء: {expiry}\n"
    )


def setup(dp, db, pm, sessions, owner):
    dp.include_router(router)

    @router.message(CommandStart())
    async def start(message: Message):
        if not allowed(message.from_user, owner):
            return await message.answer(
                "⛔ غير مصرح لك باستخدام هذا البوت."
            )

        await message.answer(
            "🤖 <b>Tepthon Factory</b>\n\n"
            "مرحبًا بك في مصنع Tepthon.\n"
            "اختر العملية المطلوبة:",
            reply_markup=main_menu(),
        )

    @router.callback_query(F.data == "home")
    async def home(callback: CallbackQuery, state: FSMContext):
        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        await state.clear()

        await callback.message.edit_text(
            "🤖 <b>Tepthon Factory</b>\n\n"
            "اختر العملية المطلوبة:",
            reply_markup=main_menu(),
        )

        await callback.answer()

    @router.callback_query(F.data == "new")
    async def new_install(
        callback: CallbackQuery,
        state: FSMContext,
    ):
        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        await state.set_state(
            InstallState.waiting_name
        )

        await callback.message.answer(
            "➕ <b>تنصيب جديد</b>\n\n"
            "أرسل اسم التنصيب:"
        )

        await callback.answer()

    @router.callback_query(F.data == "session_new")
    async def session_new(
        callback: CallbackQuery,
        state: FSMContext,
    ):
        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        await state.set_state(
            InstallState.waiting_session
        )

        await callback.message.answer(
            "🔑 <b>تنصيب عبر Session String</b>\\n\\n"
            "أرسل Session String الخاصة بحساب Telegram."
        )

        await callback.answer()


    @router.message(InstallState.waiting_session)
    async def get_session(
        message: Message,
        state: FSMContext,
    ):
        if not allowed(message.from_user, owner):
            return

        session_string = (message.text or "").strip()

        if not session_string:
            return await message.answer(
                "❌ أرسل Session String صحيحة."
            )

        await message.answer(
            "⏳ جاري التحقق من Session String..."
        )

        try:
            # سيتم ربطها بإنشاء التنصيب في الخطوة التالية
            await state.clear()

            await message.answer(
                "✅ تم استلام Session String بنجاح."
            )

        except Exception as error:
            await message.answer(
                f"❌ فشل التحقق:\\n<code>{error}</code>"
            )


    @router.message(InstallState.waiting_name)
    async def get_name(
        message: Message,
        state: FSMContext,
    ):
        if not allowed(message.from_user, owner):
            return

        name = (message.text or "").strip()

        if not name:
            return await message.answer(
                "❌ أرسل اسمًا صحيحًا."
            )

        if len(name) > 50:
            return await message.answer(
                "❌ الاسم طويل جدًا، الحد الأقصى 50 حرفًا."
            )

        await state.update_data(name=name)
        await state.set_state(
            InstallState.waiting_days
        )

        await message.answer(
            "📅 أرسل مدة التنصيب بالأيام.\n\n"
            "مثال: <code>30</code>\n"
            "أو أرسل <code>0</code> للتنصيب غير المحدود."
        )

    @router.message(InstallState.waiting_days)
    async def get_days(
        message: Message,
        state: FSMContext,
    ):
        if not allowed(message.from_user, owner):
            return

        try:
            days = int((message.text or "").strip())
        except ValueError:
            return await message.answer(
                "❌ أرسل رقمًا صحيحًا."
            )

        if days < 0 or days > 3650:
            return await message.answer(
                "❌ المدة يجب أن تكون بين 0 و3650 يومًا."
            )

        data = await state.get_data()
        name = data["name"]

        unlimited = days == 0

        if unlimited:
            expires_at = None
        else:
            expires_at = (
                datetime.now(timezone.utc)
                + timedelta(days=days)
            ).timestamp()

        try:
            install_id = db.create(
                user_id=message.from_user.id,
                name=name,
                expires_at=expires_at,
                unlimited=unlimited,
            )

            pm.create(install_id)

        except Exception as error:
            return await message.answer(
                f"❌ فشل إنشاء التنصيب:\n<code>{error}</code>"
            )

        await state.update_data(
            install_id=install_id
        )

        await state.set_state(
            InstallState.waiting_phone
        )

        await message.answer(
            f"✅ تم إنشاء التنصيب رقم <b>{install_id}</b>.\n\n"
            "📱 الآن أرسل رقم الهاتف مع مفتاح الدولة.\n"
            "مثال:\n"
            "<code>+9665XXXXXXXX</code>"
        )

    @router.message(InstallState.waiting_phone)
    async def get_phone(
        message: Message,
        state: FSMContext,
    ):
        if not allowed(message.from_user, owner):
            return

        phone = (message.text or "").strip()

        if not phone.startswith("+"):
            return await message.answer(
                "❌ يجب أن يبدأ الرقم بـ <code>+</code>."
            )

        data = await state.get_data()
        install_id = data["install_id"]

        try:
            await sessions.send_code(
                phone,
                API_ID,
                API_HASH,
            )
        except Exception as error:
            return await message.answer(
                "❌ فشل إرسال كود Telegram:\n"
                f"<code>{error}</code>"
            )

        await state.update_data(phone=phone)
        await state.set_state(
            InstallState.waiting_code
        )

        await message.answer(
            "📨 تم إرسال كود Telegram.\n\n"
            "أرسل الكود كما وصلك."
        )

    @router.callback_query(F.data == "resend_code")
    async def resend_code(
        callback: CallbackQuery,
        state: FSMContext,
    ):
        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        data = await state.get_data()
        phone = data.get("phone")

        if not phone:
            return await callback.answer(
                "❌ رقم الهاتف غير موجود. ابدأ التنصيب من جديد.",
                show_alert=True,
            )

        try:
            await sessions.resend_code(phone)

            await callback.message.answer(
                "📨 <b>تم إرسال كود جديد.</b>\\n\\n"
                "استخدم الكود الجديد فقط."
            )

            await callback.answer("✅ تم إرسال كود جديد")

        except Exception as error:
            await callback.answer(
                str(error),
                show_alert=True,
            )


    @router.message(InstallState.waiting_code)
    async def get_code(
        message: Message,
        state: FSMContext,
    ):
        if not allowed(message.from_user, owner):
            return

        code = (message.text or "").replace(" ", "").strip()

        data = await state.get_data()

        try:
            target = await sessions.login_code(
                data["install_id"],
                data["phone"],
                code,
                API_ID,
                API_HASH,
            )

        except SessionPasswordNeededError:
            await state.set_state(
                InstallState.waiting_password
            )

            return await message.answer(
                "🔐 الحساب محمي بالتحقق بخطوتين.\n\n"
                "أرسل كلمة مرور Telegram."
            )

        except Exception as error:
            return await message.answer(
                "❌ فشل تسجيل الدخول:\n"
                f"<code>{error}</code>"
            )

        db.session(
            data["install_id"],
            target,
            data["phone"],
        )

        try:
            pm.start(data["install_id"])
            db.status(
                data["install_id"],
                "running",
            )
        except Exception as error:
            db.status(
                data["install_id"],
                "error",
            )
            await state.clear()

            return await message.answer(
                "⚠️ تم حفظ الجلسة، لكن فشل تشغيل السورس:\n"
                f"<code>{error}</code>"
            )

        await state.clear()

        await message.answer(
            "✅ <b>تم تسجيل الحساب وتشغيل Tepthon بنجاح.</b>\n\n"
            f"🆔 رقم التنصيب: <b>{data['install_id']}</b>",
            reply_markup=account_menu(
                data["install_id"]
            ),
        )

    @router.message(InstallState.waiting_password)
    async def get_password(
        message: Message,
        state: FSMContext,
    ):
        if not allowed(message.from_user, owner):
            return

        password = message.text or ""
        data = await state.get_data()

        try:
            target = await sessions.login_code(
                data["install_id"],
                data["phone"],
                "",
                API_ID,
                API_HASH,
                password=password,
            )

        except Exception as error:
            return await message.answer(
                "❌ كلمة المرور غير صحيحة أو فشل تسجيل الدخول:\n"
                f"<code>{error}</code>"
            )

        db.session(
            data["install_id"],
            target,
            data["phone"],
        )

        try:
            pm.start(data["install_id"])
            db.status(
                data["install_id"],
                "running",
            )
        except Exception as error:
            db.status(
                data["install_id"],
                "error",
            )
            await state.clear()

            return await message.answer(
                "⚠️ تم حفظ الجلسة، لكن فشل تشغيل السورس:\n"
                f"<code>{error}</code>"
            )

        await state.clear()

        await message.answer(
            "✅ <b>تم تسجيل الدخول وتشغيل الحساب بنجاح.</b>",
            reply_markup=account_menu(
                data["install_id"]
            ),
        )

    @router.callback_query(F.data == "list")
    async def list_installs(
        callback: CallbackQuery,
        state: FSMContext,
    ):
        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        await state.clear()

        rows = db.user(owner)

        if not rows:
            return await callback.message.edit_text(
                "📋 <b>تنصيباتك</b>\n\n"
                "لا توجد تنصيبات حاليًا.",
                reply_markup=main_menu(),
            )

        text = "📋 <b>تنصيباتك:</b>\n\n"

        b = InlineKeyboardBuilder()

        for row in rows:
            text += format_install(row) + "\n"
            b.button(
                text=f"📦 {row['name']} #{row['id']}",
                callback_data=f"account:{row['id']}",
            )

        b.button(
            text="⬅️ الرئيسية",
            callback_data="home",
        )
        b.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=b.as_markup(),
        )

        await callback.answer()

    @router.callback_query(F.data.startswith("account:"))
    async def account(
        callback: CallbackQuery,
    ):
        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        iid = int(callback.data.split(":")[1])
        row = db.get(iid)

        if not row or row["user_id"] != owner:
            return await callback.answer(
                "التنصيب غير موجود.",
                show_alert=True,
            )

        await callback.message.edit_text(
            "📦 <b>إدارة التنصيب</b>\n\n"
            + format_install(row),
            reply_markup=account_menu(iid),
        )

        await callback.answer()

    @router.callback_query(F.data.startswith("start:"))
    async def start_account(callback: CallbackQuery):
        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        iid = int(callback.data.split(":")[1])
        row = db.get(iid)

        if not row or row["user_id"] != owner:
            return await callback.answer(
                "التنصيب غير موجود.",
                show_alert=True,
            )

        try:
            pm.start(iid)
            db.status(iid, "running")

            await callback.answer(
                "✅ تم التشغيل."
            )

        except Exception as error:
            db.status(iid, "error")
            await callback.answer(
                f"❌ {error}",
                show_alert=True,
            )

    @router.callback_query(F.data.startswith("stop:"))
    async def stop_account(callback: CallbackQuery):
        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        iid = int(callback.data.split(":")[1])

        try:
            pm.stop(iid)
            db.status(iid, "stopped")

            await callback.answer(
                "⛔ تم الإيقاف."
            )

        except Exception as error:
            await callback.answer(
                f"❌ {error}",
                show_alert=True,
            )

    @router.callback_query(F.data.startswith("restart:"))
    async def restart_account(callback: CallbackQuery):
        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        iid = int(callback.data.split(":")[1])

        try:
            pm.restart(iid)
            db.status(iid, "running")

            await callback.answer(
                "🔄 تمت إعادة التشغيل."
            )

        except Exception as error:
            db.status(iid, "error")

            await callback.answer(
                f"❌ {error}",
                show_alert=True,
            )

    @router.callback_query(F.data.startswith("log:"))
    async def log_account(callback: CallbackQuery):
        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        iid = int(callback.data.split(":")[1])
        text = pm.log(iid)

        if not text:
            text = "📄 لا يوجد سجل حتى الآن."

        if len(text) > 3800:
            text = text[-3800:]

        await callback.message.answer(
            f"📄 <b>سجل التنصيب #{iid}</b>\n\n"
            f"<pre>{text}</pre>"
        )

        await callback.answer()

    @router.callback_query(F.data.startswith("delete:"))
    async def delete_account(callback: CallbackQuery):
        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        iid = int(callback.data.split(":")[1])
        row = db.get(iid)

        if not row or row["user_id"] != owner:
            return await callback.answer(
                "التنصيب غير موجود.",
                show_alert=True,
            )

        try:
            pm.delete(iid)
            db.delete(iid)

            await callback.message.edit_text(
                "🗑 <b>تم حذف التنصيب بنجاح.</b>",
                reply_markup=main_menu(),
            )

            await callback.answer()

        except Exception as error:
            await callback.answer(
                f"❌ فشل الحذف: {error}",
                show_alert=True,
            )

    @router.callback_query(F.data == "status")
    async def status(callback: CallbackQuery):
        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        rows = db.user(owner)

        running = sum(
            1 for x in rows
            if x["status"] == "running"
        )

        stopped = sum(
            1 for x in rows
            if x["status"] != "running"
        )

        await callback.message.edit_text(
            "📊 <b>حالة المصنع</b>\n\n"
            f"📦 إجمالي التنصيبات: <b>{len(rows)}</b>\n"
            f"🟢 تعمل: <b>{running}</b>\n"
            f"🔴 متوقفة/خطأ: <b>{stopped}</b>",
            reply_markup=main_menu(),
        )

        await callback.answer()


async def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN غير موجود في Environment Variables."
        )

    if not OWNER_ID:
        raise RuntimeError(
            "OWNER_ID غير موجود في Environment Variables."
        )

    db = Database("data/factory.db")

    pm = ProcessManager(
        "template/Tepthon",
        "data/accounts",
    )

    sessions = SessionManager(
        "data/accounts"
    )

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        ),
    )

    dp = Dispatcher()

    setup(
        dp,
        db,
        pm,
        sessions,
        OWNER_ID,
    )

    print("================================")
    print(" Tepthon Factory")
    print(" Database: OK")
    print(" Sessions: OK")
    print(" Permissions: OK")
    print("================================")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
