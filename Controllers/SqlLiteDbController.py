import os
import sqlite3

from Controllers.Log.LogController import LogController
from Controllers.CliArgsController import CliArgsController


class SqlLiteDbController:

    conn = ""
    cursor = ""

    def __init__(self):
        self.config = CliArgsController.getConfig()
        self.logger = LogController()

    def openConnection(self):
        self.conn = sqlite3.connect(self.config.DB_FILENAME)
        self.cursor = self.conn.cursor()

    def executeQuery(self, query: str):
        self.cursor.execute(query)
        return self.cursor.lastrowid

    def commitQuery(self):
        self.conn.commit()

    def closeConnection(self):
        self.cursor.close()
        self.conn.close()

    def fetchResult(self):
        rows = self.cursor.fetchall()
        result = []

        for row in rows:
            result.append(row)

        return result

    def submitQuery(self, query: str):
        try:
            self.openConnection()
            record_id = self.executeQuery(query)
            self.commitQuery()
            self.closeConnection()
            return record_id
        except sqlite3.Error as error:
            self.logger.alert('Error while connecting to database: {}'.format(error))
            print('Problem query: ', query)

    def fetchQuery(self, query: str):
        try:
            self.openConnection()
            self.executeQuery(query)
            result = self.fetchResult()
            self.closeConnection()
            return result

        except sqlite3.Error as error:
            self.logger.alert('Error while connecting to database: {}'.format(error))
            print('Problem query: ', query)

    def dropDb(self):
        try:
            os.remove(self.config.DB_FILENAME)
            self.logger.info('DB was deleted')
        except Exception as e:
            self.logger.alert('Error while deleting db: {}'.format(e))

    def makeDump(self):
        try:
            self.openConnection()
            with open(self.config.DUMP_FILENAME, 'w') as file:
                for line in self.conn.iterdump():
                    file.write('%s\n' % line)
            self.closeConnection()
        except Exception as e:
            self.logger.alert('Error while dumping db: {}'.format(e))
