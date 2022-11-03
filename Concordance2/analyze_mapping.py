"""
    This program aims at analyzing the mapping of a particular finding
"""
import sys

import mysql.connector
from Concordance2.Compound import Compound
from knowledgehub.api import KnowledgeHubAPI

inchi_group = 'GDLIGKIOYRNHDA'
finding_code = '10073720'

api = KnowledgeHubAPI(server='TEST', client_secret='39c644b3-1f23-4d94-a71f-e0fb43ebd760')
status = api.login('erik.mulligen', 'Crosby99!')
if not status:
    print('not logged in')
    sys.exit(1)

for compound in api.Medline().getAllCompounds2(maximum=10):
    print(compound)

# db = mysql.connector.connect(host='localhost', database='concordance-medline', user='root', password='crosby9')
# compound = Compound(database=db)
# compound.get_by_inchi_group(inchi_group)
# print(compound.inchi_key())