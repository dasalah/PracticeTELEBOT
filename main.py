from telethon import TelegramClient, events, Button
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
                        )
#proxy=("HTTP","127.0.0.1",8087)
#special words for not declare for it
special_words=["لغو","ثبت نام","درباره ما","تایید میکنم","پیشنهاد"]

#replace your id channel for Forced joining in the channel
idchannel = None  # Will use database settings instead

# Admin commands list
admin_commands = ['/set_force_channel', '/toggle_force_join', '/force_join_stats']


@client.on(events.NewMessage(pattern=r'^/start',func= lambda e: e.is_private))
async def star(event : Message):
    # Use new force join system
    if not await check_force_join(event, client):
        return

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
    # Check for admin commands first
    if any(event.text.startswith(cmd) for cmd in admin_commands):
        await handle_admin_commands(event, client)
        return
        
    # Use new force join system
    if not await check_force_join(event, client):
        return
        
    # if word in special words
    if event.text in special_words:
        return

    #for signUp#
    if event.chat_id in users_status and users_status[event.chat_id]["step"] != 0:
        await save_information(event,client,users_status)
    #for signUp#

    if event.chat_id in users_status and users_status[event.chat_id]["step"] == "message":
        await save_comment_to_excel(event,users_status,client)


# if text in special words
@client.on(events.NewMessage(func = lambda e : e.text in special_words))
async def action(event):
    # Use new force join system
    if not await check_force_join(event, client):
        return
    await handle_SpecialWords(event,client,users_status)

# Handle callback queries (inline button presses)
@client.on(events.CallbackQuery)
async def callback_query_handler(event):
    if event.data == b"check_membership":
        # Re-check membership when user clicks "Check Membership Again"
        if await check_force_join(event, client):
            await event.edit("✅ عضویت شما تأیید شد! حالا می‌تونید از ربات استفاده کنید.")
            # Show main menu
            await start(event, client)
        else:
            await event.answer("❌ هنوز عضو چنل نشده‌اید. لطفاً ابتدا عضو شوید.", alert=True)


if __name__ == '__main__':
    client.start(bot_token=token)
    if client.is_connected():
        print('bot Connected')

    client.run_until_disconnected()




