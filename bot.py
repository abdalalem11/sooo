from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder


router = Router()


class InstallState(StatesGroup):
    waiting_name = State()
    waiting_days = State()


def main_menu():
    b = InlineKeyboardBuilder()

    b.button(text="➕ تنصيب جديد", callback_data="new")
    b.button(text="📋 تنصيبتي", callback_data="list")
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


def allowed(user, owner):
    return user and user.id == owner


def setup(dp, db, pm, owner):

    dp.include_router(router)

    @router.message(CommandStart())
    async def start(message: Message):

        if not allowed(message.from_user, owner):
            return await message.answer("⛔ غير مصرح لك باستخدام هذا البوت.")

        await message.answer(
            "🤖 <b>Tepthon Factory</b>\n\n"
            "مرحبًا بك في مصنع Tepthon.\n"
            "يمكنك إنشاء وإدارة التنصيبات من الأزرار بالأسفل.",
            reply_markup=main_menu(),
        )

    @router.callback_query(F.data == "home")
    async def home(callback: CallbackQuery):

        if callback.from_user.id != owner:
            return await callback.answer("غير مصرح", show_alert=True)

        await callback.message.edit_text(
            "🤖 <b>Tepthon Factory</b>\n\n"
            "اختر العملية المطلوبة:",
            reply_markup=main_menu(),
        )

        await callback.answer()

    # =========================
    # إنشاء تنصيب
    # =========================

    @router.callback_query(F.data == "new")
    async def new_install(callback: CallbackQuery, state: FSMContext):

        if callback.from_user.id != owner:
            return await callback.answer("غير مصرح", show_alert=True)

        await state.set_state(InstallState.waiting_name)

        await callback.message.answer(
            "➕ <b>إنشاء تنصيب جديد</b>\n\n"
            "أرسل اسم التنصيب:"
        )

        await callback.answer()

    @router.message(InstallState.waiting_name)
    async def get_name(message: Message, state: FSMContext


cat > manager/processes.py <<'PY'
import os
import shutil
import signal
import subprocess
import sys

from pathlib import Path


class ProcessManager:

    def __init__(self, template_dir, accounts_dir):

        self.template = Path(template_dir)
        self.accounts = Path(accounts_dir)

        self.accounts.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.procs = {}

    def path(self, install_id):

        return self.accounts / str(install_id)

    def create(self, install_id):

        if not self.template.exists():

            raise RuntimeError(
                f"Template not found: {self.template}"
            )

        destination = self.path(install_id)

        if destination.exists():

            shutil.rmtree(destination)

        shutil.copytree(
            self.template,
            destination,
        )

        return destination

    def start(self, install_id):

        directory = self.path(install_id)

        if not directory.exists():

            raise RuntimeError(
                "Account directory does not exist"
            )

        self.stop(install_id)

        env = os.environ.copy()

        env["FACTORY_INSTALL_ID"] = str(
            install_id
        )

        log_path = directory / "factory.log"

        log_file = open(
            log_path,
            "a",
            encoding="utf-8",
        )

        process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                "main.py",
            ],
            cwd=directory,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

        self.procs[install_id] = (
            process,
            log_file,
        )

        return process.pid

    def stop(self, install_id):

        item = self.procs.pop(
            install_id,
            None,
        )

        if not item:
            return

        process, log_file = item

        try:

            os.killpg(
                process.pid,
                signal.SIGTERM,
            )

        except Exception:

            try:
                process.terminate()

            except Exception:
                pass

        try:

            process.wait(timeout=8)

        except Exception:

            try:
                os.killpg(
                    process.pid,
                    signal.SIGKILL,
                )

            except Exception:
                pass

        try:
            log_file.close()

        except Exception:
            pass

    def restart(self, install_id):

        self.stop(install_id)

        return self.start(
            install_id
        )

    def delete(self, install_id):

        self.stop(install_id)

        directory = self.path(
            install_id
        )

        if directory.exists():

            shutil.rmtree(
                directory
            )

    def log(self, install_id):

        log_path = (
            self.path(install_id)
            / "factory.log"
        )

        if not log_path.exists():

            return ""

        try:

            return log_path.read_text(
                encoding="utf-8",
                errors="replace",
            )

        except Exception as error:

            return f"Unable to read log: {error}"
