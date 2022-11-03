from Concordance.meddra import MedDRA

meddra = MedDRA(username='root', password='crosby9')
record = meddra.getHltName('10000032')
print(record)