import html
from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher

from telethon.errors import SessionPasswordNeededError

from config import BOT_TOKEN, OWNER_ID, API_ID, API_HASH
from database import Database
from manager.processes import ProcessManager
from manager.sessions import SessionManager


router = Router()


# ============================================================
# STATES
# ============================================================

class InstallState(StatesGroup):
    waiting_name = State()
    waiting_days = State()
    waiting_phone = State()
    waiting_code = State()
    waiting_password = State()
    waiting_session = State()


# ============================================================
# AUTH
# ============================================================

def allowed(user, owner):
    return user is not None and user.id == owner


# ============================================================
# MAIN MENU
# ============================================================

def main_menu():
    b = InlineKeyboardBuilder()

    b.button(
        text="💌 طلب تنصيب",
        callback_data="install_menu",
    )

    b.button(
        text="✅ تسجيل | LoGiN",
        callback_data="login_menu",
    )

    b.button(
        text="🔑 استخراج جلسة",
        callback_data="session_info",
    )

    b.button(
        text="💎 ميزات السورس",
        callback_data="features",
    )

    b.button(
        text="👨‍💻 المطور",
        callback_data="developer",
    )

    b.button(
        text="🔗 قناة السورس",
        callback_data="source",
    )

    b.adjust(2, 1, 2, 1)

    return b.as_markup()


# ============================================================
# INSTALL MENU
# ============================================================

def install_menu():
    b = InlineKeyboardBuilder()

    b.button(
        text="📱 تسجيل بالرقم",
        callback_data="new",
    )

    b.button(
        text="🔑 Session String",
        callback_data="session_new",
    )

    b.button(
        text="📋 تنصيباتي",
        callback_data="list",
    )

    b.button(
        text="⬅️ رجوع",
        callback_data="home",
    )

    b.adjust(2, 1, 1)

    return b.as_markup()


# ============================================================
# ACCOUNT MENU
# ============================================================

def account_menu(iid):
    b = InlineKeyboardBuilder()

    b.button(
        text="▶️ تشغيل",
        callback_data=f"start:{iid}",
    )

    b.button(
        text="⛔ إيقاف",
        callback_data=f"stop:{iid}",
    )

    b.button(
        text="🔄 إعادة تشغيل",
        callback_data=f"restart:{iid}",
    )

    b.button(
        text="📄 السجل",
        callback_data=f"log:{iid}",
    )

    b.button(
        text="🗑 حذف التنصيب",
        callback_data=f"delete:{iid}",
    )

    b.button(
        text="⬅️ رجوع",
        callback_data="list",
    )

    b.adjust(2, 2, 1, 1)

    return b.as_markup()


def back_home():
    b = InlineKeyboardBuilder()

    b.button(
        text="⬅️ الرئيسية",
        callback_data="home",
    )

    return b.as_markup()


# ============================================================
# FORMAT ACCOUNT
# ============================================================

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

        expiry = dt.strftime(
            "%Y-%m-%d %H:%M UTC"
        )

    else:
        expiry = "غير محدد"

    return (
        f"🆔 <b>{row['id']}</b>\n"
        f"📦 <b>{html.escape(str(row['name']))}</b>\n"
        f"📡 الحالة: {status_text}\n"
        f"📅 الانتهاء: {expiry}\n"
    )


# ============================================================
# SETUP
# ============================================================

def setup(dp, db, pm, sessions, owner):

    dp.include_router(router)

    # ========================================================
    # START
    # ========================================================

    @router.message(CommandStart())
    async def start(message: Message):

        if not allowed(message.from_user, owner):
            return await message.answer(
                "⛔ غير مصرح لك باستخدام هذا البوت."
            )

        text = (
            "🤖 <b>Tepthon Factory</b>\n\n"
            "⌁ مرحباً بك عزيزي في مصنع Tepthon\n\n"
            "⌁ اختر الخدمة المطلوبة من الأزرار بالأسفل."
        )

        await message.answer(
            text,
            reply_markup=main_menu(),
        )

    # ========================================================
    # HOME
    # ========================================================

    @router.callback_query(F.data == "home")
    async def home(
        callback: CallbackQuery,
        state: FSMContext,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        await state.clear()

        text = (
            "🤖 <b>Tepthon Factory</b>\n\n"
            "⌁ مرحباً بك عزيزي في مصنع Tepthon\n\n"
            "⌁ اختر الخدمة المطلوبة من الأزرار بالأسفل."
        )

        try:
            await callback.message.edit_text(
                text,
                reply_markup=main_menu(),
            )
        except TelegramBadRequest:
            pass

        await callback.answer()

    # ========================================================
    # INSTALL MENU
    # ========================================================

    @router.callback_query(F.data == "install_menu")
    async def install_menu_handler(
        callback: CallbackQuery,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        await callback.message.edit_text(
            "💌 <b>طلب تنصيب</b>\n\n"
            "اختر طريقة تسجيل الحساب:",
            reply_markup=install_menu(),
        )

        await callback.answer()

    # ========================================================
    # LOGIN MENU
    # ========================================================

    @router.callback_query(F.data == "login_menu")
    async def login_menu_handler(
        callback: CallbackQuery,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        rows = db.user(owner)

        if not rows:
            return await callback.message.edit_text(
                "✅ <b>تسجيل | LoGiN</b>\n\n"
                "لا توجد حسابات مسجلة حاليًا.",
                reply_markup=install_menu(),
            )

        text = (
            "✅ <b>تسجيل | LoGiN</b>\n\n"
            "اختر الحساب الذي تريد إدارته:"
        )

        b = InlineKeyboardBuilder()

        for row in rows:
            b.button(
                text=f"📦 {row['name']} #{row['id']}",
                callback_data=f"account:{row['id']}",
            )

        b.button(
            text="⬅️ رجوع",
            callback_data="home",
        )

        b.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=b.as_markup(),
        )

        await callback.answer()

    # ========================================================
    # SESSION INFO
    # ========================================================

    @router.callback_query(F.data == "session_info")
    async def session_info(
        callback: CallbackQuery,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        await callback.message.edit_text(
            "🔑 <b>استخراج جلسة</b>\n\n"
            "يمكنك استخدام Session String لحسابك "
            "عن طريق خيار <b>طلب تنصيب → Session String</b>.\n\n"
            "⚠️ لا ترسل Session String لأي شخص آخر.",
            reply_markup=back_home(),
        )

        await callback.answer()

    # ========================================================
    # FEATURES
    # ========================================================

    @router.callback_query(F.data == "features")
    async def features(
        callback: CallbackQuery,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        await callback.message.edit_text(
            "💎 <b>ميزات السورس</b>\n\n"
            "▫️ تشغيل Tepthon\n"
            "▫️ إيقاف الحساب\n"
            "▫️ إعادة التشغيل\n"
            "▫️ تسجيل الدخول بالرقم\n"
            "▫️ دعم Session String\n"
            "▫️ إدارة عدة تنصيبات\n"
            "▫️ عرض سجل التشغيل\n"
            "▫️ حذف التنصيب\n"
            "▫️ تحديد مدة الاشتراك\n"
            "▫️ اشتراك غير محدود",
            reply_markup=back_home(),
        )

        await callback.answer()

    # ========================================================
    # DEVELOPER
    # ========================================================

    @router.callback_query(F.data == "developer")
    async def developer(
        callback: CallbackQuery,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        await callback.message.edit_text(
            "👨‍💻 <b>المطور</b>\n\n"
            "⌁ Tepthon Factory\n"
            "⌁ إدارة وتنصيب وتشغيل الحسابات",
            reply_markup=back_home(),
        )

        await callback.answer()

    # ========================================================
    # SOURCE
    # ========================================================

    @router.callback_query(F.data == "source")
    async def source(
        callback: CallbackQuery,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        await callback.message.edit_text(
            "🔗 <b>قناة السورس</b>\n\n"
            "أضف رابط قناة السورس هنا.",
            reply_markup=back_home(),
        )

        await callback.answer()

    # ========================================================
    # NEW PHONE INSTALL
    # ========================================================

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

        await state.update_data(
            install_mode="phone"
        )

        await state.set_state(
            InstallState.waiting_name
        )

        await callback.message.answer(
            "📱 <b>تسجيل حساب جديد</b>\n\n"
            "أرسل اسم التنصيب:"
        )

        await callback.answer()

    # ========================================================
    # SESSION INSTALL
    # ========================================================

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

        await state.update_data(
            install_mode="session"
        )

        await state.set_state(
            InstallState.waiting_name
        )

        await callback.message.answer(
            "🔑 <b>تنصيب عبر Session String</b>\n\n"
            "أرسل اسم التنصيب:"
        )

        await callback.answer()

    # ========================================================
    # NAME
    # ========================================================

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

        await state.update_data(
            name=name
        )

        await state.set_state(
            InstallState.waiting_days
        )

        await message.answer(
            "📅 <b>مدة التنصيب</b>\n\n"
            "أرسل عدد الأيام.\n\n"
            "مثال: <code>30</code>\n"
            "أو <code>0</code> للتنصيب غير المحدود."
        )

    # ========================================================
    # DAYS
    # ========================================================

    @router.message(InstallState.waiting_days)
    async def get_days(
        message: Message,
        state: FSMContext,
    ):

        if not allowed(message.from_user, owner):
            return

        try:
            days = int(
                (message.text or "").strip()
            )

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
        install_mode = data.get(
            "install_mode",
            "phone",
        )

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
                "❌ فشل إنشاء التنصيب:\n"
                f"<code>{html.escape(str(error))}</code>"
            )

        await state.update_data(
            install_id=install_id
        )

        if install_mode == "session":

            await state.set_state(
                InstallState.waiting_session
            )

            return await message.answer(
                f"✅ تم إنشاء التنصيب رقم "
                f"<b>{install_id}</b>.\n\n"
                "🔑 أرسل الآن Session String."
            )

        await state.set_state(
            InstallState.waiting_phone
        )

        await message.answer(
            f"✅ تم إنشاء التنصيب رقم "
            f"<b>{install_id}</b>.\n\n"
            "📱 أرسل رقم الهاتف مع مفتاح الدولة.\n"
            "مثال:\n"
            "<code>+9665XXXXXXXX</code>"
        )

    # ========================================================
    # SESSION STRING
    # ========================================================

    @router.message(InstallState.waiting_session)
    async def get_session(
        message: Message,
        state: FSMContext,
    ):

        if not allowed(message.from_user, owner):
            return

        session_string = (
            message.text or ""
        ).strip()

        if not session_string:
            return await message.answer(
                "❌ أرسل Session String صحيحة."
            )

        data = await state.get_data()

        install_id = data.get(
            "install_id"
        )

        if not install_id:
            await state.clear()

            return await message.answer(
                "❌ لم يتم العثور على التنصيب."
            )

        await message.answer(
            "⏳ <b>جاري التحقق من Session...</b>"
        )

        try:

            target = await sessions.install_string_session(
                install_id,
                session_string,
                API_ID,
                API_HASH,
            )

            db.session(
                install_id,
                target,
            )

            pm.start(install_id)

            db.status(
                install_id,
                "running",
            )

        except Exception as error:

            db.status(
                install_id,
                "error",
            )

            await state.clear()

            return await message.answer(
                "❌ <b>فشل التنصيب</b>\n\n"
                f"<code>{html.escape(str(error))}</code>"
            )

        await state.clear()

        await message.answer(
            "✅ <b>تم التنصيب بنجاح</b>\n\n"
            f"🆔 التنصيب: <b>{install_id}</b>\n"
            "🟢 الحالة: يعمل",
            reply_markup=account_menu(
                install_id
            ),
        )

    # ========================================================
    # PHONE
    # ========================================================

    @router.message(InstallState.waiting_phone)
    async def get_phone(
        message: Message,
        state: FSMContext,
    ):

        if not allowed(message.from_user, owner):
            return

        phone = (
            message.text or ""
        ).strip()

        if not phone.startswith("+"):
            return await message.answer(
                "❌ يجب أن يبدأ الرقم بـ <code>+</code>."
            )

        data = await state.get_data()

        try:

            await sessions.send_code(
                phone,
                API_ID,
                API_HASH,
            )

        except Exception as error:

            return await message.answer(
                "❌ فشل إرسال كود Telegram:\n"
                f"<code>{html.escape(str(error))}</code>"
            )

        await state.update_data(
            phone=phone
        )

        await state.set_state(
            InstallState.waiting_code
        )

        b = InlineKeyboardBuilder()

        b.button(
            text="🔄 إعادة إرسال الكود",
            callback_data="resend_code",
        )

        await message.answer(
            "📨 <b>تم إرسال الكود.</b>\n\n"
            "أرسل كود Telegram.",
            reply_markup=b.as_markup(),
        )

    # ========================================================
    # RESEND
    # ========================================================

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
                "❌ رقم الهاتف غير موجود.",
                show_alert=True,
            )

        try:

            await sessions.resend_code(
                phone
            )

            await callback.answer(
                "✅ تم إرسال كود جديد."
            )

            await callback.message.answer(
                "📨 <b>تم إرسال كود جديد.</b>\n\n"
                "استخدم آخر كود وصلك."
            )

        except Exception as error:

            await callback.answer(
                "❌ تعذر إرسال الكود.",
                show_alert=True,
            )

    # ========================================================
    # CODE
    # ========================================================

    @router.message(InstallState.waiting_code)
    async def get_code(
        message: Message,
        state: FSMContext,
    ):

        if not allowed(message.from_user, owner):
            return

        code = (
            message.text or ""
        ).replace(" ", "").strip()

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
                f"<code>{html.escape(str(error))}</code>"
            )

        db.session(
            data["install_id"],
            target,
            data["phone"],
        )

        try:

            pm.start(
                data["install_id"]
            )

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
                f"<code>{html.escape(str(error))}</code>"
            )

        await state.clear()

        await message.answer(
            "✅ <b>تم تسجيل الحساب وتشغيل Tepthon.</b>\n\n"
            f"🆔 التنصيب: "
            f"<b>{data['install_id']}</b>",
            reply_markup=account_menu(
                data["install_id"]
            ),
        )

    # ========================================================
    # PASSWORD
    # ========================================================

    @router.message(InstallState.waiting_password)
    async def get_password(
        message: Message,
        state: FSMContext,
    ):

        if not allowed(message.from_user, owner):
            return

        password = (
            message.text or ""
        )

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
                f"<code>{html.escape(str(error))}</code>"
            )

        db.session(
            data["install_id"],
            target,
            data["phone"],
        )

        try:

            pm.start(
                data["install_id"]
            )

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
                "⚠️ تم حفظ الجلسة، لكن فشل التشغيل:\n"
                f"<code>{html.escape(str(error))}</code>"
            )

        await state.clear()

        await message.answer(
            "✅ <b>تم تسجيل الدخول وتشغيل الحساب.</b>",
            reply_markup=account_menu(
                data["install_id"]
            ),
        )

    # ========================================================
    # LIST
    # ========================================================

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
                reply_markup=install_menu(),
            )

        text = (
            "📋 <b>تنصيباتك</b>\n\n"
        )

        b = InlineKeyboardBuilder()

        for row in rows:

            text += (
                format_install(row)
                + "\n"
            )

            b.button(
                text=(
                    f"📦 {row['name']} "
                    f"#{row['id']}"
                ),
                callback_data=(
                    f"account:{row['id']}"
                ),
            )

        b.button(
            text="⬅️ رجوع",
            callback_data="install_menu",
        )

        b.adjust(1)

        try:

            await callback.message.edit_text(
                text,
                reply_markup=b.as_markup(),
            )

        except TelegramBadRequest as error:

            if "message is not modified" not in str(error):
                raise

        await callback.answer()

    # ========================================================
    # ACCOUNT
    # ========================================================

    @router.callback_query(
        F.data.startswith("account:")
    )
    async def account(
        callback: CallbackQuery,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        try:

            iid = int(
                callback.data.split(":")[1]
            )

        except (ValueError, IndexError):

            return await callback.answer(
                "❌ رقم غير صحيح.",
                show_alert=True,
            )

        row = db.get(iid)

        if not row or row["user_id"] != owner:

            return await callback.answer(
                "❌ التنصيب غير موجود.",
                show_alert=True,
            )

        await callback.message.edit_text(
            "📦 <b>إدارة التنصيب</b>\n\n"
            + format_install(row),
            reply_markup=account_menu(iid),
        )

        await callback.answer()

    # ========================================================
    # START
    # ========================================================

    @router.callback_query(
        F.data.startswith("start:")
    )
    async def start_account(
        callback: CallbackQuery,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        iid = int(
            callback.data.split(":")[1]
        )

        row = db.get(iid)

        if not row or row["user_id"] != owner:

            return await callback.answer(
                "❌ التنصيب غير موجود.",
                show_alert=True,
            )

        try:

            pm.start(iid)

            db.status(
                iid,
                "running",
            )

            await callback.answer(
                "🟢 تم التشغيل."
            )

        except Exception as error:

            db.status(
                iid,
                "error",
            )

            await callback.answer(
                f"❌ {error}",
                show_alert=True,
            )

    # ========================================================
    # STOP
    # ========================================================

    @router.callback_query(
        F.data.startswith("stop:")
    )
    async def stop_account(
        callback: CallbackQuery,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        iid = int(
            callback.data.split(":")[1]
        )

        try:

            pm.stop(iid)

            db.status(
                iid,
                "stopped",
            )

            await callback.answer(
                "⛔ تم الإيقاف."
            )

        except Exception as error:

            await callback.answer(
                f"❌ {error}",
                show_alert=True,
            )

    # ========================================================
    # RESTART
    # ========================================================

    @router.callback_query(
        F.data.startswith("restart:")
    )
    async def restart_account(
        callback: CallbackQuery,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        iid = int(
            callback.data.split(":")[1]
        )

        try:

            pm.restart(iid)

            db.status(
                iid,
                "running",
            )

            await callback.answer(
                "🔄 تمت إعادة التشغيل."
            )

        except Exception as error:

            db.status(
                iid,
                "error",
            )

            await callback.answer(
                f"❌ {error}",
                show_alert=True,
            )

    # ========================================================
    # LOG
    # ========================================================

    @router.callback_query(
        F.data.startswith("log:")
    )
    async def log_account(
        callback: CallbackQuery,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        try:

            iid = int(
                callback.data.split(":")[1]
            )

        except (ValueError, IndexError):

            return await callback.answer(
                "❌ رقم التنصيب غير صحيح.",
                show_alert=True,
            )

        row = db.get(iid)

        if not row or row["user_id"] != owner:

            return await callback.answer(
                "❌ التنصيب غير موجود.",
                show_alert=True,
            )

        await callback.answer(
            "📄 جاري جلب السجل..."
        )

        try:

            text = pm.log(iid)

            if not text:
                text = "لا يوجد سجل حتى الآن."

            text = html.escape(text)

            if len(text) > 3500:
                text = text[-3500:]

            await callback.message.answer(
                f"📄 <b>سجل التنصيب #{iid}</b>\n\n"
                f"<pre>{text}</pre>",
            )

        except Exception as error:

            await callback.message.answer(
                "❌ تعذر قراءة سجل التنصيب.\n\n"
                f"<code>{html.escape(str(error))}</code>"
            )

    # ========================================================
    # DELETE
    # ========================================================

    @router.callback_query(
        F.data.startswith("delete:")
    )
    async def delete_account(
        callback: CallbackQuery,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        iid = int(
            callback.data.split(":")[1]
        )

        row = db.get(iid)

        if not row or row["user_id"] != owner:

            return await callback.answer(
                "❌ التنصيب غير موجود.",
                show_alert=True,
            )

        try:

            pm.delete(iid)

            db.delete(iid)

            await callback.message.edit_text(
                "🗑 <b>تم حذف التنصيب بنجاح.</b>\n\n"
                "تم إيقاف الحساب وحذف ملفاته.",
                reply_markup=main_menu(),
            )

            await callback.answer()

        except Exception as error:

            await callback.answer(
                f"❌ فشل الحذف: {error}",
                show_alert=True,
            )

    # ========================================================
    # STATUS
    # ========================================================

    @router.callback_query(F.data == "status")
    async def status(
        callback: CallbackQuery,
    ):

        if callback.from_user.id != owner:
            return await callback.answer(
                "غير مصرح",
                show_alert=True,
            )

        rows = db.user(owner)

        running = sum(
            1
            for x in rows
            if x["status"] == "running"
        )

        stopped = len(rows) - running

        await callback.message.edit_text(
            "📊 <b>حالة المصنع</b>\n\n"
            f"📦 إجمالي التنصيبات: "
            f"<b>{len(rows)}</b>\n"
            f"🟢 تعمل: <b>{running}</b>\n"
            f"🔴 متوقفة/خطأ: <b>{stopped}</b>",
            reply_markup=main_menu(),
        )

        await callback.answer()


# ============================================================
# MAIN
# ============================================================

async def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN غير موجود في Environment Variables."
        )

    if not OWNER_ID:
        raise RuntimeError(
            "OWNER_ID غير موجود في Environment Variables."
        )

    if not API_ID:
        raise RuntimeError(
            "API_ID غير موجود في Environment Variables."
        )

    if not API_HASH:
        raise RuntimeError(
            "API_HASH غير موجود في Environment Variables."
        )

    db = Database(
        "data/factory.db"
    )

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

    print("==============================")
    print(" Tepthon Factory")
    print(" Database: OK")
    print(" Sessions: OK")
    print(" Process Manager: OK")
    print(" Bot: OK")
    print("==============================")

    try:

        await dp.start_polling(bot)

    finally:

        await sessions.close()

        await bot.session.close()
