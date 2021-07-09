import pandas as pd
from rdkit.Chem import PandasTools
from rdkit import Chem
m2 = Chem.MolFromSmiles('COc1ccc2[nH]c([S+]([O-])Cc3ncc(C)c(OC)c3C)nc2c1')
print(Chem.MolToMolBlock(m2))

f = open('/Users/mulligen/downloads/omeprazole.sdf', 'w')
f.write(Chem.MolToMolBlock(m2))
f.close()