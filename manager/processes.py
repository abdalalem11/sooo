import os, shutil, subprocess, signal
from pathlib import Path

class ProcessManager:
    def __init__(self, template_dir, accounts_dir):
        self.template=Path(template_dir); self.accounts=Path(accounts_dir); self.accounts.mkdir(parents=True,exist_ok=True); self.procs={}
    def path(self,iid): return self.accounts / str(iid)
    def create(self,iid):
        if not self.template.exists(): raise RuntimeError(f'Template not found: {self.template}')
        dst=self.path(iid)
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(self.template,dst)
        return dst
    def start(self,iid):
        p=self.path(iid)
        if not p.exists(): raise RuntimeError('Account directory does not exist')
        self.stop(iid)
        env=os.environ.copy(); env['FACTORY_INSTALL_ID']=str(iid)
        log=open(p/'factory.log','a',encoding='utf-8')
        proc=subprocess.Popen(['python','-u','main.py'],cwd=p,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        self.procs[iid]=(proc,log); return proc.pid
    def stop(self,iid):
        item=self.procs.pop(iid,None)
        if not item: return
        proc,log=item
        try: os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError: pass
        try: proc.wait(timeout=8)
        except Exception: pass
        log.close()
    def restart(self,iid): self.stop(iid); return self.start(iid)
    def delete(self,iid): self.stop(iid); shutil.rmtree(self.path(iid),ignore_errors=True)
