from telethon.tl.custom.message import Message
from main import *
import openpyxl
from telethon.tl.types import PeerChannel
from userDB import Base, User, Event, db_init
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

    await client.send_message(entity=event.chat_id,message="سلام به ربات انجمن مهندسی کامپیوتر خوش آمدید",
                              reply_to=event.message,
                              buttons=first_buttons)
###start function


### information bot function
async def information_bot(event):
    await event.reply("این ربات دموی انجمن مهندسی کامپیوتر دانشگاه سیستان و بلوچستان میباشد."
                "\n"
                "ارتباط با ما @pichpichboy",buttons=first_buttons)
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

async def is_join(event,client,idchannel):
    ## if user joined in the  chaneel
    joined = await client.get_entity(PeerChannel(idchannel))
    participants_channel = await client.get_participants(entity=joined)
    for user in participants_channel:
        if user.id == event.chat_id:
            return True
    return False

async def join_Request(event):
    join_Message = "لطفا در چنل مهندسی کامپیوتر دانشگاه سیستان و بلوچستان عضو شوید سپس کلمه /start را ارسال نمایید."
    await event.respond(join_Message,
                        buttons=[Button.url("انجمن مهندسی کامپیوتر", url="t.me/ceusb")])


