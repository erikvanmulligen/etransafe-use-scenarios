from Concordance.meddra import MedDRA

meddra = MedDRA(username='root', password='crosby9')
print(meddra.getPt('10013908'))