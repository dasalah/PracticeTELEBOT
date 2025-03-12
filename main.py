from telethon import TelegramClient, events,Button
from config import api_id, api_hash, token


users_status={"FirstName":" ",
              "LastName":" ",
              "step":0,
              "StudentCode":0,
              "PhoneNumber":0}

step_sign=1
step_name=2
step_last=3
step_code=4
step_phone=5
step_complate=6


client = TelegramClient(session="salah",
                        api_id=api_id,
                        api_hash=api_hash)

special_words=["لفو","ثبت نام","درباره ما","/start"]
@client.on(events.NewMessage(pattern="/start",func= lambda e: e.is_private))
async def start(event):

    buttons = [
        [Button.text(text="ثبت نام", resize=True)],
        [Button.text(text="درباره ما")]
    ]

    await client.send_message(entity=event.chat_id,message="سلام به ربات انجمن مهندسی کامپیوتر خوش آمدید",reply_to=event.message,buttons=buttons)




@client.on(events.NewMessage(func=lambda e: e.text == "ثبت نام"))
async def logging(event):

            users_status[event.chat_id] = { "step" : step_sign }
            await event.respond("لطفا نام خود را وارد کنید",buttons=Button.text(text="لغو", resize=True))


@client.on(events.NewMessage(func=lambda e : e.text=="لغو"))
async def cancel(event):
    await client.send_message(entity=event.chat_id,message="عملیات با موفقیت لفو شد.",buttons=[])##bug

@client.on(events.NewMessage(func= lambda e: e.is_private))
async def login(event):

    if event.text in special_words:
        return

    if   users_status[event.chat_id]["step"] == step_sign:
          users_status[event.chat_id]["FirstName"] = event.text
          users_status[event.chat_id]["step"] = step_name
          await event.respond("لطفا نام خانوادگی خود را وارد نمایید.")

    elif users_status[event.chat_id]["step"] == step_name:
          users_status[event.chat_id]["LastName"] = event.text
          users_status[event.chat_id]["step"] = step_last
          await event.respond("لطفا شماره دانشجویی خود را وارد کنید.")

    elif users_status[event.chat_id]["step"] == step_last:
          users_status[event.chat_id]["StudentCode"] = event.text
          users_status[event.chat_id]["step"] = step_code
          await event.respond("لطفا شماره تلفن خود را وارد کنید.")


    elif users_status[event.chat_id]["step"] == step_code:
          users_status[event.chat_id] = {"PhoneNumber":event.text}
          users_status[event.chat_id]["step"] = step_complate
          await event.respond("ثبت نام با موفقیت انجام شد")
          await event.respond(f"{users_status[event.chat_id].get('PhoneNumber')}")


    else:
        print("error")
        await event.respond("error")



client.start(bot_token=token)
if client.is_connected():
    print('Connected')
client.run_until_disconnected()