import streamlit as st
import requests
import base64
import os
from requests.auth import HTTPBasicAuth

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'password' not in st.session_state:
    st.session_state['password'] = ""

def login_form():
    """Display login form as a popup"""
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            response = requests.get('http://localhost:8000/users/me', auth=(username, password))
            if response.status_code == 200:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['password'] = password
                st.success(f'Logged in successfully as {username}')
            else:
                st.error('Login failed')
        except requests.exceptions.RequestException as e:
            st.error(f"Error: {e}")

if not st.session_state['logged_in']:
    login_form()
else:
    # Move the welcome message and logout button to the sidebar
    with st.sidebar.expander("User", expanded=True):
        st.header(f'Welcome {st.session_state["username"]}')
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ""
            st.success('Logged out successfully')

    

    with st.sidebar.expander("Upload Documents", expanded=True):
        knowledge_base = st.selectbox('Select Knowledge Base', ['Healthcare', 'Math'])
        uploaded_files = st.file_uploader("Choose a file", accept_multiple_files=True)
        
        if st.button('Upload'):
            for uploaded_file in uploaded_files:
                print(f"Trying to upload {uploaded_file}")
                file_bytes = uploaded_file.getvalue()
                print("")
                #print(type(file_bytes))
                auth = HTTPBasicAuth(st.session_state['username'], st.session_state['password'])

                files = {'file': (uploaded_file.name, file_bytes)}
                params = {'knowledge_base': knowledge_base}
                response = requests.post('http://localhost:8000/uploadfiles/', auth=auth, files=files, params=params)
                if response.status_code == 200:
                    st.success(f'File {uploaded_file.name} uploaded successfully')
                else:
                    st.error(f'Failed to upload file {uploaded_file.name}')

    with st.sidebar.expander("Document Viewer", expanded=False):
        # Get the path of the selected knowledge base
        kb_path = os.path.join("./data/temp/", knowledge_base)
        
        # Get the list of pdf files in the selected knowledge base
        pdf_files = [f for f in os.listdir(kb_path) if f.endswith('.pdf')]
        
        selected_pdf = st.selectbox('Select a PDF file', pdf_files)

        if st.button('Load PDF'):
            with open(os.path.join(kb_path, selected_pdf), "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
                st.session_state['pdf_display'] = pdf_display

        st.session_state['display_pdf'] = st.checkbox('Display PDF')

    if 'pdf_display' in st.session_state and st.session_state.get('display_pdf', False):
        st.markdown(st.session_state['pdf_display'], unsafe_allow_html=True)
                
    #Display the PDF in the main body if 'display_pdf' is True
    # if 'pdf_display' in st.session_state and st.session_state.get('display_pdf', False):
    #     st.markdown(st.session_state['pdf_display'], unsafe_allow_html=True)

    st.header('Search')
    search_type = st.selectbox('Select search type', ['semantic', 'lexical', 'hybrid'])
    query = st.text_input("Enter your query")
    if st.button('Search'):
        response = requests.get(f'http://localhost:8000/search?query={query}&type={search_type}&kb={knowledge_base}', auth=(st.session_state['username'], st.session_state['password']))

        if response.status_code == 200:
            results = response.json()
            iter = 0
            for match in results['matches']:
                score = round(match['score'], 2)

                if search_type == 'lexical' and (match['score_reranked'] is None or match['score_reranked']  <= 0):
                    continue
                    
                if score >= 0.5:
                    source = os.path.basename(match['metadata']['source'])
                    st.markdown(f"""
                    <div style='display: flex; flex-direction: column; justify-content: space-between; border: 1px solid blue; padding: 10px; margin: 10px 0; border-radius: 5px; background-color: #f0f0f0;'>
                        <div style='display: flex; justify-content: space-between; font-size: small;'>
                            <h3 style='text-align: left; color: SteelBlue; font-size: small;'>Source: <span style='font-weight: bold;'>{source}</span></h3>
                            <h3 style='text-align: center; color: SteelBlue; font-size: small;'>Chunk Num: <span style='font-weight: bold;'>{int(match['metadata']['chunk_num'])}</span></h3>
                            <h3 style='text-align: right; color: SteelBlue; font-size: small;'>Score: <span style='font-weight: bold;'>{score}</span></h3>
                        </div>
                        <p style='background-color: #f0f0f0; padding: 10px; border-radius: 5px;'>{match['metadata']['chunk_text']}</p>
                        <div style='display: flex; justify-content: right; font-size: small;'>
                            <h3 style='text-align: right; color: SteelBlue; font-size: small;'><span style='font-weight: bold;'>{iter+1}</span></h3>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    iter+=1
                else:
                    pass
        else:
            st.error('Search failed')

