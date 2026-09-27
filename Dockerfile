# استخدام نسخة بايثون 3.11 الرسمية والمستقرة والمبنية على نظام دبيان
FROM python:3.11-slim

# تثبيت الاعتماديات الرسومية والأدوات الأساسية التي يحتاجها متصفح Playwright للعمل في وضع headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfix6 \
    librandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# إعداد مجلد العمل داخل السيرفر
WORKDIR /app

# نسخ ملف الاعتماديات أولاً لتسريع عملية البناء عبر الـ Cache
COPY requirements.txt .

# تحديث أداة التثبيت وتثبيت الحزم البرمجية المستقرة بنجاح
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# تثبيت محرك متصفح Chromium المخصص لـ Playwright مع تعريفاته
RUN playwright install chromium

# نسخ باقي ملفات المشروع البرمجية (bot.py و lab_engine.py) إلى السيرفر
COPY . .

# الأمر النهائي لتشغيل بوت التليجرام بشكل مستمر
CMD ["python", "bot.py"]
