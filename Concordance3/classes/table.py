from types import SimpleNamespace


class Record:

    def __init__(self, columns = None, record = None) -> None:
        self.record = SimpleNamespace()
        self.insert(columns, record)

    def insert(self, columns: tuple, values: object) -> bool:
        if values is not None:
            for i in range(0, len(columns)):
                setattr(self.record, columns[i], values[i])
            return True
        else:
            return False

    def get(self, column):
        return self.record.__getattribute__(column)



class Table:

    def __init__(self, db: object) -> None:
        self.records = list[Record]
        self.db = db

    def select(self, query: str) -> list[Record]:
        if self.db is not None:
            cursor = self.db.cursor(prepared=True)
            cursor.execute(query);
            self.records = [Record(cursor.column_names, record) for record in cursor.fetchall()]
            return self.records
        else:
            raise ConnectionError
