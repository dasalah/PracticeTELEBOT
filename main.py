from telethon import TelegramClient, events,Button
from config import api_id, api_hash, token
from func import *


users_status={"FirstName":" ",
              "LastName":" ",
              "step":0,
              "StudentCode":0,
              "PhoneNumber":0}

#bot client
client = TelegramClient(session="salah",
                        api_id=api_id,
                        api_hash=api_hash,
                        proxy=("HTTP","127.0.0.1",8086))

#special words for not declare for it
special_words=["لغو","ثبت نام","درباره ما","/start","تایید میکنم"]


#SignUp
@client.on(events.NewMessage(func= lambda e: e.is_private))
async def action(event):
    # if word in special words
    if event.text in special_words:
        return

    #for signUp#
    if event.chat_id in users_status and users_status[event.chat_id]["step"] != 0:
        await save_information(event,client,users_status)
    #for signUp#


# if text in special words
@client.on(events.NewMessage(func= lambda e : e.text in special_words))
async def action(event):
    await handle_SpecialWords(event,client,users_status)

if __name__ == '__main__':
    client.start(bot_token=token)
    if client.is_connected():
        print('bot Connected')
    client.run_until_disconnected()





