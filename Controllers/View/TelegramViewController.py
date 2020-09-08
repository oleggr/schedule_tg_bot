import json
from telebot import types

from Controllers.Date.DateTimeController import DateTimeController
from DbManager import DbManager


class TelegramViewController:
    icons = {
        "snowman": u'\U000026C4',
        "watches": u'\U0001F551',
        "look_here_left": u'\U0001F449',
        "look_here_right": u'\U0001F448'
    }

    @staticmethod
    def getUniversityKeyboardMarkup():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        universities = DbManager().getUniversities()

        for university in universities:
            markup.row(university[0])

        return markup

    # old method
    # probably should be removed
    @staticmethod
    def getGroupKeyboardMarkup(universityId):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        groups = DbManager().getGroupsByUniversityId(universityId)

        for group in groups:
            markup.row(group[1])

        return markup

    @staticmethod
    def removeKeyboardMarkup():
        removeKeyboard = {'remove_keyboard': True}
        removeKeyboardEncoded = json.dumps(removeKeyboard)
        return removeKeyboardEncoded

    @staticmethod
    def getScheduleKeyboardMarkup():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        day_id = DateTimeController.getCurrDayOfWeek()
        days_of_week = DateTimeController.days_of_week
        days_of_week[day_id] = TelegramViewController.applyLookHereFilter(days_of_week[day_id])

        keyboard = [
            [days_of_week[0], days_of_week[1]],
            [days_of_week[2], days_of_week[3]],
            [days_of_week[4], days_of_week[5]]
        ]

        for keys in keyboard:
            markup.row(keys[0], keys[1])

        return markup

    @staticmethod
    def applyMarkup(params: list):

        watches = TelegramViewController.icons.get('watches')

        result = [
            # watches + " *" + params[0] + "*",       # time
            " *" + params[0] + "*",     # time
            "_" + params[1] + "_",      # lesson name
            params[4],                  # type of lesson
            params[2],                  # room
            params[3]                   # teacher name
        ]

        return result

    @staticmethod
    def applyLookHereFilter(word):
        if TelegramViewController.icons["look_here_left"] in word \
                or TelegramViewController.icons["look_here_right"] in word:
            return word
        else:
            return TelegramViewController.icons["look_here_left"] \
                   + word \
                   + TelegramViewController.icons["look_here_right"]

    @staticmethod
    def removeLookHereFilter(word):
        res = word.split(TelegramViewController.icons["look_here_left"])[1]
        res = res.split(TelegramViewController.icons["look_here_right"])[0]
        return res