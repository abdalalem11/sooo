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
        self.accounts.mkdir(parents=True, exist_ok=True)
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

        shutil.copytree(self.template, destination)

        return destination

    def start(self, install_id):
        directory = self.path(install_id)

        if not directory.exists():
            raise RuntimeError(
                f"Account directory does not exist: {directory}"
            )

        package = directory / "Tepthon"

        if not package.exists():
            raise RuntimeError(
                f"Tepthon package not found: {package}"
            )

        if not (package / "__main__.py").exists():
            raise RuntimeError(
                "Tepthon/__main__.py غير موجود."
            )

        # Telethon SQLite session تكون عادةً:
        # session.session
        session_base = directory / "session"
        session_file = directory / "session.session"

        if not session_file.exists():
            # دعم أي ملف session موجود داخل مجلد الحساب
            candidates = list(directory.glob("*.session"))

            if candidates:
                session_file = candidates[0]
                session_base = session_file.with_suffix("")
            else:
                raise RuntimeError(
                    f"Session غير موجودة للحساب {install_id}. "
                    "سجّل الدخول أولاً من المصنع."
                )

        self.stop(install_id)

        env = os.environ.copy()

        env["FACTORY_INSTALL_ID"] = str(install_id)
        env["FACTORY_ACCOUNT_DIR"] = str(directory.absolute())

        # نعطي Tepthon مسار ملف الجلسة الفعلي
        env["SESSION"] = str(session_file.absolute())

        env["REDISHOST"] = os.getenv(
            "REDISHOST",
            "127.0.0.1",
        )

        env["REDISPORT"] = os.getenv(
            "REDISPORT",
            "6379",
        )

        # PORT خاص بالمصنع الرئيسي
        env.pop("PORT", None)

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
                "-m",
                "Tepthon",
            ],
            cwd=directory,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
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

        if process.poll() is None:
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
                    try:
                        process.kill()
                    except Exception:
                        pass

        try:
            log_file.close()
        except Exception:
            pass

    def restart(self, install_id):
        self.stop(install_id)
        return self.start(install_id)

    def delete(self, install_id):
        self.stop(install_id)

        directory = self.path(install_id)

        if directory.exists():
            shutil.rmtree(directory)

    def log(self, install_id):
        log_path = self.path(install_id) / "factory.log"

        if not log_path.exists():
            return ""

        try:
            return log_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except Exception as error:
            return f"Unable to read log: {error}"
