'''
This program computes the concordance table per organ
'''

import sys
from settings import settings
import mysql.connector
from classes.table import Table


def main():
    db = mysql.connector.connect(host=settings['db']['host'],
                                 database=settings['db']['database'],
                                 username=settings['db']['user'],
                                 password=settings['db']['password'])

    drugs_table = Table(db)
    drugs = drugs_table.select('select nr_inchi_keys, names, inchi_group, inchi_keys from drugs')
    for drug in drugs:
        print(drug)
    pass


if __name__ == "__main__":
    main()