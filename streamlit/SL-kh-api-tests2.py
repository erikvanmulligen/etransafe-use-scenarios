from knowledgehub.api import KnowledgeHubAPI
# import ipywidgets as w
# from IPython.display import display, Javascript
# from ipypublish import nb_setup
import numpy as np
import numpy.ma as ma
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from streamlit import SessionState

print("libs loaded")

@st.cache
def get_similars(compoundSmile, nr_results):
    print("searching similars")
    similar_compounds = api.SimilarityService().get(compoundSmile, nr_results = nr_results)

    if similar_compounds != None:
        if ('search_results' in similar_compounds) and (len(similar_compounds['search_results']) == 1):
            search_result = similar_compounds['search_results'][0]
            if 'obj_nam' in search_result:
                for i in range(len(search_result['obj_nam'])):
                    names.append(search_result['obj_nam'][i])
                    smiles.append(search_result['SMILES'][i])
                    similarities.append("{:.4f}".format(search_result['distances'][i]))

                for cmp in search_result['obj_nam']:
                    concept = api.SemanticService().normalize(cmp, ['RxNorm'])
                    if 'concepts' in concept and len(concept['concepts']) == 1:
                        compoundIds.append(concept['concepts'][0]['conceptCode'])
                        compoundNames.append(concept['concepts'][0]['conceptName'])
                df = pd.DataFrame(np.random.rand(len(names),3),columns=['NAME','SMILES','SIMILARITY'])
        df.NAME = names
        df.SMILES = smiles
        df.SIMILARITY = similarities
        df.round(3)
        return df, compoundIds, compoundNames

@st.cache
def get_studies(compoundIds, compoundNames):
    return {
        'Medline': api.Medline().getStudiesByCompoundIds(compoundIds),
        'FAERS': api.Faers().getStudiesByCompoundIds(compoundIds),
        'ClinicalTrials': api.ClinicalTrials().getStudiesByCompoundIds(compoundIds),
        'eTOXSys': api.eToxSys().getStudiesByCompoundNames(compoundNames)
    }

st.set_page_config(page_title="eTRANSAFE heatmap" , page_icon=None, layout='centered', initial_sidebar_state='auto')
st.markdown(
    f"""
<style>
    .stButton>button {{
        color: #4F8BF9;
        border-radius: 5%;
        height: 3em;
        width: 20em;
        margin-top: {32}px;
        }}
    .reportview-container .main .block-container{{
        max-width: {1200}px;
        padding-top: {0}rem;
        padding-right: {0}rem;
        padding-left: {0}rem;
        padding-bottom: {0}rem;
    }}
    .reportview-container .main {{
        color: green;
        background-color: white;
    }}
</style>
""", unsafe_allow_html=True,
)
st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True) #this makes all radio buttons on the page horizontally
st.set_option('deprecation.showPyplotGlobalUse', False) #TODO: this is just a work-around!

st.title("eTRANSAFE  heatmap workflow")
with st.beta_expander("Click here for explanations"):
    st.markdown("""
                under construction!
                ...
                """, unsafe_allow_html=True)

session_state = SessionState.get(compoundName="Omeprazole", compoundSmile="", similar_compounds="",
                                 compoundIds=[], compoundNames=[], studies={}, df_sim=[])

api = KnowledgeHubAPI()
compoundSmile = ''
############1. Translate compound to SMILES using semantic services
compoundName = st.text_input("compound name: (e.g. Omeprazole)", value=session_state.compoundName)
session_state.compoundName = compoundName
if st.button('Retrieve') and len(compoundName)>0:
    compound = api.SemanticService().normalize(compoundName, ['RxNorm','smiles'])
    if 'concepts' in compound:
        for concept in compound['concepts']:
            if 'vocabularyId' in concept:
                if concept['vocabularyId'] == 'smiles':
                    # global compoundSmile
                    compoundSmile = concept['conceptCode']
                    st.text(f'Found SMILES {compoundSmile} for {compoundName}')
                    session_state.compoundSmile = compoundSmile
                    session_state.similar_compounds=[]
                    session_state.compoundIds=[]
                    session_state.compoundNames=[]
                    session_state.studies= {}
                    session_state.df_sim=[]

########2. Retrieve similar compounds

compoundIds = []
compoundNames = []
names = []
smiles = []
similarities = []
c1, c2 = st.beta_columns([3,1])
compoundSmile = c1.text_input("Enter SMILES:", value=session_state.compoundSmile)

nr_results = c2.number_input("number of results", min_value=1, max_value=500, value=20)
df = []
if st.button("Retrieve similar compounds") and len(compoundSmile) > 0:
    res = get_similars(compoundSmile, nr_results)
    if res is None:
        st.text('something wrong in the result object from the similarity service')
    else:
        df_sim, compoundIds, compoundNames = res

        session_state.compoundIds = compoundIds
        session_state.compoundNames = compoundNames
        session_state.df_sim = df_sim
if len(session_state.df_sim) > 0:
    st.dataframe(data=session_state.df_sim, width=None, height=None)
compoundIds = session_state.compoundIds
compoundNames = session_state.compoundNames
print("compoundIds:",compoundIds)
print("\ncompoundNames:",compoundNames)
##############3.Retrieve data from the preclinical and clinical databases
if st.button("Retrieve data from DBs"):
    session_state.studies = get_studies(compoundIds, compoundNames)

studies = session_state.studies
if len(studies)>0:
    count = 0
    for source in studies:
        st.text(f"{len(studies[source])} in {source}")
        count += len(studies[source])
    st.text(f'Found {count} studies in total.')


########4. Aggregate the data per system organ class

if st.button("Aggregate and plot"):
    system = {}
    all_compounds = [c.lower() for c in compoundNames]
    socs = {}
    socs_labels = []

    # retrieve all system organ classes used
    for source in studies:
        for study in studies[source]:
            if study['FINDING']['finding'] != None and study['FINDING']['finding'] != 'No abnormalities detected' and len(study['FINDING']['finding']) > 0:
                specimenOrgans = api.SemanticService().getSocs(study['FINDING']['specimenOrgan'])
                for specimenOrgan in specimenOrgans:
                    if len(specimenOrgan) > 0:
                        if specimenOrgan not in socs:
                            socs[specimenOrgan] = 0
                            socs_labels.append(specimenOrgan)

    # travers the studies and count distinct findings per system organ class
    for source in studies:
        # initialize for each source again a data structure to capture per combination of a system organ class
        # and a compound what findings have been found
        findings_rows_cols = [[[] for compound in all_compounds] for soc in socs_labels]

        for study in studies[source]:
            if study['FINDING']['finding'] != None and study['FINDING']['finding'] != 'No abnormalities detected' and len(study['FINDING']['finding']) > 0:
                specimenOrgans = api.SemanticService().getSocs(study['FINDING']['specimenOrgan'])
                for specimenOrgan in specimenOrgans:
                    if len(specimenOrgan) > 0:
                        compound = study['COMPOUND']['name'].lower()
                        row = socs_labels.index(specimenOrgan)
                        col = all_compounds.index(compound)
                        finding = study['FINDING']['finding']
                        if finding not in findings_rows_cols[row][col]:
                            socs[specimenOrgan] += 1
                            findings_rows_cols[row][col].append(finding)

    # sort the socs per count
    all_socs = {k: v for k, v in sorted(socs.items(), key=lambda item: item[1], reverse=True)}

    # traverse all studies and create a matrix per source
    for source in studies:
        system[source] = {
            'data':np.zeros((len(all_socs),len(all_compounds)), dtype=int).tolist(),
            'rows':list(all_socs.keys()),
            'cols':all_compounds
        }

        # initialize for each source again a data structure to capture per combination of a system organ class
        # and a compound what findings have been found
        findings_rows_cols = [[[] for compound in all_compounds] for soc in socs_labels]

        for study in studies[source]:
            if study['FINDING']['finding'] != None and study['FINDING']['finding'] != 'No abnormalities detected' and len(study['FINDING']['finding']) > 0:
                specimenOrgans = api.SemanticService().getSocs(study['FINDING']['specimenOrgan'])
                for specimenOrgan in specimenOrgans:
                    if len(specimenOrgan) > 0:
                        row = system[source]['rows'].index(specimenOrgan)
                        col = system[source]['cols'].index(study['COMPOUND']['name'].lower())
                        finding = study['FINDING']['finding']
                        if finding not in findings_rows_cols[row][col]:
                            system[source]['data'][row][col] += 1
                            findings_rows_cols[row][col].append(finding)

    i = 1
    for source,value in system.items():
        plt.figure(figsize=(12,9))
        data = system[source]['data']

        # create mask
        data_mask = ma.array(np.zeros((len(all_socs.keys()), len(all_compounds))))
        for r in range(0, len(all_socs.keys())):
            for c in range(0, len(all_compounds)):
                data_mask[r][c] = 1 if data[r][c] == 0 else 0

        colormap = sns.cubehelix_palette(as_cmap=True, light=.9)
        ax = sns.heatmap(data, mask=data_mask, xticklabels=all_compounds, yticklabels=list(all_socs.keys()), annot=True, fmt=".0f", cmap=colormap)
        ax.set_xticklabels(ax.get_xmajorticklabels(), rotation=45)
        plt.title(source, fontsize = 14)
        plt.ylabel("Findings per organ class", fontsize = 12)
        plt.xlabel("Similar compounds", fontsize = 12)
        st.pyplot()

        i += 1
        print('')
        print('')

