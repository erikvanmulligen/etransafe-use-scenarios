from knowledgehub.api import KnowledgeHubAPI
import argparse


def main():
    parser = argparse.ArgumentParser(description='Process parameters for collecting all data from eToxSys')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    args = parser.parse_args()

    api = KnowledgeHubAPI(server='TEST', client_secret='39c644b3-1f23-4d94-a71f-e0fb43ebd760')
    api.login(args.username, args.password)

    compounds = [compound for compound in api.eToxSys().getAllCompounds() if 'inchiKey' in compound]
    print(f'total compounds:{len(compounds)}')
    for compound in compounds:
        print(compound)
        break


if __name__ == "__main__":
    main()