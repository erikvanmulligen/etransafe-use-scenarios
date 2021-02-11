from rdkit import Chem


def main():
    print('hello')
    m = Chem.MolFromSmiles('Cc1ccccc1')
    print(str(m))


if __name__ == "__main__":
    main()
