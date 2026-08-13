import shutil
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError


class SessionManager:
    def __init__(self, accounts_dir):
        self.accounts_dir = Path(accounts_dir)
        self.accounts_dir.mkdir(parents=True, exist_ok=True)

        self.clients = {}
        self.phone_hashes = {}

    def _pending_path(self, phone):
        safe_phone = "".join(
            c for c in phone
            if c.isdigit()
        )
        return self.accounts_dir / f".pending_{safe_phone}"

    def _session_path(self, install_id):
        directory = self.accounts_dir / str(install_id)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / "session"

    async def send_code(self, phone, api_id, api_hash):
        pending = self._pending_path(phone)

        client = TelegramClient(
            str(pending),
            api_id,
            api_hash,
        )

        await client.connect()

        result = await client.send_code_request(phone)

        self.clients[phone] = client
        self.phone_hashes[phone] = result.phone_code_hash

        return result

    async def resend_code(self, phone):
        client = self.clients.get(phone)

        if client is None:
            raise RuntimeError(
                "جلسة التحقق غير موجودة. "
                "ابدأ التنصيب من جديد."
            )

        if not client.is_connected():
            await client.connect()

        result = await client.send_code_request(phone)

        self.phone_hashes[phone] = result.phone_code_hash

        return result

    async def login_code(
        self,
        install_id,
        phone,
        code,
        api_id,
        api_hash,
        password=None,
    ):
        client = self.clients.get(phone)

        if client is None:
            raise RuntimeError(
                "جلسة التحقق غير موجودة. "
                "ابدأ التنصيب من جديد."
            )

        if not client.is_connected():
            await client.connect()

        try:
            if password:
                await client.sign_in(
                    password=password
                )
            else:
                phone_code_hash = self.phone_hashes.get(phone)

                if not phone_code_hash:
                    raise RuntimeError(
                        "كود التحقق غير موجود أو انتهت صلاحيته."
                    )

                try:
                    await client.sign_in(
                        phone=phone,
                        code=code,
                        phone_code_hash=phone_code_hash,
                    )
                except SessionPasswordNeededError:
                    raise

        except SessionPasswordNeededError:
            raise

        if not await client.is_user_authorized():
            raise RuntimeError(
                "فشل التحقق من الحساب."
            )

        # حفظ جلسة Telethon قبل نسخها
        client.session.save()

        pending_file = Path(
            str(self._pending_path(phone)) + ".session"
        )

        target_file = Path(
            str(self._session_path(install_id)) + ".session"
        )

        # إغلاق العميل حتى يتم تحرير ملف SQLite
        await client.disconnect()

        if not pending_file.exists():
            raise RuntimeError(
                "ملف جلسة Telegram لم يتم إنشاؤه."
            )

        target_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            pending_file,
            target_file,
        )

        # ProcessManager يستخدم المسار بدون امتداد
        target = self._session_path(install_id)

        # Telethon سيبحث عن target.session
        return str(target)

    async def close(self):
        for client in list(self.clients.values()):
            try:
                if client.is_connected():
                    await client.disconnect()
            except Exception:
                pass

        self.clients.clear()
        self.phone_hashes.clear()
