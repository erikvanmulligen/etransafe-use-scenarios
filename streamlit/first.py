import streamlit as st
from state import provide_state
import sys
sys.path.insert(1, '../kh')
from api import KnowledgeHubAPI


@provide_state
def main(state):
    api = KnowledgeHubAPI()
    state.inputs = state.inputs or set()

    input_string = st.text_input("Give inputs")
    state.inputs.add(input_string)
    terms = api.SemanticService().lookup(input_string, "HPATH")
    state.inputs.clear()
    for term in terms:
        state.inputs.add(term)

    st.selectbox("Select Dynamic", options=list(state.inputs))


main()