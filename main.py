from telethon import TelegramClient, events,Button
from config import api_id, api_hash, token


users_status={}

client = TelegramClient(session="salah",
                        api_id=api_id,
                        api_hash=api_hash)


@client.on(events.NewMessage(pattern="/start",func= lambda e: e.is_private))
async def start(event):

    buttons = [
        [Button.text(text="ثبت نام", resize=True)],
        [Button.text(text="درباره ما")]
    ]

    await client.send_message(entity=event.chat_id,message="سلام به ربات انجمن مهندسی کامپیوتر خوش آمدید",reply_to=event.message,buttons=buttons)

@client.on(events.NewMessage(func=lambda e: e.text == "ثبت نام"))
def logging(event):

    if users_status[event.chat_id] == None:
        users_status[event.chat_id] = { "step" : "SignUp" }
        event.respond("لطفا نام خود را وارد کنید",buttons=Button.text(text="لغو", resize=True))

@client.on(events.NewMessage(func=lambda e : e.text=="لغو"))
def cancel(event):
    event.respond("عملبات با موفقیت لفو شد.")
    Button.clear()

@client.on(events.NewMessage(func= lambda e: e.is_private))
def login(event):

    if   users_status[event.chat_id]["step"] == "SignUp":
          users_status[event.chat_id]["first name"] = event.text

    elif users_status[event.chat_id]["step"] == "First Name":
          users_status[event.chat_id]["last name"] = event.text

    elif users_status[event.chat_id]["step"] == "StudentCode":
          users_status[event.chat_id]["student code"] = event.text

    elif users_status[event.chat_id]["step"] == "PhoneNumber":
          users_status[event.chat_id]["phone number"] = event.text

    else:
        print("error")
        event.respond("error")



client.start(bot_token=token)
if client.is_connected():
    print('Connected')
client.run_until_disconnected()