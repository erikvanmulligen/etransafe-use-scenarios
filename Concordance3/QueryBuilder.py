class QueryBuilder(object):
    __db__ = None

    def __init__(self, db):
        self.__db__ = db

    def query(self, sql):
        cursor = self.__db__.cursor()
        cursor.execute(f'select * from mappings where clinicalFindingCode = {pt}')
        result = Result()
        for r in cursor.fetchall():
            record = {}
            c = 0
            for value in r:
                record[cursor.column_names[c]] = value
                c += 1
            result.append(record)
        return result

class Result(object):
    __records__ = []

    def __init__(self):
        pass

    def append(self, record):
        self.__records__.append(record)

    def select(self, attributes):
        result = Result()
        for record in self.__records__:
            new_record = {}
            for attribute in attributes:
                new_record[attribute] = record[attribute]
            result.append(new_record)
        return result


