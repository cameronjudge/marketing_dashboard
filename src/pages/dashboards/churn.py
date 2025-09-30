import streamlit as st


def churn_page() -> None:
    st.title('Churn')
    st.info('Churn metrics coming soon.')
    st.selectbox('Churn', ['Churn', 'Churn Rate'])


    st.multiselect('Churn', ['Churn', 'Churn Rate'])



    # filter types examples