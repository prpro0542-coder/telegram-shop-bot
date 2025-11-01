import sqlite3
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# توکن ربات - همین توکن خودتان را استفاده کنید
TOKEN = '8088141391:AAHRJ5RQxk86NR5hnX2y1zRXB03jfBBdrgc'
ADMIN_CHAT_ID = 5906972432

def init_db():
    conn = sqlite3.connect('accessory_shop.db', check_same_thread=False, timeout=30)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY, user_id INTEGER, user_name TEXT, phone TEXT, 
                  product TEXT, quantity INTEGER, address TEXT, status TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL, 
                  description TEXT, stock INTEGER, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (id INTEGER PRIMARY KEY, order_id INTEGER, user_id INTEGER, 
                  rating INTEGER, comment TEXT, created_at TEXT)''')
    
    # اضافه کردن محصولات نمونه اگر وجود ندارند
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        sample_products = [
            ('قاب سیلیکونی آیفون 15', 'case', 120000, 'قاب سیلیکونی با کیفیت عالی', 50),
            ('کاور چرمی گلکسی S24', 'case', 180000, 'کاور چرمی اصل', 30),
            ('کابل اورجینال تایپ سی', 'charging', 75000, 'کابل اورجینال با گارانتی', 100),
            ('شارژر فست شارژ 45 وات', 'charging', 150000, 'شارژر سریع', 40),
            ('هدفون بی‌سیم اپل', 'audio', 450000, 'هدفون اصلی اپل', 20),
            ('هندزفری بلوتوث سامسونگ', 'audio', 220000, 'هندزفری با کیفیت', 35),
            ('محافظ شیشه ای آیفون', 'screen', 65000, 'محافظ شیشه ای 9H', 80),
            ('محافظ نانو شیائومی', 'screen', 45000, 'محافظ نانو ضد خش', 60),
            ('پاوربانک 10000 میلی‌آمپر', 'powerbank', 280000, 'پاوربانک فست شارژ', 30),
            ('پاوربانک فست شارژ 20000', 'powerbank', 420000, 'پاوربانک ظرفیت بالا', 25)
        ]
        c.executemany('''INSERT INTO products (name, category, price, description, stock, created_at)
                         VALUES (?, ?, ?, ?, ?, ?)''', 
                     [(name, cat, price, desc, stock, datetime.now().isoformat()) for name, cat, price, desc, stock in sample_products])
    
    conn.commit()
    conn.close()

init_db()
user_states = {}

def get_db_connection():
    return sqlite3.connect('accessory_shop.db', check_same_thread=False, timeout=30)

def admin_main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 آمار فروشگاه", callback_data="stats")],
        [InlineKeyboardButton("📦 سفارشات جدید", callback_data="new_orders")],
        [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="manage_products")],
        [InlineKeyboardButton("⭐ نظرات مشتریان", callback_data="view_reviews")],
        [InlineKeyboardButton("📞 تماس با مشتریان", callback_data="contact_customers")],
        [InlineKeyboardButton("🔄 ریست سیستم", callback_data="reset_system")]
    ]
    return InlineKeyboardMarkup(keyboard)

def user_main_menu():
    keyboard = [
        [InlineKeyboardButton("🛒 خرید محصولات", callback_data="shop_products")],
        [InlineKeyboardButton("📦 پیگیری سفارش", callback_data="track_order")],
        [InlineKeyboardButton("⭐ ثبت نظر", callback_data="add_review")],
        [InlineKeyboardButton("📚 راهنمای خرید", callback_data="shopping_guide")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="user_support")]
    ]
    return InlineKeyboardMarkup(keyboard)

def product_categories_menu():
    keyboard = [
        [InlineKeyboardButton("📱 قاب و کاور", callback_data="category_case")],
        [InlineKeyboardButton("⚡ کابل و شارژر", callback_data="category_charging")],
        [InlineKeyboardButton("🎧 هدفون و هندزفری", callback_data="category_audio")],
        [InlineKeyboardButton("🖥️ محافظ صفحه", callback_data="category_screen")],
        [InlineKeyboardButton("🔋 پاوربانک", callback_data="category_powerbank")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_user_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def phone_keyboard():
    keyboard = [
        [KeyboardButton("📱 اشتراک‌گذاری شماره تلفن", request_contact=True)],
        [KeyboardButton("📝 وارد کردن دستی شماره")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def rating_keyboard():
    keyboard = [
        [InlineKeyboardButton("⭐", callback_data="rate_1"),
         InlineKeyboardButton("⭐⭐", callback_data="rate_2"),
         InlineKeyboardButton("⭐⭐⭐", callback_data="rate_3")],
        [InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rate_4"),
         InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rate_5")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_user_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def category_selection_keyboard():
    keyboard = [
        [InlineKeyboardButton("📱 قاب و کاور", callback_data="new_category_case")],
        [InlineKeyboardButton("⚡ کابل و شارژر", callback_data="new_category_charging")],
        [InlineKeyboardButton("🎧 هدفون و هندزفری", callback_data="new_category_audio")],
        [InlineKeyboardButton("🖥️ محافظ صفحه", callback_data="new_category_screen")],
        [InlineKeyboardButton("🔋 پاوربانک", callback_data="new_category_powerbank")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="manage_products")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if update.message:
        await update.message.reply_text("🔄 در حال بارگذاری...", reply_markup=ReplyKeyboardRemove())
    
    if user_id == ADMIN_CHAT_ID:
        if update.message:
            await update.message.reply_text("🏪 **پنل مدیریت فروشگاه لوازم جانبی موبایل**", reply_markup=admin_main_menu())
        else:
            await update.callback_query.edit_message_text("🏪 **پنل مدیریت فروشگاه لوازم جانبی موبایل**", reply_markup=admin_main_menu())
    else:
        user_name = update.effective_user.first_name or "مشتری"
        if update.message:
            await update.message.reply_text(
                f"👋 {user_name} عزیز، به فروشگاه تخصصی لوازم جانبی موبایل خوش آمدید!\n\n"
                "📱 بهترین لوازم جانبی با کیفیت عالی", 
                reply_markup=user_main_menu()
            )
        else:
            await update.callback_query.edit_message_text(
                f"👋 {user_name} عزیز، به فروشگاه تخصصی لوازم جانبی موبایل خوش آمدید!\n\n"
                "📱 بهترین لوازم جانبی با کیفیت عالی", 
                reply_markup=user_main_menu()
            )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "مشتری"
    text = update.message.text
    
    # حالت ثبت نظر
    if user_states.get(user_id) == 'waiting_for_review_comment':
        rating = context.user_data.get('rating')
        try:
            conn = get_db_connection()
            c = conn.cursor()
            # پیدا کردن آخرین سفارش کاربر
            c.execute("SELECT id FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
            last_order = c.fetchone()
            
            if last_order:
                order_id = last_order[0]
                c.execute('''INSERT INTO reviews (order_id, user_id, rating, comment, created_at)
                            VALUES (?, ?, ?, ?, ?)''',
                         (order_id, user_id, rating, text, datetime.now().isoformat()))
                conn.commit()
                await update.message.reply_text("✅ نظر شما با موفقیت ثبت شد! از مشارکت شما سپاسگزاریم.", reply_markup=user_main_menu())
            else:
                await update.message.reply_text("❌ شما هیچ سفارشی برای ثبت نظر ندارید.", reply_markup=user_main_menu())
            
            conn.close()
        except Exception as e:
            await update.message.reply_text("❌ خطا در ثبت نظر.", reply_markup=user_main_menu())
        
        user_states[user_id] = None
        return
    
    # حالت ثبت سفارش
    elif user_states.get(user_id) == 'waiting_for_phone':
        if text == "📝 وارد کردن دستی شماره":
            await update.message.reply_text("📱 لطفاً شماره تماس خود را وارد کنید:", reply_markup=ReplyKeyboardRemove())
            return
        
        context.user_data['phone'] = text
        await update.message.reply_text("🏠 لطفاً آدرس دقیق خود را برای ارسال مرسوله وارد کنید:", reply_markup=ReplyKeyboardRemove())
        user_states[user_id] = 'waiting_for_address'
        return
    
    elif user_states.get(user_id) == 'waiting_for_address':
        phone = context.user_data.get('phone', 'ثبت نشده')
        product = context.user_data.get('product', 'محصول نامشخص')
        quantity = context.user_data.get('quantity', 1)
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''INSERT INTO orders (user_id, user_name, phone, product, quantity, address, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (user_id, user_name, phone, product, quantity, text, 'new', datetime.now().isoformat()))
            order_id = c.lastrowid
            conn.commit()
            conn.close()
            
            await update.message.reply_text(
                f"✅ **سفارش شما ثبت شد!**\n\n"
                f"🆔 کد پیگیری: #{order_id}\n"
                f"📦 محصول: {product}\n"
                f"🔢 تعداد: {quantity}\n\n"
                f"📞 به زودی با شما تماس گرفته خواهد شد.", 
                reply_markup=user_main_menu()
            )
            
            admin_message = (
                f"🚨 **سفارش جدید!**\n"
                f"🆔 #{order_id}\n"
                f"👤 {user_name}\n"
                f"📞 {phone}\n"
                f"📦 {product}\n"
                f"🔢 {quantity}\n"
                f"🏠 {text}"
            )
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
            
        except Exception as e:
            await update.message.reply_text("❌ خطا در ثبت سفارش.", reply_markup=user_main_menu())
        
        user_states[user_id] = None
        return
    
    # حالت‌های مدیریت محصولات برای ادمین
    elif user_states.get(user_id) == 'waiting_for_product_name' and user_id == ADMIN_CHAT_ID:
        context.user_data['new_product_name'] = text
        user_states[user_id] = 'waiting_for_product_price'
        await update.message.reply_text("💰 لطفاً قیمت محصول را به تومان وارد کنید:")
        return
    
    elif user_states.get(user_id) == 'waiting_for_product_price' and user_id == ADMIN_CHAT_ID:
        try:
            price = int(text.replace(',', '').replace('تومان', '').strip())
            context.user_data['new_product_price'] = price
            user_states[user_id] = 'waiting_for_product_description'
            await update.message.reply_text("📝 لطفاً توضیحات محصول را وارد کنید:")
        except ValueError:
            await update.message.reply_text("❌ قیمت باید یک عدد باشد. لطفاً مجدداً وارد کنید:")
        return
    
    elif user_states.get(user_id) == 'waiting_for_product_description' and user_id == ADMIN_CHAT_ID:
        context.user_data['new_product_description'] = text
        user_states[user_id] = 'waiting_for_product_stock'
        await update.message.reply_text("📦 لطفاً تعداد موجودی محصول را وارد کنید:")
        return
    
    elif user_states.get(user_id) == 'waiting_for_product_stock' and user_id == ADMIN_CHAT_ID:
        try:
            stock = int(text)
            # ذخیره محصول در دیتابیس
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''INSERT INTO products (name, category, price, description, stock, created_at)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                     (context.user_data['new_product_name'],
                      context.user_data['new_product_category'],
                      context.user_data['new_product_price'],
                      context.user_data['new_product_description'],
                      stock,
                      datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
            await update.message.reply_text(
                f"✅ **محصول با موفقیت اضافه شد!**\n\n"
                f"📦 نام: {context.user_data['new_product_name']}\n"
                f"💰 قیمت: {context.user_data['new_product_price']:,} تومان\n"
                f"📝 توضیحات: {context.user_data['new_product_description']}\n"
                f"📦 موجودی: {stock}",
                reply_markup=admin_main_menu()
            )
            
            # پاک کردن داده‌های موقت
            for key in ['new_product_name', 'new_product_category', 'new_product_price', 'new_product_description']:
                if key in context.user_data:
                    del context.user_data[key]
            
        except ValueError:
            await update.message.reply_text("❌ تعداد موجودی باید عدد باشد. لطفاً مجدداً وارد کنید:")
            return
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در افزودن محصول: {str(e)}", reply_markup=admin_main_menu())
        
        user_states[user_id] = None
        return

    # حالت ویرایش محصولات - بخش جدید
    elif user_states.get(user_id) == 'waiting_for_edit_value' and user_id == ADMIN_CHAT_ID:
        product_id = context.user_data.get('editing_product_id')
        field = context.user_data.get('editing_field')
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            if field == 'price':
                value = int(text.replace(',', '').replace('تومان', '').strip())
            elif field == 'stock':
                value = int(text)
            else:
                value = text
            
            # به روزرسانی فیلد در دیتابیس
            c.execute(f"UPDATE products SET {field} = ? WHERE id = ?", (value, product_id))
            conn.commit()
            
            # دریافت اطلاعات به روز شده محصول
            c.execute("SELECT name, category, price, description, stock FROM products WHERE id = ?", (product_id,))
            updated_product = c.fetchone()
            conn.close()
            
            field_names = {
                'name': 'نام',
                'price': 'قیمت',
                'description': 'توضیحات', 
                'stock': 'موجودی'
            }
            
            if updated_product:
                name, category, price, description, stock = updated_product
                await update.message.reply_text(
                    f"✅ **ویرایش با موفقیت انجام شد**\n\n"
                    f"📦 محصول: {name}\n"
                    f"✏️ فیلد ویرایش شده: {field_names.get(field, field)}\n"
                    f"🆕 مقدار جدید: {value}\n\n"
                    f"برای ویرایش بیشتر محصول، از منوی مدیریت محصولات استفاده کنید.",
                    reply_markup=admin_main_menu()
                )
            else:
                await update.message.reply_text("❌ خطا در به روزرسانی محصول.", reply_markup=admin_main_menu())
            
        except ValueError:
            if field == 'price':
                await update.message.reply_text("❌ قیمت باید یک عدد باشد. لطفاً مجدداً وارد کنید:")
            elif field == 'stock':
                await update.message.reply_text("❌ موجودی باید عدد باشد. لطفاً مجدداً وارد کنید:")
            return
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در ویرایش محصول: {str(e)}", reply_markup=admin_main_menu())
        
        # پاک کردن حالت ویرایش
        user_states[user_id] = None
        if 'editing_product_id' in context.user_data:
            del context.user_data['editing_product_id']
        if 'editing_field' in context.user_data:
            del context.user_data['editing_field']
        return
    
    else:
        if user_id == ADMIN_CHAT_ID:
            await update.message.reply_text("💡 از منوی زیر استفاده کنید:", reply_markup=admin_main_menu())
        else:
            await update.message.reply_text("💡 از منوی زیر استفاده کنید:", reply_markup=user_main_menu())

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    contact = update.message.contact
    
    if user_states.get(user_id) == 'waiting_for_phone':
        context.user_data['phone'] = contact.phone_number
        await update.message.reply_text("✅ شماره تماس ثبت شد\n🏠 لطفاً آدرس دقیق خود را وارد کنید:", reply_markup=ReplyKeyboardRemove())
        user_states[user_id] = 'waiting_for_address'

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    # مدیریت برگشت
    if query.data == "back_main" and user_id == ADMIN_CHAT_ID:
        await query.edit_message_text("🏪 **پنل مدیریت فروشگاه**", reply_markup=admin_main_menu())
        return
    
    elif query.data == "back_user_main" or (query.data == "back_main" and user_id != ADMIN_CHAT_ID):
        await query.edit_message_text("👋 به فروشگاه لوازم جانبی موبایل خوش آمدید!", reply_markup=user_main_menu())
        return
    
    # منوی کاربران
    elif query.data == "shop_products":
        await query.edit_message_text("📱 **دسته‌بندی محصولات**\n\nلطفاً دسته مورد نظر را انتخاب کنید:", reply_markup=product_categories_menu())
        return
    
    elif query.data == "add_review":
        await query.edit_message_text("⭐ **ثبت نظر**\n\nلطفاً به خدمات ما امتیاز دهید:", reply_markup=rating_keyboard())
        return
    
    elif query.data.startswith('rate_'):
        rating = int(query.data.split('_')[1])
        context.user_data['rating'] = rating
        user_states[user_id] = 'waiting_for_review_comment'
        await query.edit_message_text(f"⭐ امتیاز {rating} ستاره ثبت شد.\n\nلطفاً نظر خود را بنویسید:")
        return
    
    # نمایش محصولات بر اساس دسته‌بندی
    elif query.data.startswith('category_'):
        category = query.data.replace('category_', '')
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT id, name, price, description, stock FROM products WHERE category = ?", (category,))
            products = c.fetchall()
            conn.close()
            
            if not products:
                await query.edit_message_text("❌ هیچ محصولی در این دسته‌بندی یافت نشد.", reply_markup=product_categories_menu())
                return
            
            category_names = {
                'case': '📱 قاب و کاور',
                'charging': '⚡ کابل و شارژر',
                'audio': '🎧 هدفون و هندزفری',
                'screen': '🖥️ محافظ صفحه',
                'powerbank': '🔋 پاوربانک'
            }
            
            message = f"📦 **محصولات {category_names.get(category, 'دسته‌بندی')}**\n\n"
            keyboard = []
            
            for product_id, name, price, description, stock in products:
                message += f"📱 {name}\n💵 {price:,} تومان\n📝 {description}\n📦 موجودی: {stock}\n{'─'*30}\n"
                keyboard.append([InlineKeyboardButton(f"🛒 خرید {name}", callback_data=f"buy_{product_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 برگشت به دسته‌ها", callback_data="shop_products")])
            
            await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
            
        except Exception as e:
            await query.edit_message_text("❌ خطا در دریافت محصولات.", reply_markup=product_categories_menu())
        return
    
    # خرید محصول
    elif query.data.startswith('buy_'):
        try:
            product_id = int(query.data.replace('buy_', ''))
            
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT name, price FROM products WHERE id = ?", (product_id,))
            product = c.fetchone()
            conn.close()
            
            if product:
                product_name, price = product
                context.user_data['product'] = product_name
                context.user_data['quantity'] = 1
                
                await query.message.reply_text("📱 برای تکمیل سفارش، لطفاً شماره تماس خود را ارائه دهید:", reply_markup=phone_keyboard())
                user_states[user_id] = 'waiting_for_phone'
            else:
                await query.edit_message_text("❌ محصول یافت نشد.", reply_markup=product_categories_menu())
                
        except Exception as e:
            await query.edit_message_text("❌ خطا در انتخاب محصول.", reply_markup=product_categories_menu())
        return
    
    elif query.data == "user_support":
        await query.edit_message_text(
            "📞 **پشتیبانی فروشگاه**\n\n"
            "🕒 ساعات پاسخگویی: ۹ صبح تا ۱۰ شب\n"
            "📞 تلفن: 09301111969\n"
            "📍 آدرس: تهران، خیابان ولیعصر",
            reply_markup=user_main_menu()
        )
        return
    
    elif query.data == "shopping_guide":
        content = """📚 **راهنمای خرید از فروشگاه**

🛒 **مراحل خرید:**
1. انتخاب دسته محصول
2. مشاهده محصولات و قیمت‌ها  
3. انتخاب محصول مورد نظر
4. ثبت شماره تماس و آدرس
5. تأیید نهایی سفارش

🚚 **ارسال و تحویل:**
• ارسال رایگان برای خریدهای بالای 300 هزار تومان
• ارسال در تهران: 1-2 روز کاری
• ارسال به شهرستان: 3-5 روز کاری

💳 **روش‌های پرداخت:**
• پرداخت در محل
• پرداخت آنلاین
• کارت به کارت"""
        await query.edit_message_text(content, reply_markup=user_main_menu())
        return
    
    elif query.data == "track_order":
        await query.edit_message_text(
            "📦 **پیگیری سفارش**\n\n"
            "برای پیگیری سفارش خود لطفاً با پشتیبانی تماس بگیرید:\n"
            "📞 09301111969\n\n"
            "یا کد پیگیری خود را برای ما ارسال کنید.",
            reply_markup=user_main_menu()
        )
        return
    
    # بخش مدیریت
    elif query.data == "stats" and user_id == ADMIN_CHAT_ID:
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM orders")
            total_orders = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM orders WHERE status = 'new'")
            new_orders = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'")
            completed_orders = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM products")
            total_products = c.fetchone()[0] or 0
            conn.close()
            
            await query.edit_message_text(
                f"📊 **آمار فروشگاه**\n\n"
                f"📦 کل سفارشات: {total_orders}\n"
                f"🆕 سفارشات جدید: {new_orders}\n"
                f"✅ سفارشات تکمیل شده: {completed_orders}\n"
                f"📋 تعداد محصولات: {total_products}",
                reply_markup=admin_main_menu()
            )
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در دریافت آمار: {str(e)}", reply_markup=admin_main_menu())
        return
    
    elif query.data == "new_orders" and user_id == ADMIN_CHAT_ID:
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT id, user_name, phone, product, quantity, address FROM orders WHERE status = 'new' ORDER BY created_at DESC LIMIT 10")
            new_orders = c.fetchall()
            conn.close()
            
            if not new_orders:
                await query.edit_message_text("📭 **هیچ سفارش جدیدی وجود ندارد**", reply_markup=admin_main_menu())
                return
            
            orders_text = "📋 **سفارش‌های جدید:**\n\n"
            keyboard = []
            
            for order in new_orders:
                order_id, user_name, phone, product, quantity, address = order
                orders_text += f"🆔 #{order_id}\n👤 {user_name}\n📞 {phone}\n📦 {product}\n🔢 {quantity}\n🏠 {address[:30]}...\n{'─'*30}\n"
                keyboard.append([InlineKeyboardButton(f"✅ تکمیل سفارش #{order_id}", callback_data=f"complete_{order_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_main")])
            
            await query.edit_message_text(orders_text, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در دریافت سفارش‌ها: {str(e)}", reply_markup=admin_main_menu())
        return

    elif query.data.startswith('complete_') and user_id == ADMIN_CHAT_ID:
        order_id = query.data.split('_')[1]
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("UPDATE orders SET status = 'completed' WHERE id = ?", (order_id,))
            conn.commit()
            conn.close()
            
            await query.edit_message_text(f"✅ سفارش #{order_id} با موفقیت تکمیل شد.", reply_markup=admin_main_menu())
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در تکمیل سفارش: {str(e)}", reply_markup=admin_main_menu())
        return

    elif query.data == "contact_customers" and user_id == ADMIN_CHAT_ID:
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT id, user_name, phone FROM orders WHERE status = 'new' ORDER BY created_at DESC LIMIT 10")
            new_orders = c.fetchall()
            conn.close()
            
            if not new_orders:
                await query.edit_message_text("✅ هیچ مشتری برای تماس وجود ندارد.", reply_markup=admin_main_menu())
                return
            
            keyboard = []
            for order_id, name, phone in new_orders:
                keyboard.append([InlineKeyboardButton(f"👤 {name} (#{order_id}) - {phone}", callback_data=f"view_order_{order_id}")])
            keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_main")])
            
            await query.edit_message_text("📞 **لیست مشتریان برای تماس:**\n\nیکی از مشتریان را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در دریافت لیست مشتریان: {str(e)}", reply_markup=admin_main_menu())
        return

    elif query.data.startswith('view_order_') and user_id == ADMIN_CHAT_ID:
        order_id = query.data.split('_')[2]
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT user_name, phone, product, quantity, address, status FROM orders WHERE id = ?", (order_id,))
            order_info = c.fetchone()
            conn.close()
            
            if order_info:
                name, phone, product, quantity, address, status = order_info
                status_text = "🆕 جدید" if status == 'new' else "✅ تکمیل شده"
                
                message = (
                    f"📋 **جزئیات سفارش**\n\n"
                    f"🆔 کد: #{order_id}\n"
                    f"👤 نام: {name}\n"
                    f"📞 شماره: {phone}\n"
                    f"📦 محصول: {product}\n"
                    f"🔢 تعداد: {quantity}\n"
                    f"🏠 آدرس: {address}\n"
                    f"📊 وضعیت: {status_text}"
                )
                
                keyboard = []
                if status == 'new':
                    keyboard.append([InlineKeyboardButton("✅ تکمیل سفارش", callback_data=f"complete_{order_id}")])
                keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="contact_customers")])
                
                await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در دریافت اطلاعات سفارش: {str(e)}", reply_markup=admin_main_menu())
        return

    elif query.data == "manage_products" and user_id == ADMIN_CHAT_ID:
        keyboard = [
            [InlineKeyboardButton("➕ افزودن محصول جدید", callback_data="add_product")],
            [InlineKeyboardButton("📋 لیست تمام محصولات", callback_data="list_products")],
            [InlineKeyboardButton("✏️ ویرایش محصولات", callback_data="edit_products")],
            [InlineKeyboardButton("🗑️ حذف محصول", callback_data="delete_product")],
            [InlineKeyboardButton("🔙 برگشت", callback_data="back_main")]
        ]
        await query.edit_message_text("📦 **مدیریت محصولات**\n\nلطفاً عملیات مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif query.data == "add_product" and user_id == ADMIN_CHAT_ID:
        await query.edit_message_text(
            "📦 **افزودن محصول جدید**\n\n"
            "لطفاً دسته‌بندی محصول را انتخاب کنید:",
            reply_markup=category_selection_keyboard()
        )
        return

    elif query.data.startswith('new_category_') and user_id == ADMIN_CHAT_ID:
        category = query.data.replace('new_category_', '')
        context.user_data['new_product_category'] = category
        user_states[user_id] = 'waiting_for_product_name'
        
        category_names = {
            'case': 'قاب و کاور',
            'charging': 'کابل و شارژر',
            'audio': 'هدفون و هندزفری',
            'screen': 'محافظ صفحه',
            'powerbank': 'پاوربانک'
        }
        
        await query.edit_message_text(
            f"📦 افزودن محصول به دسته‌بندی: {category_names.get(category, 'دسته‌بندی')}\n\n"
            "لطفاً نام محصول را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data="manage_products")]])
        )
        return

    elif query.data == "list_products" and user_id == ADMIN_CHAT_ID:
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT id, name, category, price, stock FROM products ORDER BY category, name")
            products = c.fetchall()
            conn.close()
            
            if not products:
                await query.edit_message_text("📭 هیچ محصولی ثبت نشده است.", reply_markup=admin_main_menu())
                return
            
            message = "📋 **لیست تمام محصولات:**\n\n"
            current_category = ""
            
            for product_id, name, category, price, stock in products:
                category_names = {
                    'case': '📱 قاب و کاور',
                    'charging': '⚡ کابل و شارژر',
                    'audio': '🎧 هدفون و هندزفری',
                    'screen': '🖥️ محافظ صفحه',
                    'powerbank': '🔋 پاوربانک'
                }
                
                if category != current_category:
                    current_category = category
                    message += f"\n{category_names.get(category, 'دسته‌بندی')}:\n"
                
                message += f"🆔 #{product_id} - {name}\n💵 {price:,} تومان - 📦 {stock} عدد\n{'─'*20}\n"
            
            keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="manage_products")]]
            await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در دریافت لیست محصولات: {str(e)}", reply_markup=admin_main_menu())
        return

    elif query.data == "edit_products" and user_id == ADMIN_CHAT_ID:
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT id, name, price, stock FROM products ORDER BY name")
            products = c.fetchall()
            conn.close()
            
            if not products:
                await query.edit_message_text("📭 هیچ محصولی برای ویرایش وجود ندارد.", reply_markup=admin_main_menu())
                return
            
            keyboard = []
            for product_id, name, price, stock in products:
                keyboard.append([InlineKeyboardButton(f"✏️ {name} - {price:,} تومان", callback_data=f"edit_{product_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="manage_products")])
            
            await query.edit_message_text("✏️ **ویرایش محصولات**\n\nلطفاً محصول مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در دریافت لیست محصولات: {str(e)}", reply_markup=admin_main_menu())
        return

    elif query.data == "delete_product" and user_id == ADMIN_CHAT_ID:
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT id, name FROM products ORDER BY name")
            products = c.fetchall()
            conn.close()
            
            if not products:
                await query.edit_message_text("📭 هیچ محصولی برای حذف وجود ندارد.", reply_markup=admin_main_menu())
                return
            
            keyboard = []
            for product_id, name in products:
                keyboard.append([InlineKeyboardButton(f"🗑️ {name}", callback_data=f"delete_{product_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="manage_products")])
            
            await query.edit_message_text("🗑️ **حذف محصولات**\n\nلطفاً محصول مورد نظر برای حذف را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در دریافت لیست محصولات: {str(e)}", reply_markup=admin_main_menu())
        return

    # سیستم ویرایش محصولات - بخش جدید و کامل
    elif query.data.startswith('edit_') and user_id == ADMIN_CHAT_ID:
        product_id = query.data.replace('edit_', '')
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT id, name, category, price, description, stock FROM products WHERE id = ?", (product_id,))
            product = c.fetchone()
            conn.close()
            
            if product:
                product_id, name, category, price, description, stock = product
                context.user_data['editing_product_id'] = product_id
                
                category_names = {
                    'case': '📱 قاب و کاور',
                    'charging': '⚡ کابل و شارژر',
                    'audio': '🎧 هدفون و هندزفری',
                    'screen': '🖥️ محافظ صفحه',
                    'powerbank': '🔋 پاوربانک'
                }
                
                message = (
                    f"✏️ **ویرایش محصول**\n\n"
                    f"🆔 کد: #{product_id}\n"
                    f"📦 نام: {name}\n"
                    f"📁 دسته: {category_names.get(category, category)}\n"
                    f"💰 قیمت: {price:,} تومان\n"
                    f"📝 توضیحات: {description}\n"
                    f"📦 موجودی: {stock}\n\n"
                    f"لطفاً فیلدی که می‌خواهید ویرایش کنید را انتخاب کنید:"
                )
                
                keyboard = [
                    [InlineKeyboardButton("📦 ویرایش نام", callback_data=f"edit_name_{product_id}")],
                    [InlineKeyboardButton("💰 ویرایش قیمت", callback_data=f"edit_price_{product_id}")],
                    [InlineKeyboardButton("📝 ویرایش توضیحات", callback_data=f"edit_desc_{product_id}")],
                    [InlineKeyboardButton("📦 ویرایش موجودی", callback_data=f"edit_stock_{product_id}")],
                    [InlineKeyboardButton("📁 تغییر دسته‌بندی", callback_data=f"edit_category_{product_id}")],
                    [InlineKeyboardButton("🔙 برگشت به مدیریت محصولات", callback_data="manage_products")]
                ]
                
                await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await query.edit_message_text("❌ محصول یافت نشد.", reply_markup=admin_main_menu())
                
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در دریافت اطلاعات محصول: {str(e)}", reply_markup=admin_main_menu())
        return

    elif query.data.startswith('edit_name_') and user_id == ADMIN_CHAT_ID:
        product_id = query.data.replace('edit_name_', '')
        context.user_data['editing_product_id'] = product_id
        context.user_data['editing_field'] = 'name'
        user_states[user_id] = 'waiting_for_edit_value'
        
        await query.edit_message_text(
            "✏️ **ویرایش نام محصول**\n\n"
            "لطفاً نام جدید محصول را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data=f"edit_{product_id}")]])
        )
        return

    elif query.data.startswith('edit_price_') and user_id == ADMIN_CHAT_ID:
        product_id = query.data.replace('edit_price_', '')
        context.user_data['editing_product_id'] = product_id
        context.user_data['editing_field'] = 'price'
        user_states[user_id] = 'waiting_for_edit_value'
        
        await query.edit_message_text(
            "💰 **ویرایش قیمت محصول**\n\n"
            "لطفاً قیمت جدید را به تومان وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data=f"edit_{product_id}")]])
        )
        return

    elif query.data.startswith('edit_desc_') and user_id == ADMIN_CHAT_ID:
        product_id = query.data.replace('edit_desc_', '')
        context.user_data['editing_product_id'] = product_id
        context.user_data['editing_field'] = 'description'
        user_states[user_id] = 'waiting_for_edit_value'
        
        await query.edit_message_text(
            "📝 **ویرایش توضیحات محصول**\n\n"
            "لطفاً توضیحات جدید را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data=f"edit_{product_id}")]])
        )
        return

    elif query.data.startswith('edit_stock_') and user_id == ADMIN_CHAT_ID:
        product_id = query.data.replace('edit_stock_', '')
        context.user_data['editing_product_id'] = product_id
        context.user_data['editing_field'] = 'stock'
        user_states[user_id] = 'waiting_for_edit_value'
        
        await query.edit_message_text(
            "📦 **ویرایش موجودی محصول**\n\n"
            "لطفاً تعداد موجودی جدید را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data=f"edit_{product_id}")]])
        )
        return

    elif query.data.startswith('edit_category_') and user_id == ADMIN_CHAT_ID:
        product_id = query.data.replace('edit_category_', '')
        context.user_data['editing_product_id'] = product_id
        context.user_data['editing_field'] = 'category'
        
        keyboard = [
            [InlineKeyboardButton("📱 قاب و کاور", callback_data=f"set_category_case_{product_id}")],
            [InlineKeyboardButton("⚡ کابل و شارژر", callback_data=f"set_category_charging_{product_id}")],
            [InlineKeyboardButton("🎧 هدفون و هندزفری", callback_data=f"set_category_audio_{product_id}")],
            [InlineKeyboardButton("🖥️ محافظ صفحه", callback_data=f"set_category_screen_{product_id}")],
            [InlineKeyboardButton("🔋 پاوربانک", callback_data=f"set_category_powerbank_{product_id}")],
            [InlineKeyboardButton("🔙 برگشت", callback_data=f"edit_{product_id}")]
        ]
        
        await query.edit_message_text(
            "📁 **تغییر دسته‌بندی محصول**\n\n"
            "لطفاً دسته‌بندی جدید را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    elif query.data.startswith('set_category_') and user_id == ADMIN_CHAT_ID:
        parts = query.data.split('_')
        category = parts[2]
        product_id = parts[3]
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("UPDATE products SET category = ? WHERE id = ?", (category, product_id))
            conn.commit()
            conn.close()
            
            category_names = {
                'case': '📱 قاب و کاور',
                'charging': '⚡ کابل و شارژر',
                'audio': '🎧 هدفون و هندزفری',
                'screen': '🖥️ محافظ صفحه',
                'powerbank': '🔋 پاوربانک'
            }
            
            await query.edit_message_text(
                f"✅ **دسته‌بندی محصول با موفقیت تغییر کرد**\n\n"
                f"دسته‌بندی جدید: {category_names.get(category, category)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به ویرایش", callback_data=f"edit_{product_id}")]])
            )
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در تغییر دسته‌بندی: {str(e)}", reply_markup=admin_main_menu())
        return

    elif query.data.startswith('delete_') and user_id == ADMIN_CHAT_ID:
        product_id = query.data.replace('delete_', '')
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            conn.close()
            
            await query.edit_message_text(f"✅ محصول #{product_id} با موفقیت حذف شد.", reply_markup=admin_main_menu())
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در حذف محصول: {str(e)}", reply_markup=admin_main_menu())
        return

    elif query.data == "view_reviews" and user_id == ADMIN_CHAT_ID:
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''SELECT r.rating, r.comment, u.user_name, r.created_at 
                         FROM reviews r 
                         JOIN orders u ON r.order_id = u.id 
                         ORDER BY r.created_at DESC LIMIT 10''')
            reviews = c.fetchall()
            conn.close()
            
            if not reviews:
                await query.edit_message_text("📭 هنوز نظری ثبت نشده است.", reply_markup=admin_main_menu())
                return
            
            message = "⭐ **آخرین نظرات مشتریان:**\n\n"
            for rating, comment, name, created_at in reviews:
                stars = "⭐" * rating
                date = datetime.fromisoformat(created_at).strftime("%Y/%m/%d")
                message += f"{stars}\n👤 {name}\n📝 {comment}\n📅 {date}\n{'─'*30}\n"
            
            keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="back_main")]]
            await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در دریافت نظرات: {str(e)}", reply_markup=admin_main_menu())
        return

    elif query.data == "reset_system" and user_id == ADMIN_CHAT_ID:
        keyboard = [
            [InlineKeyboardButton("✅ بله، ریست کن", callback_data="confirm_reset")],
            [InlineKeyboardButton("❌ انصراف", callback_data="back_main")]
        ]
        await query.edit_message_text(
            "⚠️ **هشدار: ریست کامل سیستم**\n\n"
            "این عمل تمام داده‌ها را پاک می‌کند:\n"
            "• همه سفارشات\n• همه نظرات\n• آمار سیستم\n\n"
            "آیا مطمئن هستید؟", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    elif query.data == "confirm_reset" and user_id == ADMIN_CHAT_ID:
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("DELETE FROM orders")
            c.execute("DELETE FROM reviews")
            conn.commit()
            conn.close()
            
            user_states.clear()
            
            await query.edit_message_text(
                "✅ **سیستم با موفقیت ریست شد**\n\n"
                "• تمام سفارشات پاک شد\n• تمام نظرات حذف شد\n• آمار سیستم صفر شد", 
                reply_markup=admin_main_menu()
            )
            
        except Exception as e:
            await query.edit_message_text(f"❌ **خطا در ریست سیستم**\n\nخطا: {str(e)}", reply_markup=admin_main_menu())
        return

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("🟢 ربات فروشگاه لوازم جانبی موبایل اجرا شد!")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
