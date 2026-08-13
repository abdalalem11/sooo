import base64
import ipaddress
import struct
import sys
from pathlib import Path
from logging import getLogger

from telethon.sessions.string import (
    _STRUCT_PREFORMAT,
    CURRENT_VERSION,
    StringSession,
)
from telethon.sessions import SQLiteSession

LOGS = getLogger("Tepthon")

_PYRO_FORM = {
    351: ">B?256sI?",
    356: ">B?256sQ?",
    362: ">BI?256sQ?",
}


def _pyrogram_session(session):
    DC_IPV4 = {
        1: "149.154.175.53",
        2: "149.154.167.51",
        3: "149.154.175.100",
        4: "149.154.167.91",
        5: "91.108.56.130",
    }

    data_ = struct.unpack(
        _PYRO_FORM[len(session)],
        base64.urlsafe_b64decode(
            session + "=" * (-len(session) % 4)
        ),
    )

    auth_id = 2 if len(session) in {351, 356} else 3
    dc_id, auth_key = data_[0], data_[auth_id]

    return StringSession(
        CURRENT_VERSION
        + base64.urlsafe_b64encode(
            struct.pack(
                _STRUCT_PREFORMAT.format(4),
                dc_id,
                ipaddress.ip_address(
                    DC_IPV4[dc_id]
                ).packed,
                443,
                auth_key,
            )
        ).decode("ascii")
    )


def _telethon_file_session(path):
    """
    تحميل جلسة Telethon SQLite من ملف .session.
    """

    path = Path(path)

    if not path.exists():
        raise RuntimeError(
            f"ملف Session غير موجود: {path}"
        )

    if not path.is_file():
        raise RuntimeError(
            f"مسار Session ليس ملفًا: {path}"
        )

    try:
        session = SQLiteSession(str(path))

        if not session.auth_key:
            session.close()

            raise RuntimeError(
                "ملف Session موجود لكنه غير مصادق عليه."
            )

        return session

    except Exception as error:
        raise RuntimeError(
            f"تعذر فتح ملف Session: {error}"
        ) from error


def both_session(session, logger=LOGS, _exit=True):
    if not session:
        message = (
            "⚠️ لم يتم العثور على كود Session."
        )

        logger.error(message)

        if _exit:
            sys.exit(1)

        return None

    session = str(session).strip()

    # ==========================================
    # Telethon SQLite Session file
    # ==========================================

    session_path = Path(session)

    if session_path.exists():
        try:
            return _telethon_file_session(
                session_path
            )
        except Exception as error:
            logger.error(
                f"✖️ فشل فتح ملف Session: {error}"
            )

            if _exit:
                sys.exit(1)

            return None

    # ==========================================
    # Telethon StringSession
    # ==========================================

    if session.startswith(CURRENT_VERSION):
        try:
            return StringSession(session)
        except Exception as error:
            logger.error(
                f"✖️ Session String غير صالحة: {error}"
            )

            if _exit:
                sys.exit(1)

            return None

    # ==========================================
    # Pyrogram Session String
    # ==========================================

    if len(session) in _PYRO_FORM:
        try:
            return _pyrogram_session(session)
        except Exception as error:
            logger.error(
                f"✖️ تعذر تحويل Pyrogram Session: {error}"
            )

            if _exit:
                sys.exit(1)

            return None

    # ==========================================
    # Invalid Session
    # ==========================================

    logger.error(
        "✖️ كود السيشن غير صحيح، "
        "يرجى التأكد من إدخاله بالشكل الصحيح."
    )

    if _exit:
        sys.exit(1)

    return None
