"""
❃ `{i}لوك`
    لـ عرض آخر أسطر من عملية التنصيب وعرض سجل العمليات

❃ `{i}اعادة تشغيل`
    لـ إعـادة تشغيل سورس النسر الاسود

❃ `{i}تحديث`
    لـ تحديث سورس النسرالاسود من GitHub

© @SSSTlF
"""

import os
import sys
import subprocess

from Tepthon.helper import get_client
from .. import Tepthon_cmd


REPO_URL = "https://github.com/abdalalem11/Tepthon.git"


@Tepthon_cmd(pattern="لوك( (.*)|$)")
async def logs_Tepthon(event):
    arg = event.pattern_match.group(1).strip()

    file_path = "tepthon logs"

    if not arg:
        with open(file_path, "r") as file:
            content = file.read()[-4000:]

        return await event.eor(f"`{content}`")

    elif arg == "تلجراف":
        client = get_client()

        with open(file_path, "r") as file:
            title = "Tepthon Logs"
            page = client.create_page(
                title=title,
                content=[file.read()]
            )

        return await event.eor(
            f'[Tepthon Logs]({page["url"]})',
            link_preview=True
        )

    await event.eor(file=file_path)


@Tepthon_cmd(pattern="اعادة تشغيل$")
async def restart_Tepthon(event):
    await event.eor(
        "⎆ جاري إعادة تشغيل سورس النسرالاسود.....\n\n"
        "© @SSSTlF"
    )

    os.execl(
        sys.executable,
        sys.executable,
        "-m",
        "Tepthon"
    )


@Tepthon_cmd(pattern="تحديث( (.*)|$)")
async def update_Tepthon(event):

    msg = await event.eor(
        "**⎆ جاري التحقق من تحديثات سورس النسر الاسود...**\n\n"
        "© @SSSTlF"
    )

    # التحديث من مستودع Tepthon الرسمي المحدد
    process = subprocess.run(
        ["git", "pull", REPO_URL, "main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if process.returncode != 0:
        return await msg.edit(
            "**❌ فشل تحديث سورس النسر الاسود.**\n\n"
            f"`{process.stderr[-1500:]}`\n\n"
            "© @SSSTlF"
        )

    await msg.edit(
        "**✅ تم تحديث سورس النسر الاسود بنجاح.**\n\n"
        "⎆ جاري إعادة التشغيل...\n\n"
        "© @SSSTlF"
    )

    os.execl(
        sys.executable,
        sys.executable,
        "-m",
        "Tepthon"
    )
