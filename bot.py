import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from lab_engine import automate_lab_and_deploy

# إعداد توكن البوت
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# تخزين مؤقت لحالات المستخدمين وجلسات العمل
user_sessions = {}

# قائمة بالمناطق الشائعة والمتاحة لـ Cloud Run ليختار المستخدم منها يدوياً
AVAILABLE_REGIONS = [
    ("🇺🇸 US East 1 (N. Virginia)", "us-east1"),
    ("🇺🇸 US Central 1 (Iowa)", "us-central1"),
    ("🇪🇺 Europe West 1 (Belgium)", "europe-west1"),
    ("🇪🇺 Europe West 3 (Frankfurt)", "europe-west3"),
    ("🌏 Asia East 1 (Taiwan)", "asia-east1"),
    ("🌏 Asia Northeast 1 (Tokyo)", "asia-northeast1")
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ **مرحباً بك سيدي في نظام أتمتة المختبرات المتكامل** ⚡\n\n"
        "لتشغيل الحاوية الخاصة بك تلقائياً بالإعدادات المطلوبة، يرجى إرسال رابط المختبر (Qwiklabs) مباشرة في الشات."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        await update.message.reply_text("❌ يرجى إرسال رابط مختبر صحيح سيدي.")
        return

    # حفظ الرابط في جلسة المستخدم الحالية
    user_sessions[update.effective_user.id] = {"lab_url": url}

    # توليد أزرار اختيار المنطقة يدوياً (Region Selection)
    keyboard = []
    for name, code in AVAILABLE_REGIONS:
        keyboard.append([InlineKeyboardButton(name, callback_data=f"region_{code}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📍 **الرجاء تحديد المنطقة (Region) المطلوبة لنشر الـ Cloud Run يدوياً:**", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id not in user_sessions:
        await query.edit_message_text("❌ انتهت الجلسة أو حدث خطأ. يرجى إرسال الرابط من جديد.")
        return

    if query.data.startswith("region_"):
        selected_region = query.data.split("_")[1]
        user_sessions[user_id]["region"] = selected_region
        
        lab_url = user_sessions[user_id]["lab_url"]
        
        await query.edit_message_text(f"⏳ **جاري بدء المعالجة الذكية...**\n"
                                      f"🔹 المنطقة المختارة: `{selected_region}`\n"
                                      f"🔹 يتم الآن فتح صفحة المختبر وتوليد الحساب ونشر الخدمة بكافة الخصائص المطلوبة الفائقة تلقائياً. يرجى الانتظار...", parse_mode="Markdown")
        
        # تنفيذ الأتمتة الكاملة خلف الكواليس
        # ملاحظة: إذا كان المختبر يتطلب حساب Qwiklabs خاص بك لتسجيل الدخول مرره هنا، وإلا اتركها None إذا كانت الصفحة مفتوحة عامة
        result = automate_lab_and_deploy(lab_url, selected_region, qwiklabs_email=None, qwiklabs_password=None)
        
        if result["success"]:
            await query.message.reply_text(
                f"✅ **تم إنشاء وتشغيل مشروعك بنجاح وبدون أي قيود!**\n\n"
                f"⚙️ **تفاصيل النشر:**\n"
                f"• اسم الخدمة: `mustapha35`\n"
                f"• الحاوية: `winda2635/mustapha-vless-xhttp:latest`\n"
                f"• المنافذ: `8080`\n"
                f"• المعالج والذاكرة: `1 CPU | 1 GiB` (مخصصة دائماً)\n"
                f"• جيل البيئة: `Second Generation`\n"
                f"• النطاق الترددي (Autoscaling): `1 - 16 Instances`\n"
                f"• الوصول: `Allow public access (All Ingress)`\n"
                f"• معرف المشروع المؤقت: `{result['project_id']}`\n\n"
                f"🔗 **رابط الـ Cloud Run المباشر:**\n{result['url']}",
                parse_mode="Markdown"
            )
        else:
            await query.message.reply_text(f"❌ حدث خطأ أثناء تنفيذ النشر التلقائي:\n`{result['error']}`", parse_mode="Markdown")
            
        # تنظيف الجلسة
        user_sessions.pop(user_id, None)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("[+] Smart Lab Bot with advanced Custom Cloud Run configs is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
