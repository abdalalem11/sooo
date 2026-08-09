# Tepthon Factory Bot

بوت مصنع لإدارة نسخ مستقلة من Tepthon. لا تضع BOT_TOKEN داخل GitHub؛ ضعه في Render Environment Variables.

## المتغيرات
BOT_TOKEN=توكن البوت الجديد
OWNER_ID=رقم حساب المالك
PORT=10000
TEMPLATE_DIR=template/Tepthon
ACCOUNTS_DIR=data/accounts
DB_PATH=data/factory.db

## التشغيل
pip install -r requirements.txt
python main.py

ضع نسخة Tepthon التي تريد تشغيلها داخل `template/Tepthon`.

كل تنصيب يحصل على مجلد مستقل، ويمكن تشغيله وإيقافه وإعادة تشغيله وحذفه وتحديد تاريخ الانتهاء.
