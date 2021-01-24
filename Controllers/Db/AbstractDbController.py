from Controllers.CliArgsController import CliArgsController
from Controllers.Log.LogController import LogController

from types import ModuleType
from typing import Any


class AbstractDbController:

    DB_MODULE: ModuleType
    DB_PARAMS: dict

    cursor: str
    conn: str

    def __init__(self) -> None:
        self.config = CliArgsController().getConfig()
        self.logger = LogController()

    def _openConnection(self) -> None:
        self.conn = self.DB_MODULE.connect(**self.DB_PARAMS)
        self.cursor = self.conn.cursor()

    def _executeQuery(self, query: str) -> Any:
        self.cursor.execute(query)
        self.conn.commit()
        return self.cursor.lastrowid

    def _closeConnection(self) -> None:
        self.cursor.close()
        self.conn.close()

    def fetchResult(self) -> list:
        rows = self.cursor.fetchall()
        return [row for row in rows]

    def submitQuery(self, query: str) -> Any:
        try:
            self._openConnection()
            record_id = self._executeQuery(query)
            self._closeConnection()
            return record_id
        except self.DB_MODULE.Error as error:
            self.logger.alert(f'Error while connecting to database: {error}')
            print('Problem query: ', query)

    def fetchQuery(self, query: str) -> list:
        try:
            self._openConnection()
            self._executeQuery(query)
            result = self.fetchResult()
            self._closeConnection()
            return result

        except self.DB_MODULE.Error as error:
            self.logger.alert(f'Error while connecting to database: {error}')
            print('Problem query: ', query)

    def makeDump(self) -> None: ...
    def dropDb(self) -> None: ...