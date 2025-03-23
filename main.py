from telethon import TelegramClient, events,Button
from config import api_id, api_hash, token
from func import *
from telethon.tl.custom.message import Message


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
special_words=["لغو","ثبت نام","درباره ما","تایید میکنم","پیشنهاد"]

@client.on(events.NewMessage(pattern=r'^/start',func= lambda e: e.is_private))
async def star(event : Message):
    if len(event.text.split(" ")) == 2 :
        splited_text=event.text.split(" ")
        print(splited_text[1])
        if splited_text[1] == "salah":
            await client.forward_messages(
                                          entity=event.chat_id,
                                          from_peer="t.me/usb_karafarini",
                                          messages=654,
                                          drop_author=True,
                                          drop_media_captions=False,
            )

    else:
        await start(event,client)


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

    if event.chat_id in users_status and users_status[event.chat_id]["step"] == "message":
        await save_comment_to_excel(event,users_status)


# if text in special words
@client.on(events.NewMessage(func = lambda e : e.text in special_words))
async def action(event):
    await handle_SpecialWords(event,client,users_status)


if __name__ == '__main__':
    client.start(bot_token=token)
    if client.is_connected():
        print('bot Connected')
    client.run_until_disconnected()





