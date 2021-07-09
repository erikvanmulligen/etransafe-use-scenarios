from knowledgehub.api import KnowledgeHubAPI


def main():
    api = KnowledgeHubAPI()
    terms = api.SemanticService().lookup('inflamm', 'HPATH')
    print(terms)


if __name__ == '__main__':
    main()