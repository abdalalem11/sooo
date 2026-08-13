import os
import signal
import shutil
import subprocess
import sys
from pathlib import Path


class ProcessManager:
    def __init__(self, accounts_dir, template_dir):
        self.accounts = Path(accounts_dir)
        self.template = Path(template_dir)

        self.accounts.mkdir(parents=True, exist_ok=True)

        self.processes = {}

    def create(self, install_id):
        if not self.template.exists():
            raise RuntimeError(
                f"Tepthon غير موجود في {self.template}"
            )

        destination = self.accounts / str(install_id)

        if destination.exists():
            shutil.rmtree(destination)

        shutil.copytree(
            self.template,
            destination
        )

        return destination

    def start(self, install_id):
        directory = self.accounts / str(install_id)

        package = directory / "Tepthon"
        database = directory / "database"

        if not package.exists():
            raise RuntimeError(
                f"مجلد Tepthon غير موجود داخل {directory}"
            )

        if not (package / "__main__.py").exists():
            raise RuntimeError(
                f"Tepthon/__main__.py غير موجود داخل {directory}"
            )

        if not database.exists():
            raise RuntimeError(
                f"مجلد database غير موجود داخل {directory}"
            )

        old = self.processes.get(install_id)

        if old and old.poll() is None:
            return old.pid

        log_path = directory / "factory.log"

        log = open(
            log_path,
            "a",
            encoding="utf-8"
        )

        env = os.environ.copy()

        # معلومات المصنع
        env["FACTORY_INSTALL_ID"] = str(install_id)
        env["FACTORY_ACCOUNT_DIR"] = str(
            directory.absolute()
        )

        # جلسة الحساب الخاصة بهذا التنصيب
        session_path = directory / "session"

        env["SESSION"] = str(
            session_path.absolute()
        )

        # مهم جدًا:
        # لا نرسل PORT إلى Tepthon الفرعي.
        # الـ PORT مخصص لبوت المصنع نفسه على Render.
        env.pop("PORT", None)

        # تشغيل Tepthon كـ package
        command = [
            sys.executable,
            "-u",
            "-m",
            "Tepthon",
        ]

        process = subprocess.Popen(
            command,
            cwd=directory,
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )

        self.processes[install_id] = process

        return process.pid

    def stop(self, install_id):
        process = self.processes.get(install_id)

        if not process:
            return

        if process.poll() is not None:
            self.processes.pop(
                install_id,
                None
            )
            return

        try:
            os.killpg(
                process.pid,
                signal.SIGTERM
            )
        except Exception:
            try:
                process.terminate()
            except Exception:
                pass

        self.processes.pop(
            install_id,
            None
        )

    def restart(self, install_id):
        self.stop(install_id)

        return self.start(install_id)

    def delete(self, install_id):
        self.stop(install_id)

        directory = self.accounts / str(install_id)

        if directory.exists():
            shutil.rmtree(directory)
