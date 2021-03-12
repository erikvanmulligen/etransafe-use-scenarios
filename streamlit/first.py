import streamlit as st

# Add a selectbox to the sidebar:
add_selectbox = st.sidebar.selectbox(
    'How would you like to be contacted?',
    ('Email', 'Home phone', 'Mobile phone')
)

# Add a slider to the sidebar:
add_slider = st.sidebar.slider(
    'Select a range of values',
    0.0, 100.0, (25.0, 75.0)
)

# Add a slider to the sidebar:
add_slider2 = st.sidebar.slider(
    'Select a range of values2',
    0.0, 100.0, (25.0, 75.0)
)

st.selectbox('Select', [1,2,3])

text_field = st.text('Fixed width text')

text_field2 = st.text('Fixed width text2')