import Concordance3.concordance_utils as conutils
import mysql.connector

db = mysql.connector.connect(host='localhost', database='concordance-30082022', user='root', password='crosby9')
findings = conutils.getAllDrugPreclinicalFindings(db, 'GDLIGKIOYRNHDA')
print(findings)