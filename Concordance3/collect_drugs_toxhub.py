'''
This program accesses the toxhub using the toxhub library in order to get the compounds that match between preclinical and clinical
'''
from toxhub.dataclass import DataClass
from toxhub.datasource import DataSources
from toxhub.primitiveadaptor import PrimitiveAdaptor
from toxhub.query import QueryBuilder, Fields, ComparisonOperator
from toxhub.toxhub import ToxHub


def main():
    toxhub = ToxHub('tester', 'tester', 'dev', '3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

    pass
if __name__ == "__main__":
    main()