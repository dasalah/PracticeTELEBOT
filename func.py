from telethon.tl.custom.message import Message
from main import *
import openpyxl
import datetime
from telethon.tl.types import PeerChannel
from userDB import Base, User, Event, Settings, db_init
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


admin = 6033723482

##signup database in excel
excelDatabace = openpyxl.load_workbook("database.xlsx")
excelCursor = excelDatabace.active

#sql database
engine = create_engine('sqlite:///bot.db')
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
db_init()
#sql database


users_status={"FirstName":" ",
              "LastName":" ",
              "step":0,
              "StudentCode":0,
              "PhoneNumber":0}

step_sign,step_name,step_last,step_code,step_phone,step_complate=1,2,3,4,5,6

first_buttons = [
        [Button.text(text="ثبت نام", resize=True)],
        [Button.text(text="درباره ما", resize=True)],
        [Button.text(text="پیشنهاد",resize=True)]
    ]

###start function
async def start(event , client):

    await client.send_message(entity=event.chat_id,message="🤖 سلام به ربات انجمن هوش مصنوعی دانشگاه سیستان و بلوچستان خوش آمدید",
                              reply_to=event.message,
                              buttons=first_buttons)
###start function


### information bot function
async def information_bot(event):
    await event.reply("🧠 این ربات مخصوص انجمن هوش مصنوعی دانشگاه سیستان و بلوچستان میباشد."
                "\n"
                "💡 ارتباط با ما @pichpichboy",buttons=first_buttons)
### information bot function

### cancel progres
async def cancel(event , client, users_status):
    if users_status[event.chat_id]["step"] != 6 : #if while SignUp
        await client.send_message(entity=event.chat_id,
                                  message="عملیات با موفقیت لفو شد.",
                                  buttons=Button.clear())
        users_status[event.chat_id]["step"] = 0


## def save information for save information
async def save_information(event,client,users_status):

    if users_status[event.chat_id]["step"] == step_sign:
        users_status[event.chat_id]["FirstName"] = event.text
        users_status[event.chat_id]["step"] = step_name

    if users_status[event.chat_id]["step"] == step_name:
        users_status[event.chat_id]["FirstName"] = event.text
        users_status[event.chat_id]["step"] = step_last
        await event.respond("لطفا نام خانوادگی خود را وارد نمایید.")

    elif users_status[event.chat_id]["step"] == step_last:
        users_status[event.chat_id]["LastName"] = event.text
        users_status[event.chat_id]["step"] = step_code
        await event.respond("لطفا شماره دانشجویی خود را وارد کنید.")

    elif users_status[event.chat_id]["step"] == step_code:
        if event.text.isdigit():
            users_status[event.chat_id]["StudentCode"] = event.text
            users_status[event.chat_id]["step"] = step_phone
            await event.respond("لطفا شماره تلفن خود را وارد کنید.")
        else:
            await event.respond("لطفا شماره دانشجویی را درست وارد کنید", reply_to=event.message)

    elif users_status[event.chat_id]["step"] == step_phone:

        if event.text.isdigit() and len(event.text) == 11:

            users_status[event.chat_id]["PhoneNumber"] = event.text
            users_status[event.chat_id]["step"] = step_complate

            confirm_information_button = [
                Button.text("تایید میکنم", resize=True),
                Button.text("ویرایش اطلاعات")
            ]

            person_information = f"نام : {users_status[event.chat_id].get("FirstName")} \n نام خانوادگی  : {users_status[event.chat_id].get("LastName")} \n شماره دانشجویی :  {users_status[event.chat_id].get("StudentCode")} \n شماره تلفن : {users_status[event.chat_id].get("PhoneNumber")} "
            await client.send_message(entity=event.chat_id,
                                      message=f" آیا صحت اطلاعات را تایید می نمایید؟ \n {person_information}",
                                      buttons=confirm_information_button)

        else:
            await event.respond("لطفا شماره تلفن را درست وارد کنید"
                                "نمونه درست: 09151234567")

    if event.text == "ویرایش اطلاعات":
        # declare SignUp for edit information
        await signUp(event,users_status)

async def handle_SpecialWords(event,client,users_status):
    if event.text == "/start":
        await start(event , client)
    elif event.text == "درباره ما":
        await information_bot(event)
    elif event.text == "لغو" :
        await cancel(event ,client ,users_status)
    elif event.text == "ثبت نام" :
        await signUp(event, users_status)
    elif event.text == "پیشنهاد" :
        await call_to_us(event,users_status)
    elif event.text == "تایید میکنم" :
        if event.chat_id in users_status and users_status[event.chat_id]["step"] == step_complate:
            await confirm_information(event,users_status)



async def confirm_information(event,users_status):
    if users_status[event.chat_id]["step"] == step_complate:
        await event.respond("اطلاعات شما با موفقیت ذخیره شد.",buttons=Button.clear())
        data = [
                users_status[event.chat_id].get("FirstName"),
                users_status[event.chat_id].get("LastName"),
                users_status[event.chat_id].get("StudentCode"),
                users_status[event.chat_id].get("PhoneNumber")
        ]
        print(data)
        excelCursor.append(data)
        excelDatabace.save("database.xlsx")

        #create user object
        new_user = User(
            telegram_id=event.chat_id,
            first_name=users_status[event.chat_id].get("FirstName"),
            last_name=users_status[event.chat_id].get("LastName"),
            student_code=users_status[event.chat_id].get("StudentCode"),
            phone_number=users_status[event.chat_id].get("PhoneNumber")
        )
        #create user object

        #save user data in database
        session = Session()
        session.add(new_user)
        session.commit()
        session.close()
        #save user data in database

    else:
        await event.respond("لطفا ثبت نام خود را کامل به پایان برسانید.")

## function for signup
async def signUp(event,users_status):
    users_status[event.chat_id] = {"step": step_sign,
                                   "FirstName": "",
                                   "LastName": "",
                                   "StudentCode": "",
                                   "PhoneNumber": ""
                                   }
    ## declare insertName here,because some problem
    await event.respond("لطفا نام خود را وارد کنید", buttons=Button.text(text="لغو", resize=True))


async def call_to_us(event : Message,users_status):
    intro_message = "با سلام,لطفا اگه پیشنهاد یا انتقادی نسبت به ما دارین یا حرفیو میخواین باهامون در ارتباط بزارین اینجا بنویسین."
    await event.respond(message=intro_message,buttons=Button.clear(),reply_to=event.message)


    users_status[event.chat_id] = {"step": "message",
                                   "FirstName": "",
                                   "LastName": "",
                                   "StudentCode": "",
                                   "PhoneNumber": ""
                                   }


async def save_comment_to_excel(event : Message,users_status,client):
        save_comment = openpyxl.load_workbook("comment.xlsx")
        saver_comment = save_comment.active
        await client.forward_messages(entity=admin,messages=event.message)
        data = [
            event.chat_id,
            event.text
        ]
        saver_comment.append(data)
        save_comment.save("comment.xlsx")
        users_status[event.chat_id]["step"] = 0
        await event.respond("بازخورد شما با موفقیت ثبت شد.",buttons=first_buttons)

# Force Join System Functions
def get_setting(key: str, default_value: str = None):
    """Get a setting value from database"""
    try:
        session = Session()
        setting = session.query(Settings).filter(Settings.key == key).first()
        session.close()
        return setting.value if setting else default_value
    except:
        return default_value

def set_setting(key: str, value: str):
    """Set a setting value in database"""
    try:
        session = Session()
        setting = session.query(Settings).filter(Settings.key == key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.datetime.utcnow()
        else:
            setting = Settings(key=key, value=value)
            session.add(setting)
        session.commit()
        session.close()
        return True
    except Exception as e:
        print(f"Error setting {key}: {e}")
        return False

def is_force_join_enabled():
    """Check if force join is enabled"""
    return get_setting('force_join_enabled', 'true').lower() == 'true'

def get_force_join_channel():
    """Get the force join channel username"""
    return get_setting('force_join_channel', None)

def is_super_admin(user_id: int):
    """Check if user is super admin"""
    super_admins = get_setting('super_admins', str(admin)).split(',')
    return str(user_id) in [admin_id.strip() for admin_id in super_admins]

async def is_user_member(client, user_id: int, channel_username: str):
    """Check if user is member of the specified channel"""
    try:
        if not channel_username:
            return True
            
        # Remove @ if present
        if channel_username.startswith('@'):
            channel_username = channel_username[1:]
        
        try:
            # Try to get channel entity
            channel = await client.get_entity(channel_username)
            
            # Get user's membership status
            try:
                participant = await client.get_participants(channel, filter=lambda p: p.id == user_id, limit=1)
                return len(participant) > 0
            except:
                # Alternative method using get_entity
                try:
                    user_in_chat = await client.get_entity(PeerChannel(channel.id))
                    participants = await client.get_participants(user_in_chat)
                    return any(user.id == user_id for user in participants)
                except:
                    return False
                
        except Exception as e:
            print(f"Error checking membership for channel {channel_username}: {e}")
            return False
            
    except Exception as e:
        print(f"Error in is_user_member: {e}")
        return True  # Allow access if we can't check

async def check_force_join(event, client):
    """Middleware function to check force join requirement before any handler"""
    user_id = event.chat_id
    
    # Skip check for super admins
    if is_super_admin(user_id):
        return True
    
    # Skip if force join is disabled
    if not is_force_join_enabled():
        return True
        
    channel_username = get_force_join_channel()
    if not channel_username:
        return True
        
    # Check if user is member
    if not await is_user_member(client, user_id, channel_username):
        await send_join_required_message(event, channel_username)
        return False
        
    return True

async def send_join_required_message(event, channel_username: str):
    """Send the force join required message with improved UI"""
    
    # Add @ if not present
    if not channel_username.startswith('@'):
        channel_username = f'@{channel_username}'
    
    join_message = f"""🔒 برای استفاده از ربات، ابتدا عضو چنل زیر شوید:

🤖 انجمن هوش مصنوعی دانشگاه سیستان و بلوچستان
{channel_username}

💡 پس از عضویت، دکمه "بررسی مجدد عضویت" را بزنید."""

    # Create inline buttons
    buttons = [
        [Button.url("🧠 عضویت در چنل", url=f"https://t.me/{channel_username[1:]}")],
        [Button.inline("✅ بررسی مجدد عضویت", data="check_membership")]
    ]
    
    await event.respond(join_message, buttons=buttons)

async def is_join(event,client,idchannel):
    ## if user joined in the  chaneel
    try:
        if not idchannel:
            return True
        joined = await client.get_entity(PeerChannel(idchannel))
        participants_channel = await client.get_participants(entity=joined)
        for user in participants_channel:
            if user.id == event.chat_id:
                return True
        return False
    except:
        return True  # Allow access if we can't check

async def join_Request(event):
    """Legacy function - keeping for backward compatibility"""
    join_Message = "🔒 برای استفاده از ربات، ابتدا عضو چنل زیر شوید:\n\n🤖 انجمن هوش مصنوعی دانشگاه سیستان و بلوچستان\n\nپس از عضویت، کلمه /start را ارسال نمایید."
    await event.respond(join_Message,
                        buttons=[Button.url("🧠 انجمن هوش مصنوعی", url="t.me/ceusb")])

# Admin Commands for Force Join Management
async def handle_admin_commands(event, client):
    """Handle admin commands for force join management"""
    user_id = event.chat_id
    
    if not is_super_admin(user_id):
        await event.respond("⛔ شما دسترسی به این دستور را ندارید.")
        return
    
    text = event.text.strip()
    
    if text.startswith('/set_force_channel '):
        # Set force join channel
        channel = text.split(' ', 1)[1].strip()
        if set_setting('force_join_channel', channel):
            await event.respond(f"✅ چنل اجباری به {channel} تنظیم شد.")
        else:
            await event.respond("❌ خطا در تنظیم چنل.")
    
    elif text == '/toggle_force_join':
        # Toggle force join on/off
        current = is_force_join_enabled()
        new_value = 'false' if current else 'true'
        if set_setting('force_join_enabled', new_value):
            status = "فعال" if new_value == 'true' else "غیرفعال"
            await event.respond(f"🔄 جوین اجباری {status} شد.")
        else:
            await event.respond("❌ خطا در تغییر وضعیت.")
    
    elif text == '/force_join_stats':
        # Show force join statistics
        enabled = "فعال" if is_force_join_enabled() else "غیرفعال"
        channel = get_force_join_channel() or "تنظیم نشده"
        
        stats_message = f"""📊 وضعیت جوین اجباری:

🔧 وضعیت: {enabled}
📢 چنل: {channel}
👑 ادمین: @{event.sender.username if event.sender.username else 'بدون نام کاربری'}

⚙️ دستورات مدیریت:
/set_force_channel @channel - تنظیم چنل
/toggle_force_join - فعال/غیرفعال
/force_join_stats - نمایش وضعیت"""
        
        await event.respond(stats_message)


