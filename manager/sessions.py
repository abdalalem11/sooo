from pathlib import Path

from telethon import TelegramClient
from telethon.sessions import SQLiteSession, StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError, PhoneNumberInvalidError, FloodWaitError


class SessionManager:
    def __init__(self, accounts_dir):
        self.accounts_dir = Path(accounts_dir)
        self.accounts_dir.mkdir(parents=True, exist_ok=True)
        self.pending = {}

    def session_file(self, install_id):
        return str(
            self.accounts_dir / str(install_id) / "session"
        )

    async def send_code(self, phone, api_id, api_hash):
        key = phone

        client = TelegramClient(
            self.accounts_dir / f".login_{phone.replace('+', '')}",
            api_id,
            api_hash
        )

        await client.connect()

        try:
            result = await client.send_code_request(phone)

        except FloodWaitError as error:
            await client.disconnect()
            raise RuntimeError(
                f"Telegram طلب الانتظار قبل المحاولة مرة أخرى. "
                f"انتظر {error.seconds} ثانية ثم حاول."
            )

        except Exception:
            await client.disconnect()
            raise

        self.pending[key] = {
            "client": client,
            "phone_code_hash": result.phone_code_hash
        }

    async def resend_code(self, phone):
        item = self.pending.get(phone)

        if not item:
            raise RuntimeError(
                "جلسة تسجيل الدخول غير موجودة. أرسل رقم الهاتف من جديد."
            )

        client = item["client"]

        try:
            result = await client.send_code_request(phone)

            item["phone_code_hash"] = result.phone_code_hash

            return result

        except FloodWaitError as error:
            raise RuntimeError(
                f"⏳ Telegram طلب الانتظار {error.seconds} ثانية قبل إعادة إرسال الكود."
            )

        except Exception as error:
            raise RuntimeError(
                f"❌ فشل إعادة إرسال الكود: {error}"
            )

    async def login_code(
        self,
        install_id,
        phone,
        code,
        api_id,
        api_hash,
        password=None
    ):
        item = self.pending.get(phone)

        if not item:
            raise RuntimeError(
                "جلسة تسجيل الدخول انتهت. أرسل الرقم مرة أخرى."
            )

        client = item["client"]

        try:
            if password:
                await client.sign_in(password=password)
            else:
                await client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=item["phone_code_hash"]
                )

        except SessionPasswordNeededError:
            if not password:
                raise

            await client.sign_in(password=password)

        except PhoneCodeInvalidError:
            raise RuntimeError(
                "❌ كود Telegram غير صحيح. أرسل آخر كود وصلك."
            )

        except PhoneCodeExpiredError:
            raise RuntimeError(
                "❌ انتهت صلاحية كود Telegram. "
                "ابدأ تسجيل الدخول من جديد واطلب كودًا جديدًا."
            )

        except FloodWaitError as error:
            raise RuntimeError(
                f"⏳ Telegram طلب الانتظار {error.seconds} ثانية "
                "قبل محاولة تسجيل الدخول مرة أخرى."
            )

        except Exception as error:
            message = str(error)

            if "ResendCodeRequest" in message:
                raise RuntimeError(
                    "⚠️ Telegram رفض إعادة إرسال الكود لأن "
                    "خيارات إرسال الكود المتاحة استُنفدت. "
                    "انتظر قليلًا ثم ابدأ تسجيل الدخول من جديد."
                )

            raise

        target = self.session_file(install_id)
        Path(target).parent.mkdir(parents=True, exist_ok=True)

        # إنشاء SQLite session مستقلة للحساب
        sqlite_session = SQLiteSession(target)

        sqlite_session.set_dc(
            client.session.dc_id,
            client.session.server_address,
            client.session.port
        )

        sqlite_session.auth_key = client.session.auth_key

        if hasattr(client.session, "takeout_id"):
            sqlite_session.takeout_id = client.session.takeout_id

        sqlite_session.save()

        await client.disconnect()

        try:
            Path(str(client.session.filename)).unlink()
        except Exception:
            pass

        self.pending.pop(phone, None)

        return target

    async def from_string(
        self,
        install_id,
        session_string,
        api_id,
        api_hash
    ):
        client = TelegramClient(
            StringSession(session_string),
            api_id,
            api_hash
        )

        await client.connect()

        if not await client.is_user_authorized():
            await client.disconnect()
            raise RuntimeError("Session String غير صالحة.")

        target = self.session_file(install_id)
        Path(target).parent.mkdir(parents=True, exist_ok=True)

        sqlite_session = SQLiteSession(target)

        sqlite_session.set_dc(
            client.session.dc_id,
            client.session.server_address,
            client.session.port
        )

        sqlite_session.auth_key = client.session.auth_key

        if hasattr(client.session, "takeout_id"):
            sqlite_session.takeout_id = client.session.takeout_id

        sqlite_session.save()

        await client.disconnect()

        return target
