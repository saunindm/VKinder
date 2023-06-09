import logger
import api
import chatbot
from vk_api.longpoll import VkEventType
import models
from models import Session, engine

# create a Session
session = Session()
connection = engine.connect()


def main():
    """
    Receives a message from the user and sends a response message.
    """
    vk_bot = chatbot.VKBot()
    vk_api = api.VkApi()
    stack = []
    flag_favourites = False
    flag_black = False

    @logger.logger('log_file.txt')
    def get_user_for_bot(user_id):
        """
        Gets information about the user by his ID: city, sex, bdate.
        Checks if the user exists in the database, if not then adds.
        Gets vk user data by the specified parameters: city, gender, age.
        Returns information about user in following format:
        First name, Last name
        Profile link
        three photos as attachments, taken from method get_photos_from_profile()
        :param user_id: int
        :return: list
        """
        city, sex, bdate = vk_api.get_user_info(user_id)
        if models.check_if_bot_user_exists(user_id) is None:
            models.add_bot_user(user_id)
        return vk_api.search_user(city, sex, bdate)

    @logger.logger('log_file.txt')
    def add_user_to_db(bot_user_id, flag_list):
        """
        Adds user information to favourites or black list.
        flag_list True - adds user information to favourites list.
        flag_list False - adds user information to black list.
        :param bot_user_id: bot_user_id
        :param flag_list: Boolean
        :return: Boolean
        """
        nonlocal flag_favourites
        nonlocal flag_black
        if not stack or (flag_list and not flag_favourites):
            vk_bot.send_msg(event.user_id, "Nothing to add")
            return False
        elif not stack or (not flag_list is None and not flag_black):
            vk_bot.send_msg(event.user_id, "Nothing to add")
            return False
        first_name, last_name, url, user_attachment = stack.pop()
        vk_user_id = int(url.split('id')[1])
        if flag_list and models.check_if_match_exists(vk_user_id)[0] is None:
            vk_bot.send_msg(event.user_id, "Added to favourites")
            flag_favourites = False
            models.add_new_match_to_favourites(vk_user_id, bot_user_id, first_name, last_name, url)
            models.add_photo_of_the_match(user_attachment, vk_user_id)
            return True
        elif not flag_list and models.check_if_match_exists(vk_user_id)[1] is None:
            vk_bot.send_msg(event.user_id, "Added to black list")
            flag_black = False
            models.add_new_match_to_black_list(vk_user_id, bot_user_id, first_name, last_name, url)
            models.add_photo_of_the_match(user_attachment, vk_user_id)
            return True
        return False

    for event in vk_bot.longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                message = event.text.lower()
                if message == "hello":
                    vk_bot.send_msg(event.user_id, 'Hello, press button "Show" to start')
                elif message == "favourites list":
                    for user in models.show_favourites_list(event.user_id):
                        msg = f'{user[0]} {user[1]}\n{user[2]}'
                        vk_bot.send_msg(event.user_id, message=msg, attachment=user[3])
                elif message == "black list":
                    for user in models.show_black_list(event.user_id):
                        msg = f'{user[0]} {user[1]}\n{user[2]}'
                        vk_bot.send_msg(event.user_id, message=msg, attachment=user[3])
                elif message == "add to favourites":
                    add_user_to_db(event.user_id, True)
                elif message == "no, thank you":
                    add_user_to_db(event.user_id, False)
                elif message == "show":
                    data = get_user_for_bot(event.user_id)
                    msg = f'{data[0]} {data[1]}\n{data[2]}'
                    stack.append(data)
                    vk_bot.send_msg(event.user_id, message=msg, attachment=data[3])
                    flag_favourites, flag_black = True, True
                else:
                    vk_bot.send_msg(event.user_id, "Sorry, I don't know this command")


if __name__ == '__main__':
    main()
