import shutil
from pathlib import Path

from telethon import TelegramClient
from telethon.sessions import StringSession, SQLiteSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    SendCodeUnavailableError,
)


class SessionManager:
    def __init__(self, accounts_dir):
        self.accounts_dir = Path(accounts_dir)
        self.accounts_dir.mkdir(parents=True, exist_ok=True)

        self.clients = {}
        self.phone_hashes = {}

    def _pending_path(self, phone):
        safe_phone = "".join(c for c in phone if c.isdigit())
        return self.accounts_dir / f".pending_{safe_phone}"

    def _session_path(self, install_id):
        directory = self.accounts_dir / str(install_id)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / "session"

    async def send_code(self, phone, api_id, api_hash):
        old_client = self.clients.pop(phone, None)
        self.phone_hashes.pop(phone, None)

        if old_client is not None:
            try:
                if old_client.is_connected():
                    await old_client.disconnect()
            except Exception:
                pass

        pending = self._pending_path(phone)

        for path in (
            pending,
            Path(str(pending) + ".session"),
        ):
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass

        client = TelegramClient(
            str(pending),
            api_id,
            api_hash,
        )

        await client.connect()

        try:
            result = await client.send_code_request(phone)
        except Exception:
            try:
                await client.disconnect()
            except Exception:
                pass
            raise

        self.clients[phone] = client
        self.phone_hashes[phone] = result.phone_code_hash

        return result

    async def resend_code(self, phone):
        client = self.clients.get(phone)

        if client is None:
            raise RuntimeError(
                "جلسة التحقق غير موجودة. ابدأ التنصيب من جديد."
            )

        if not client.is_connected():
            await client.connect()

        try:
            result = await client.send_code_request(phone)
        except SendCodeUnavailableError:
            raise RuntimeError(
                "Telegram لا يسمح بإرسال كود جديد لهذا الرقم حاليًا."
            )

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
                "جلسة التحقق غير موجودة. ابدأ التنصيب من جديد."
            )

        if not client.is_connected():
            await client.connect()

        try:
            if password:
                await client.sign_in(password=password)
            else:
                phone_code_hash = self.phone_hashes.get(phone)

                if not phone_code_hash:
                    raise RuntimeError(
                        "كود التحقق غير موجود. أرسل كودًا جديدًا."
                    )

                await client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=phone_code_hash,
                )

        except SessionPasswordNeededError:
            raise

        except PhoneCodeExpiredError:
            raise RuntimeError(
                "انتهت صلاحية كود Telegram. أعد إرسال الكود."
            )

        except PhoneCodeInvalidError:
            raise RuntimeError(
                "كود Telegram غير صحيح."
            )

        if not await client.is_user_authorized():
            raise RuntimeError("فشل التحقق من الحساب.")

        client.session.save()

        pending_file = Path(
            str(self._pending_path(phone)) + ".session"
        )

        target_file = Path(
            str(self._session_path(install_id)) + ".session"
        )

        await client.disconnect()

        self.clients.pop(phone, None)
        self.phone_hashes.pop(phone, None)

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

        return str(self._session_path(install_id))

    async def install_string_session(
        self,
        install_id,
        session_string,
        api_id,
        api_hash,
    ):
        session_string = session_string.strip()

        if not session_string:
            raise RuntimeError("Session String فارغة.")

        try:
            source_session = StringSession(session_string)

            client = TelegramClient(
                source_session,
                api_id,
                api_hash,
            )

            await client.connect()

            if not await client.is_user_authorized():
                await client.disconnect()
                raise RuntimeError(
                    "Session String غير صالحة أو غير مسجلة الدخول."
                )

            target_base = self._session_path(install_id)
            target_base.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            target = SQLiteSession(str(target_base))

            target.set_dc(
                client.session.dc_id,
                client.session.server_address,
                client.session.port,
            )

            target.auth_key = client.session.auth_key

            if hasattr(client.session, "takeout_id"):
                target.takeout_id = client.session.takeout_id

            target.save()

            await client.disconnect()

            target_file = Path(str(target_base) + ".session")

            if not target_file.exists():
                raise RuntimeError(
                    "تعذر إنشاء ملف Session للحساب."
                )

            return str(target_base)

        except Exception as error:
            raise RuntimeError(
                f"فشل تحويل Session String: {error}"
            ) from error

    async def close(self):
        for client in list(self.clients.values()):
            try:
                if client.is_connected():
                    await client.disconnect()
            except Exception:
                pass

        self.clients.clear()
        self.phone_hashes.clear()
