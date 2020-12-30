from datetime import datetime, timedelta
import Controllers.Translation.MessagesTranslation.ru as ru
import Controllers.Translation.MessagesTranslation.en as en


class DateTimeController:

    days_of_week = ru.WEEK_DAYS
    days_of_week_eng = en.WEEK_DAYS

    @staticmethod
    def getCurrDate():
        return datetime.now().strftime("%d-%m-%Y")

    @staticmethod
    def getCurrDateAndTime():
        return datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    @staticmethod
    def getCurrDayOfWeek():
        return datetime.today().weekday()

    @staticmethod
    def getCurrTimestamp():
        return datetime.now().timestamp()

    @staticmethod
    def getDateDifference(days_count):
        return (datetime.now() - timedelta(days=days_count)).timestamp() 