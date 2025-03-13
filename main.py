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

    users_status[event.chat_id]=   { "step" : step_sign,
                                    "FirstName" : "",
                                    "LastName" : "",
                                    "StudentCode" : "",
                                    "PhoneNumber" : ""
                                   }

    await event.respond("لطفا نام خود را وارد کنید",buttons=Button.text(text="لغو", resize=True))


@client.on(events.NewMessage(func=lambda e : e.text=="لغو"))
async def cancel(event):

    if users_status[event.chat_id]["step"] != 6 : #if while SignUp
        await client.send_message(entity=event.chat_id, message="عملیات با موفقیت لفو شد.", buttons=Button.clear())
        users_status[event.chat_id]["step"] = 0

@client.on(events.NewMessage(func= lambda e: e.is_private))#SignUp
async def login(event):

    if event.text in special_words:
        return

    if event.chat_id in users_status:

        if  users_status[event.chat_id]["step"] == step_sign:
              users_status[event.chat_id]["FirstName"] = event.text
              users_status[event.chat_id]["step"] = step_name
              await event.respond("لطفا نام خانوادگی خود را وارد نمایید.")

        elif users_status[event.chat_id]["step"] == step_name:
              users_status[event.chat_id]["LastName"] = event.text
              users_status[event.chat_id]["step"] = step_last
              await event.respond("لطفا شماره دانشجویی خود را وارد کنید.")

        elif users_status[event.chat_id]["step"] == step_last:

            if event.text.isdigit():
                users_status[event.chat_id]["StudentCode"] = event.text
                users_status[event.chat_id]["step"] = step_code
                await event.respond("لطفا شماره تلفن خود را وارد کنید.")

            else :
                await event.respond("لطفا شماره دانشجویی را درست وارد کنید")


        elif users_status[event.chat_id]["step"] == step_code:

            if event.text.isdigit() and len(event.text) == 11:
                  users_status[event.chat_id]["PhoneNumber"] = event.text
                  users_status[event.chat_id]["step"] = step_complate
                  await event.respond("ثبت نام با موفقیت انجام شد")
                  person_information = f"نام : { users_status[event.chat_id].get("FirstName") } \n نام خانوادگی  : {users_status[event.chat_id].get("LastName")} \n شماره دانشجویی :  {users_status[event.chat_id].get("StudentCode")} \n شماره تلفن : {users_status[event.chat_id].get("PhoneNumber")} "
                  await event.respond(f"{person_information}")
            else :
                await event.respond("لطفا شماره تلفن را درست وارد کنید"
                                    "نمونه درست: 09151234567")


if __name__ == '__main__':
    client.start(bot_token=token)
    if client.is_connected():
        print('Connected')
    client.run_until_disconnected()

