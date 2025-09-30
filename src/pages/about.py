import streamlit as st


def about_page() -> None:
    st.title('About')
    st.write('This is the About page.')
    
    st.subheader('Metric Definitions')
    # link to google doc
    st.write('https://docs.google.com/spreadsheets/d/1GXRbXjlpIa9r3z85wr_sUmue_V9-7XSzjiFb_opYOvk/edit?gid=730103567#gid=730103567')



    # growth target
    # st.subheader('Growth Target')
    # st.write(load_growth_target())



