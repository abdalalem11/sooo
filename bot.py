import asyncio
from datetime import datetime,timedelta,timezone
from aiogram import Router,F
from aiogram.filters import CommandStart,Command
from aiogram.types import Message,CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

router=Router()

def menu():
    b=InlineKeyboardBuilder()
    for text,data in [('➕ تنصيب','new'),('📋 حساباتي','list'),('▶️ تشغيل','start'),('⛔ إيقاف','stop'),('🔄 إعادة تشغيل','restart'),('🗑 حذف','delete')]: b.button(text=text,callback_data=data)
    b.adjust(2); return b.as_markup()

def setup(dp,db,pm,owner):
    dp.include_router(router)
    def allowed(m): return m.from_user and m.from_user.id==owner
    @router.message(CommandStart())
    async def start(m:Message):
        if not allowed(m): return await m.answer('⛔ غير مصرح.')
        await m.answer('🤖 <b>Tepthon Factory</b>\n\nإدارة نسخ مستقلة من Tepthon.',reply_markup=menu())
    @router.callback_query(F.data=='new')
    async def new(c:CallbackQuery):
        if c.from_user.id!=owner:return await c.answer('غير مصرح',show_alert=True)
        await c.message.answer('أرسل: <code>/install اسم 30</code>\nالاسم بدون مسافات.')
        await c.answer()
    @router.message(Command('install'))
    async def install(m:Message):
        if not allowed(m):return
        p=m.text.split()
        if len(p)!=3 or not p[2].isdigit() or int(p[2])<1:return await m.answer('الاستخدام: /install name 30')
        name=p[1]; days=int(p[2]); exp=datetime.now(timezone.utc)+timedelta(days=days)
        iid=db.add(owner,name,exp.isoformat())
        try: pm.create(iid)
        except Exception as e:
            db.delete(iid,owner); return await m.answer(f'❌ فشل إنشاء القالب: <code>{e}</code>')
        await m.answer(f'✅ تم إنشاء التنصيب #{iid}\n📦 {name}\n📅 {days} يوم\n⏰ {exp:%Y-%m-%d %H:%M UTC}\n\nشغّله من القائمة.')
    @router.callback_query(F.data=='list')
    async def listing(c:CallbackQuery):
        if c.from_user.id!=owner:return
        rows=db.list(owner)
        text='📋 <b>التنصيبات</b>\n\n'+('\n'.join(f"#{r['id']} — {r['name']} — {r['status']} — {r['expires_at'][:16]}" for r in rows) if rows else 'لا يوجد')
        await c.message.edit_text(text,reply_markup=menu()); await c.answer()
    async def action(c,kind):
        if c.from_user.id!=owner:return await c.answer('غير مصرح',show_alert=True)
        await c.message.answer(f'أرسل <code>/id {kind} رقم</code>\nمثال: <code>/id {kind} 1</code>'); await c.answer()
    for kind in ('start','stop','restart','delete'):
        router.callback_query(F.data==kind)(lambda c,k=kind: action(c,k))
    @router.message(Command('id'))
    async def do(m:Message):
        if not allowed(m):return
        p=m.text.split();
        if len(p)!=3 or not p[2].isdigit():return await m.answer('مثال: /id start 1')
        kind=p[1]; iid=int(p[2]); row=db.get(iid,owner)
        if not row:return await m.answer('❌ الحساب غير موجود')
        try:
            if kind=='start': pid=pm.start(iid); db.set_status(iid,owner,'running'); out=f'▶️ يعمل الآن PID={pid}'
            elif kind=='stop': pm.stop(iid); db.set_status(iid,owner,'stopped'); out='⛔ تم الإيقاف'
            elif kind=='restart': pid=pm.restart(iid); db.set_status(iid,owner,'running'); out=f'🔄 تمت إعادة التشغيل PID={pid}'
            elif kind=='delete': pm.delete(iid); db.delete(iid,owner); out='🗑 تم الحذف'
            else: out='❌ الأمر غير صحيح'
        except Exception as e: out=f'❌ {e}'
        await m.answer(out)
