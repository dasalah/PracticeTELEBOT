# ربات تلگرام ثبتنام رویداد

ربات تلگرام کاملی برای مدیریت ثبت‌نام کاربران در رویدادها با امکانات پیشرفته.

## ویژگی‌های اصلی

### 1. مدیریت رویدادها
- ایجاد رویداد جدید توسط ادمین
- ویرایش و حذف رویدادها
- مدیریت وضعیت رویداد (فعال/غیرفعال/تمام‌شده/منقضی)
- تولید لینک اختصاری یکتا برای هر رویداد
- مدیریت ظرفیت رویدادها

### 2. فرآیند ثبت‌نام کاربران
- نمایش اطلاعات کامل رویداد
- دریافت اطلاعات شخصی:
  - نام و نام خانوادگی
  - کد ملی (با validation ایرانی)
  - شماره تلفن ایرانی
  - عکس یا متن فیش واریزی
- پشتیبانی از اعداد فارسی
- چک تکراری بودن ثبت‌نام

### 3. سیستم تایید ادمین
- ارسال اطلاعات کاربر به ادمین‌ها
- امکان تایید یا رد ثبت‌نام
- ارسال اعلان به کاربر
- ذخیره اطلاعات در دیتابیس

### 4. مدیریت ادمین‌ها
- سطوح مختلف دسترسی (ادمین اصلی/ادمین عادی)
- افزودن/حذف ادمین
- مدیریت دسترسی‌ها

### 5. گزارشگیری و آمار
- Export به Excel
- آمار کلی سیستم
- مشاهده لیست ثبت‌نام‌شدگان
- لاگ فعالیت‌ها و پیام‌ها

## نصب و راه‌اندازی

### پیش‌نیازها
```bash
pip install -r requirements.txt
```

### تنظیمات اولیه

1. **تنظیم config.py**:
```python
api_id = YOUR_API_ID
api_hash = "YOUR_API_HASH"
token = "YOUR_BOT_TOKEN"
```

2. **اضافه کردن ادمین اصلی**:
```bash
python admin_manager.py
```

3. **اجرای ربات**:
```bash
python main.py
```

## ساختار دیتابیس

### Users Table
- user_id (Primary Key)
- telegram_id
- first_name
- last_name
- national_code
- phone_number
- created_at

### Events Table
- event_id (Primary Key)
- name
- description
- poster_path
- amount
- card_number
- capacity
- registered_count
- status
- start_date
- end_date
- unique_code
- created_at

### Registrations Table
- registration_id (Primary Key)
- user_id (Foreign Key)
- event_id (Foreign Key)
- status (pending/approved/rejected)
- payment_receipt_path
- payment_receipt_text
- registration_date
- approval_date

### Admins Table
- admin_id (Primary Key)
- telegram_id
- is_super_admin
- created_at

### Activity Logs & Message Logs
برای پیگیری فعالیت‌ها و پیام‌ها

## دستورات ادمین

### ادمین عادی
- `/create_event` - ایجاد رویداد جدید
- `/list_events` - مشاهده لیست رویدادها
- `/stats` - آمار سیستم

### ادمین اصلی
- همه دستورات ادمین عادی +
- `/add_admin` - افزودن ادمین جدید

## ویژگی‌های امنیتی

- Validation کامل کد ملی ایرانی
- چک تکراری بودن ثبت‌نام
- لاگ کامل فعالیت‌ها
- سطوح دسترسی مختلف ادمین
- ذخیره ایمن فیش‌های واریزی

## فایل‌های مهم

- `main.py` - فایل اصلی ربات
- `userDB.py` - مدل‌های دیتابیس
- `event_manager.py` - مدیریت رویدادها
- `registration_manager.py` - مدیریت ثبت‌نام
- `admin_approval.py` - سیستم تایید ادمین
- `utils.py` - توابع کمکی و validation
- `admin_manager.py` - مدیریت ادمین‌ها

## مثال استفاده

1. ادمین رویداد جدید ایجاد می‌کند
2. لینک اختصاری تولید می‌شود
3. کاربر روی لینک کلیک می‌کند
4. مبلغ را واریز می‌کند
5. اطلاعات خود را وارد می‌کند
6. فیش واریزی را ارسال می‌کند
7. ادمین درخواست را تایید/رد می‌کند
8. کاربر اعلان دریافت می‌کند

## پشتیبانی

برای پشتیبانی و سوالات با ادمین در تماس باشید.