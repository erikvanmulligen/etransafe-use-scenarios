from kh.api import KnowledgeHubAPI


def main():
    api = KnowledgeHubAPI()
    terms = api.SemanticService().lookup('hyper', ['HPATH','MEDDRA'])
    print(terms)


if __name__ == '__main__':
    main()