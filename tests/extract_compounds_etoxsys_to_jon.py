'''
This is a module to test what data comes back from eToxSys
'''

from src.knowledgehub.api import KnowledgeHubAPI
import argparse


def main():
    parser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    args = parser.parse_args()

    api = KnowledgeHubAPI('TEST', )
    api.login(args.username, args.password)

    socs = {}

    studies = api.eToxSys().getStudiesByCompoundNames(['omeprazole'])
    f = open("../data/studies_etox.json", "w")
    f.write(str(studies))
    f.close()


if __name__ == "__main__":
    main()

