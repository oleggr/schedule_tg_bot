from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
# from telebot import types
# import cherrypy

from Configs.tgConfig import *
from DbManager import DbManager
from Controllers.View.TelegramViewController import TelegramViewController
from Controllers.Translation.TranslationController import TranslationController
from Controllers.User.UserController import UserController

from Controllers.Log.LogController import LogController
from MonitoringAlertManager import MonitoringAlertManager

from ParseManager import ParseManager

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

dbManager = DbManager()
parseManager = ParseManager()

viewController = TelegramViewController()
userController = UserController()

logger = LogController()
notificator = MonitoringAlertManager()

translator = TranslationController()

# class WebhookServer(object):
#     @cherrypy.expose
#     def index(self):
#         if 'content-length' in cherrypy.request.headers and \
#                 'content-type' in cherrypy.request.headers and \
#                 cherrypy.request.headers['content-type'] == 'application/json':
#
#             length = int(cherrypy.request.headers['content-length'])
#             json_string = cherrypy.request.body.read(length).decode("utf-8")
#             update = telebot.types.Update.de_json(json_string)
#
#             bot.process_new_updates([update])
#             return ''
#         else:
#             raise cherrypy.HTTPError(403)


@dp.message_handler(commands=["start", "changeuniversity"])
async def chooseUniversity(message):
    userInfo = {
        'user_id': message.from_user.id,
        'chat_id': message.chat.id,
        'first_name': message.from_user.first_name,
        'last_name': message.from_user.last_name,
        'username': message.from_user.username,
        'is_alive': True
    }

    if not dbManager.checkUserExist(message.from_user.id):
        dbManager.addTgUser(userInfo)

        log_msg = "Bot was started by the user id: {}, name: {}, username: {}".format(
            message.from_user.id,
            message.from_user.first_name,
            message.from_user.username
        )
        notificator.notify(log_msg, MonitoringAlertManager.INFO_LEVEL)
        logger.info(log_msg)
    else:
        # probably reinstalled
        # todo: add handler in user activity tracking task
        dbManager.updateTgUser(message.from_user.id, "is_alive", "1")
        dbManager.updateTgUser(message.from_user.id, "university_id", "NULL")
        dbManager.updateTgUser(message.from_user.id, "group_id", "NULL")

        log_msg = "User {} restarted the bot".format(userInfo.get("username"))
        notificator.notify(log_msg, MonitoringAlertManager.INFO_LEVEL)
        logger.info(log_msg)

    await send_message_custom(
        message,
        translator.getMessage(
            message.from_user.language_code,
            translator.ENTER_UNIVERSITY
        ).format(message.from_user.first_name),
        reply_markup=viewController.getUniversityKeyboardMarkup()
    )


@dp.message_handler(commands=["changegroup"])
async def sendHelp(message):
    dbManager.updateTgUser(message.from_user.id, "group_id", "NULL")
    await send_message_custom(
        message,
        translator.getMessage(
            message.from_user.language_code,
            translator.CHANGE_GROUP
        ).format(message.from_user.first_name),
        reply_markup=viewController.removeKeyboardMarkup()
    )


@dp.message_handler(commands=["help"])
async def sendHelp(message):
    await send_message_custom(
        message,
        translator.getMessage(
            message.from_user.language_code,
            translator.HELP
        ).format(message.from_user.first_name),
    )


@dp.message_handler()
async def main(message):
    userController.CURR_STATUS = userController.getCurrStatus(message.from_user.id)
    dbManager.writeUserMessage(message.from_user.id, userController.CURR_STATUS, message.text)

    if userController.CURR_STATUS == userController.DEFAULT_STATUS:
        universities = dbManager.getUniversities()

        for university in universities:
            if message.text == university[0]:
                universityId = dbManager.getUniversityIdByName(message.text)[0][0]
                dbManager.updateTgUser(message.from_user.id, "university_id", universityId)

                await send_message_custom(
                    message,
                    translator.getMessage(
                        message.from_user.language_code,
                        translator.FIRST_ENTER_GROUP
                    ).format(message.from_user.first_name),
                    reply_markup=viewController.removeKeyboardMarkup()
                )
                break

    elif userController.CURR_STATUS == userController.UNIVERSITY_CHOSEN:
        universityId = userController.getUserUniversityId(message.from_user.id)
        groups = dbManager.getGroupsByUniversityId(universityId)
        userGroupName = parseManager.filterGroup(message.text, universityId)

        isGroupFound = False

        for group in groups:
            if userGroupName == group[1]:
                groupId = group[0]
                dbManager.updateTgUser(
                    message.from_user.id, "group_id", groupId)

                isGroupFound = True
                await send_message_custom(
                    message,
                    translator.getMessage(
                        message.from_user.language_code,
                        translator.SCHEDULE_WAS_FOUND
                    ).format(message.from_user.first_name),
                    reply_markup=viewController.getScheduleKeyboardMarkup()
                )
                break

        if not isGroupFound:
            json_text = parseManager.getJson(universityId, userGroupName)
            if len(json_text) > 2:
                groupInfo = {
                    "group_name": userGroupName,
                    "university_id": universityId,
                    "schedule_text": json_text,
                    "schedule_url": "default url"
                }

                dbManager.addGroup(groupInfo)
                groupId = dbManager.getGroupId(groupInfo)
                dbManager.updateTgUser(
                    message.from_user.id,
                    "group_id",
                    groupId
                )

                await send_message_custom(
                    message,
                    translator.getMessage(
                        message.from_user.language_code,
                        translator.SCHEDULE_DOWNLOADED
                    ).format(message.from_user.first_name),
                    reply_markup=viewController.getScheduleKeyboardMarkup()
                )
            else:
                await send_message_custom(
                    message,
                    translator.getMessage(
                        message.from_user.language_code,
                        translator.SCHEDULE_WAS_NOT_FOUND
                    ).format(message.from_user.first_name),
                )

    elif userController.CURR_STATUS == userController.GROUP_CHOSEN:
        userGroupId = userController.getUserGroupId(message.from_user.id)
        groupJsonText = dbManager.getGroupJsonById(userGroupId)

        if message.text == "Понедельник" \
                or message.text == "Вторник" \
                or message.text == "Среда" \
                or message.text == "Четверг" \
                or message.text == "Пятница" \
                or message.text == "Суббота":
            await send_message_custom(
                message,
                parseManager.getDaySchedule(message.text, groupJsonText),
                reply_markup=viewController.getScheduleKeyboardMarkup()
            )

        if message.text == TelegramViewController.applyLookHereFilter("Понедельник") \
                or message.text == TelegramViewController.applyLookHereFilter("Вторник") \
                or message.text == TelegramViewController.applyLookHereFilter("Среда") \
                or message.text == TelegramViewController.applyLookHereFilter("Четверг") \
                or message.text == TelegramViewController.applyLookHereFilter("Пятница") \
                or message.text == TelegramViewController.applyLookHereFilter("Суббота"):
            day = TelegramViewController.removeLookHereFilter(message.text)
            await send_message_custom(
                message,
                parseManager.getDaySchedule(day, groupJsonText),
                reply_markup=viewController.getScheduleKeyboardMarkup()
            )


async def send_message_custom(
        message,
        text: str,
        reply_markup=None,
        parse_mode="markdown"
):
    try:
        await bot.send_message(
            message.chat.id,
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )

    except Exception as e:
        if "bot was blocked by the user" in str(e):
            dbManager.updateTgUser(message.from_user.id, "is_alive", "0")

            error_message = 'Send message error: user {} blocked the bot'.format(message.from_user.id)
            notificator.notify(error_message, notificator.WARNING_LEVEL)
            logger.alert(error_message)
        else:
            error_message = 'Send message error with user {}: {}'.format(message.from_user.id, e)
            notificator.notify(error_message, notificator.DISASTER_LEVEL)
            logger.alert(error_message)


#bot.remove_webhook()
try:
    notificator.notify("Polling started", notificator.INFO_LEVEL)
    logger.info("Polling started")

    executor.start_polling(dp)

    notificator.notify("Polling stopped manually", notificator.WARNING_LEVEL)
    logger.info("Polling stopped manually")
except Exception as e:
    notificator.notify('Error while polling: {}'.format(e), notificator.DISASTER_LEVEL)
    logger.alert('Error while polling: {}'.format(e))

# notificator.notify("Webhook set", notificator.INFO_LEVEL)
# logger.info("Webhook set")
#
# bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH, certificate=open(WEBHOOK_SSL_CERT, 'r'))
#
# info = bot.get_webhook_info()
# notificator.notify(f'Webhook info: {info}', notificator.INFO_LEVEL)
#
# cherrypy.config.update({
#     'server.socket_host': WEBHOOK_LISTEN,
#     'server.socket_port': WEBHOOK_PORT,
#     'server.ssl_module': 'builtin',
#     'server.ssl_certificate': WEBHOOK_SSL_CERT,
#     'server.ssl_private_key': WEBHOOK_SSL_PRIV
# })
#
# cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
#
# notificator.notify("Webhook dead", notificator.DISASTER_LEVEL)
# logger.info("Webhook dead")