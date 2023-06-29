from email import message
from urllib import response
import requests
import vk_api
import telebot
import json
import time
from telebot import types
from threading import Thread
from vk_api.longpoll import VkLongPoll
from datetime import datetime
from time import sleep

data=json.loads(open("data.json", "r").read())
chats=json.loads(open("chats.json", "r").read())

activeChat=0

thisChat = False
token_TG=None
smeshBot = telebot.TeleBot(data["tg_token"])

id_TG = data.get('tg_id', 0)

token_VK = vk_api.VkApi(token=data["vk_token"])
token_VK.http.headers.update({'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})
vk = token_VK._auth_token()
vk = token_VK.get_api()

# Функция привязки бота
def registraion(message):
    global id_TG
    if id_TG and message.chat.id != id_TG:
        smeshBot.reply_to(message, f"Бот уже привязан к аккаунту телеграмм с ID: {id_TG}")
        return
    id_TG = message.chat.id
    data["tg_id"] = id_TG
    data_file = open("data.json", "w").write(json.dumps(data))
    smeshBot.reply_to(message, f"Привязка к ID: {id_TG}")

# Обработчик событий при вводе команды "start"
@smeshBot.message_handler(commands=['start'])
def start(message):
    global id_TG
    if id_TG and message.chat.id != id_TG:
        smeshBot.send_message(message.chat.id, "<b>🛑Вы не можете использовать этого бота, т.к. он уже привязан к другому аккаунту Telegram🛑</b>",parse_mode='HTML')
        return
    elif "password" in data:
        if data["password"] == message.text.split()[1]:
            registraion(message) 
            # добавляем кнопки в главное меню при старте бота
            main_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
            chats_btn = types.KeyboardButton('Чаты 🗨️')
            friends_btn = types.KeyboardButton('Друзья 👥')
            main_markup.add(chats_btn, friends_btn)
            smeshBot.send_message(message.chat.id, "`📱 Выберите пункт меню `", reply_markup=main_markup, parse_mode="MarkdownV2")
        else:
            smeshBot.send_message(message.chat.id,"Пароль неверный")
    else:
        registraion(message)

#Обработчик кнопки назад которая переносит в главное меню
@smeshBot.message_handler(func=lambda message: message.text == 'Назад ◀️')
def back_to_menu(message):
    try:
        if id_TG and message.chat.id == id_TG:
            keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
            buttonChats = types.KeyboardButton('Чаты 🗨️')
            buttonFriends = types.KeyboardButton('Друзья 👥')
            buttonAddChats = types.KeyboardButton('Добавить чат 🆕')
            buttonDelChats = types.KeyboardButton('Удалить чат 🗑️')
            buttonUnread = types.KeyboardButton('Непрочитанные 😴')
            keyboard.add(buttonChats, buttonFriends, buttonAddChats, buttonDelChats, buttonUnread)
            smeshBot.send_message(message.chat.id, '<b>Вы вернулись в меню 🏠</b>', reply_markup=keyboard, parse_mode='HTML')
        else:
            smeshBot.send_message(message.chat.id, "<b>🛑Вы не можете использовать этого бота, т.к. он уже привязан к другому аккаунту Telegram🛑</b>",parse_mode='HTML')
        return
    except Exception as e:
        smeshBot.send_message(message.chat.id, f"Что-то упало 😔\n{str(e)}", reply_markup=keyboard)

# Вывод клавиатуры с списком чатов из chats.json
@smeshBot.message_handler(func=lambda message: message.text == 'Чаты 🗨️')
def switch(message):
    try:
        if id_TG and message.chat.id == id_TG:
            keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
            buttonsAllChats = []
            for i in chats.keys():
                buttonsAllChats.append('Чат ' + str(i))
            buttonsAllChats.append('Назад ◀️')
            keyboard.add(*buttonsAllChats)
            smeshBot.send_message(message.chat.id, "<b>Выберите чат ✉️</b>", reply_markup=keyboard,parse_mode='HTML')
        else:
            smeshBot.send_message(message.chat.id, "<b>🛑Вы не можете использовать этого бота, т.к. он уже привязан к другому аккаунту Telegram🛑</b>",parse_mode='HTML')
        return
    except Exception as e:
        smeshBot.send_message(message.chat.id, f"Что-то упало 😔\n{str(e)}",reply_markup=keyboard)


#Обработчик кнопки "Добавить чат"
@smeshBot.message_handler(func=lambda message: message.text == 'Добавить чат 🆕')
def add_chat_handler(message):
    if id_TG and message.chat.id == id_TG:
        smeshBot.send_message(message.chat.id, '<b> 📝 Введите название чата:</b>',parse_mode='HTML')
        smeshBot.register_next_step_handler(message, process_chat_name)
    else:
        smeshBot.send_message(message.chat.id, "<b>🛑Вы не можете использовать этого бота, т.к. он уже привязан к другому аккаунту Telegram🛑</b>",parse_mode='HTML')

#Функция добавления чата, а именно введения id чата
def process_chat_name(message):
    chat_name = message.text
    smeshBot.send_message(message.chat.id, '<b>🆔 Введите ID чата:</b>',parse_mode='HTML')
    smeshBot.register_next_step_handler(message, process_chat_id, chat_name)

#Функция добавления чата в файл chats
def add_chat(name, chat_id):
    chats[name] = chat_id
    with open("chats.json", "w") as file:
        json.dump(chats, file)

#Функция добавления чата
def process_chat_id(message, chat_name):
    chat_id = message.text
    add_chat(chat_name, chat_id)
    smeshBot.send_message(message.chat.id, f'<b>Чат "{chat_name}" успешно добавлен 👍</b>',parse_mode='HTML')


#Обработчик кнопки "Удалить чат"
@smeshBot.message_handler(func=lambda message: message.text == 'Удалить чат 🗑️')
def delete_chat_handler(message):
    try:
        if id_TG and message.chat.id == id_TG:
            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
            buttonsDelChat = []
            for name, chat_id in chats.items():
                button_text = f'{name} ({chat_id})'
                button = types.KeyboardButton(button_text)
                keyboard.add(button)
            buttonsDelChat.append('Назад ◀️')
            keyboard.add(*buttonsDelChat)
            smeshBot.send_message(message.chat.id, '<b>🗑️ Выберите чат для удаления:</b>', reply_markup=keyboard,parse_mode='HTML')
            smeshBot.register_next_step_handler(message, process_delete_chat)
        else:
            smeshBot.send_message(message.chat.id, "<b>🛑Вы не можете использовать этого бота, т.к. он уже привязан к другому аккаунту Telegram🛑</b>",parse_mode='HTML')
    except Exception as e:
        smeshBot.send_message(message.chat.id, f"Что-то упало 😔\n{str(e)}")

#Функция удаления чата
def process_delete_chat(message):
    try:
        chat_info = message.text
        if message.text == 'Назад ◀️':
            back_to_menu(message)
            return
        elif ' (' in chat_info:
            chat_name, chat_id = chat_info.split(' (')
            chat_id = chat_id[:-1]
            try:
                del chats[chat_name]
                with open("chats.json", "w") as file:
                    json.dump(chats, file)
                smeshBot.send_message(message.chat.id, f'<b>🗑️✅ Чат "{chat_name}" успешно удален</b>',parse_mode='HTML')
            except KeyError:
                smeshBot.send_message(message.chat.id, f'<b>❌Чат "{chat_name}" не найден❌</b>',parse_mode='HTML')
            except Exception as e:
                smeshBot.send_message(message.chat.id, f'<b>🙁 Произошла ошибка:</b>{str(e)}',parse_mode='HTML')
    except Exception as e:
        smeshBot.send_message(message.chat.id, f"Что-то упало 😔\n{str(e)}")
########******########

#Обработчик кнопки "Непрочитанные" для просмотра последних непрочитанных сообщений из личных чатов
@smeshBot.message_handler(func=lambda message: message.text == 'Непрочитанные 😴')
def get_unread_messages(message):
    try:
        if id_TG and message.chat.id == id_TG:
            unread = vk.messages.getConversations(unread=1, extended=1)
            count = unread['count']
            if count > 0:
                messages = []
                for item in unread['items']:
                    conversation = item['conversation']
                    peer = conversation['peer']
                    if peer['type'] == 'user':
                        item_message = item['last_message']
                        text = item_message.get('text', '')
                        if text and item_message['from_id'] != token_VK.method('users.get', {'fields': 'id'})[0]['id']:
                            user_id = peer['id']
                            user = vk.users.get(user_ids=user_id)[0]
                            name = f"{user['first_name']} {user['last_name']}"
                            message_text = f"{name}: {text} \U0001F4AC"
                            messages.append(message_text)
                if messages:
                    smeshBot.send_message(message.chat.id, '\n'.join(messages))
                else:
                    smeshBot.send_message(message.chat.id, "<b>👌😊 Нет непрочитанных сообщений 👌😊</b>",parse_mode='HTML')
            else:
                smeshBot.send_message(message.chat.id, "<b>👌😊 Нет непрочитанных сообщений 👌😊</b>",parse_mode='HTML')
        else:
            smeshBot.send_message(message.chat.id, "<b>🛑Вы не можете использовать этого бота, т.к. он уже привязан к другому аккаунту Telegram🛑</b>",parse_mode='HTML')
        return
    except Exception as e:
        smeshBot.send_message(message.chat.id, f"Что-то упало 😔\n{str(e)}")


#Смена чатов и показ в сети ли собеседник
@smeshBot.message_handler(func=lambda message: message.text.startswith('Чат '))
def switch(message):
    global thisChat
    global activeChat
    try:
        if id_TG and message.chat.id == id_TG:
            if chats[message.text.split()[1]] is not None and "_chat" not in message.text:
                activeChat = token_VK.method("users.get", {"user_ids": chats[message.text.split()[1]]})[0]["id"]
                smeshBot.send_message(message.chat.id, f"<b>✅ Чат сменен на {message.text.split()[1]} 🗨️</b>",parse_mode='HTML')
                thisChat = False
            elif chats[message.text.split()[1]] is not None and "_chat" in message.text:
                activeChat = 2000000000 + int(chats[message.text.split()[1]])
                thisChat = True
                smeshBot.send_message(message.chat.id, f"<b>✅ Чат сменен на {message.text.split()[1]} 🗨️</b>",parse_mode='HTML')
            else:
                smeshBot.send_message(message.chat.id, "<b>❌Такого чата в базе нет❌</b>",parse_mode='HTML')

            # Получаем информацию о пользователе и формируем сообщение со статусом
            user_info = token_VK.method("users.get", {"user_ids": activeChat, "fields": "last_seen,online"})[0]
            if user_info["online"]:
                status = '🟢 В сети'
            elif "last_seen" in user_info:
                last_seen = user_info["last_seen"]["time"]
                last_seen_time = datetime.fromtimestamp(last_seen).strftime("%d.%m.%Y %H:%M:%S")
                status = f'🕰️ Был(а) в сети {last_seen_time}'
            else:
                status = '⚫ Не в сети'
            user_status = f'👤 {user_info["first_name"]} {user_info["last_name"]} - {status}'
            smeshBot.send_message(message.chat.id, user_status)
        else:
            smeshBot.send_message(message.chat.id, "<b>🛑Вы не можете использовать этого бота, т.к. он уже привязан к другому аккаунту Telegram🛑</b>",parse_mode='HTML')
        return

    except Exception as e:
        smeshBot.send_message(message.chat.id, f"Что-то упало 😔\n{str(e)}")

# Проверка друзей онлайн
@smeshBot.message_handler(func=lambda message: message.text == 'Друзья 👥')
def show_friends(message):
    try:
        if id_TG and message.chat.id == id_TG:
            friends = token_VK.method('friends.get', {'user_id': token_VK.method('users.get')[0]['id'], 'fields': 'online'})
            online_friends = []
            for friend in friends['items']:
                if friend['online']:
                    online_friends.append('🟢 ' + friend['first_name'] + ' ' + friend['last_name'])
            if len(online_friends) > 0:
                smeshBot.send_message(message.chat.id, "👥 <b>Друзья онлайн:</b>\n" + "\n".join(online_friends),parse_mode='HTML')
            else:
                smeshBot.send_message(message.chat.id, "<b>🚫Нет друзей онлайн.🚫</b>",parse_mode='HTML')
        else:
                smeshBot.send_message(message.chat.id, "<b>🛑Вы не можете использовать этого бота, т.к. он уже привязан к другому аккаунту Telegram🛑</b>",parse_mode='HTML')
        return
    except Exception as e:
        smeshBot.send_message(message.chat.id, f"Что-то упало 😔\n{str(e)}")




#Отправка сообщений и вложений из ТГ в ВК
@smeshBot.message_handler(content_types=["text", "sticker"])
def send(message):
    try:
        if message.text and message.text[0] != "/" and message.text[0] != "!":
            vk.account.setOffline()
            # Отправляем текстовое сообщение
            vk.messages.send(user_id=str(activeChat), random_id=0, message=str(message.text))
            vk.account.setOffline()
        elif message.sticker:
            vk.account.setOffline()
            # Отправляем стикер
            attachment = f"sticker{message.sticker.file_id}"
            vk.messages.send(user_id=str(activeChat), random_id=0, attachment=attachment)
            vk.account.setOffline()
            # Если сообщение было успешно отправлено, ничего не пишем, иначе отправляем сообщение об ошибке в телеграм
            if not response:
                smeshBot.send_message(id_TG, "<b>❌Не удалось отправить сообщение в VK❌</b>",parse_mode='HTML')
    except Exception as e:
        smeshBot.send_message(message.chat.id, f"Не выбран чат😔")

# Обработчик для фото, голосовых сообщений и документов
@smeshBot.message_handler(content_types=['photo', 'voice', 'document'])
def handle_media(message):
    try:
        if message.photo:
            # обработка фото        
            file_info = smeshBot.get_file(message.photo[-1].file_id)
            downloaded_file = smeshBot.download_file(file_info.file_path)

            upload_url = vk.photos.getMessagesUploadServer()['upload_url']
            response = token_VK.http.post(upload_url, files={'photo': ('photo.jpg', downloaded_file, 'image/jpeg')})
            photo_data = response.json()
            photo = vk.photos.saveMessagesPhoto(**photo_data)[0]

            vk.messages.send(user_id=str(activeChat), random_id=0, attachment=f"photo{photo['owner_id']}_{photo['id']}")
        elif message.voice:
            # обработка голосовых сообщений
            file_info = smeshBot.get_file(message.voice.file_id)
            downloaded_file = smeshBot.download_file(file_info.file_path)

            upload_url = vk.docs.getMessagesUploadServer(type='audio_message')['upload_url']
            response = token_VK.http.post(upload_url, files={'file': ('voice.ogg', downloaded_file)})
            audio_data = response.json()

            audio_message = vk.docs.save(file=audio_data['file'], title='voice.ogg', tags='voice')['audio_message']

            vk.messages.send(user_id=str(activeChat), random_id=0, attachment=f"doc{audio_message['owner_id']}_{audio_message['id']}")
    except Exception as e:
        smeshBot.send_message(message.chat.id, f"Что-то упало 😔\n{str(e)}")
        

# Функция ответа на сообщение 
def get_reply(message_data):
    replier = vk.users.get(user_ids=message_data['reply_message']["from_id"])[0]
    return f"{replier['first_name']} {replier['last_name']}: {message_data['reply_message']['text']}"
 
#Функция пересылки сообщений из VK в TG
def vk_work():
    try:
        print("VK loaded")

        longpoll = VkLongPoll(token_VK)
        for event in longpoll.listen():
            try:
                if event.message_id is not None:
                    message_data = vk.messages.getById(message_ids=event.message_id)['items'][0]
                    sender = vk.users.get(user_ids=event.user_id)[0]
                    if event.from_me is False and event.from_user is True: # Сообщение из лички
                        if "reply_message" in message_data:
                            reply_text = get_reply(message_data)
                            formatted_reply = f"{reply_text} |\n  📩 <b>{sender['first_name']} {sender['last_name']}</b>: {message_data['text']}"
                            smeshBot.send_message(data["tg_id"], formatted_reply, parse_mode='HTML')
                        else:
                            text = event.message
                            attachments = message_data.get('attachments')
                            if attachments:
                                text = f"{sender['first_name']} {sender['last_name']}:\n{text}" if text else ""
                                for attachment in attachments:
                                    if attachment['type'] == 'audio_message':# Отправка голосовых
                                        smeshBot.send_voice(data["tg_id"], attachment['audio_message']['link_ogg'], caption=text)
                                    elif attachment['type'] == 'photo':# Отправка фото
                                        sizes = attachment['photo']['sizes']
                                        photo_url = sizes[-1]['url'] 
                                        photo_file = requests.get(photo_url).content
                                        smeshBot.send_photo(data["tg_id"], photo_file, caption=text)
                                    elif attachment['type'] == 'video':# Отправка видео
                                        video_info = attachment['video']
                                        best_quality_url = max((url for url in video_info['files'] if url.split('_')[1].isdigit()), key=lambda x: int(x.split('_')[1]))
                                        video_url = 'https://' + best_quality_url
                                        video_file = requests.get(video_url).content
                                        smeshBot.send_video(data["tg_id"], video_file, caption=text)
                                    elif attachment['type'] == 'sticker':# Отправка стикеров
                                        sticker_info = attachment['sticker']
                                        sticker_images = sticker_info['images']
                                        biggest_sticker = max(sticker_images, key=lambda x: x['width'])
                                        sticker_url = biggest_sticker['url']
                                        smeshBot.send_sticker(data["tg_id"], sticker_url)
                            else:
                                formatted_text = f"<b>{sender['first_name']} {sender['last_name']}</b>: 📩\n{text}"
                                smeshBot.send_message(data["tg_id"], formatted_text, parse_mode='HTML')
            except Exception as e:
                smeshBot.send_message(message.chat.id, f"Что-то упало 😔\n{str(e)}")
    except Exception as e:
        Thread(target=vk_work).start()


Thread(target=vk_work).start()
while True:
    try:     
        Thread(target=smeshBot.infinity_polling(none_stop=True)).start()
 
    except Exception as e:
        smeshBot.send_message(message.chat.id, f"Что-то упало 😔\n{str(e)}")


