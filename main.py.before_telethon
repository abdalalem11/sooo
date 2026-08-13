import os,asyncio,logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
from aiogram import Bot,Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from database import DB
from manager.processes import ProcessManager
from bot import setup
load_dotenv(); logging.basicConfig(level=logging.INFO)
token=os.getenv('BOT_TOKEN'); owner=int(os.getenv('OWNER_ID','0')); port=int(os.getenv('PORT','10000'))
db=DB(os.getenv('DB_PATH','data/factory.db')); pm=ProcessManager(os.getenv('TEMPLATE_DIR','template/Tepthon'),os.getenv('ACCOUNTS_DIR','data/accounts'))
bot=Bot(token,default=DefaultBotProperties(parse_mode=ParseMode.HTML)); dp=Dispatcher(); setup(dp,db,pm,owner)
@asynccontextmanager
async def life(app):
    task=asyncio.create_task(dp.start_polling(bot))
    yield
    task.cancel(); await bot.session.close()
app=FastAPI(lifespan=life)
@app.get('/')
async def root(): return {'status':'ok','service':'Tepthon Factory'}
@app.get('/health')
async def health(): return {'status':'healthy'}
if __name__=='__main__': uvicorn.run(app,host='0.0.0.0',port=port)
