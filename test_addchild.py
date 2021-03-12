import pysolr

def main():
    solr = pysolr.Solr('http://localhost:30000/solr/entities', always_commit=True)

    solr.delete('*:*')
    solr.commit()

    document = {
        'id': '1',
        'type': 'organization',
        'active': True,
        'name' : 'document 1',
        'source' : 'kvk'
    }

    childDocs = []
    childDocs.append({
        'id': 'text_' + document['id'],
        'entity': document['id'],
        'active': True,
        'type': 'kvk-description',
        'source' : 'kvk'
    })

    document['_doc'] = childDocs
    solr.add([document]);
    solr.commit()

    results = solr.search('id:1', **{'fl': '*, [child parentFilter=type:organization]', 'start': 0, 'rows': 10})
    for r in results:
        print("#1 number of childDocs: " + str(len(r['_childDocuments_'])))
        r['_childDocuments_'].append({
            'id': 'text_2',
            'entity': document['id'],
            'active': True,
            'type': 'kvk-description',
            'source' : 'kvk'
        })
        solr.add(r)
    solr.commit()

    results = solr.search('id:1', **{'fl': '*, [child parentFilter=type:organization]', 'start': 0, 'rows': 10})
    for r in results:
        print("#2 number of childDocs: " + str(len(r['_childDocuments_'])))

if __name__ == "__main__":
    main()