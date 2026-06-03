# src/streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import json

API_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="MatrixCurator", layout="wide")

st.title("MatrixCurator")

# Sidebar for configuration
st.sidebar.header("Configuration")
model_provider = st.sidebar.selectbox(
    "Model Provider",
    ["gemini/gemini-1.5-pro", "gemini/gemini-1.5-flash", "openai/gpt-4o", "anthropic/claude-3-5-sonnet-20240620"]
)

# Main area
col1, col2 = st.columns(2)

with col1:
    st.header("1. Upload Document")
    doc_file = st.file_uploader("Upload PDF, DOCX, or TXT", type=["pdf", "docx", "txt"])
    
    if doc_file and st.button("Parse Document"):
        with st.spinner("Parsing..."):
            files = {"file": (doc_file.name, doc_file.getvalue(), doc_file.type)}
            response = requests.post(f"{API_URL}/document/parse", files=files)
            if response.status_code == 200:
                st.session_state.parsed_context = response.json()["text"]
                st.success("Document parsed successfully!")
            else:
                st.error(f"Error parsing document: {response.text}")

with col2:
    st.header("2. Upload NEXUS")
    nex_file = st.file_uploader("Upload NEXUS file", type=["nex", "nexus"])
    if nex_file:
        st.session_state.original_nexus = nex_file.getvalue().decode("utf-8")
        st.success("NEXUS file loaded.")

if "parsed_context" in st.session_state and "original_nexus" in st.session_state:
    st.header("3. Extract Characters")
    char_indices_str = st.text_input("Character Indices (comma-separated)", "1, 2, 3")
    
    if st.button("Extract"):
        indices = [int(x.strip()) for x in char_indices_str.split(",") if x.strip().isdigit()]
        if not indices:
            st.warning("Please enter valid character indices.")
        else:
            with st.spinner("Extracting..."):
                payload = {
                    "context": st.session_state.parsed_context,
                    "character_indices": indices,
                    "model_provider": model_provider
                }
                response = requests.post(f"{API_URL}/agent/extract", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.extracted_states = data["extracted_states"]
                    if data.get("errors"):
                        for err in data["errors"]:
                            st.warning(err)
                    st.success("Extraction complete!")
                else:
                    st.error(f"Error extracting data: {response.text}")

if "extracted_states" in st.session_state and st.session_state.extracted_states:
    st.header("4. Review & Edit")
    
    # Convert to DataFrame for editing
    df_data = []
    for state in st.session_state.extracted_states:
        df_data.append({
            "character_index": state.get("character_index"),
            "character_name": state.get("character_name"),
            "states": json.dumps(state.get("states", {}))
        })
    
    df = pd.DataFrame(df_data)
    edited_df = st.data_editor(df, num_rows="dynamic")
    
    if st.button("Generate Updated NEXUS"):
        with st.spinner("Generating..."):
            # Convert back to list of dicts
            final_states = []
            for _, row in edited_df.iterrows():
                try:
                    states_dict = json.loads(row["states"])
                except:
                    states_dict = {}
                final_states.append({
                    "character_index": int(row["character_index"]),
                    "character_name": str(row["character_name"]),
                    "states": states_dict
                })
                
            payload = {
                "original_nexus": st.session_state.original_nexus,
                "extracted_states": final_states
            }
            
            response = requests.post(f"{API_URL}/document/nexus", json=payload)
            if response.status_code == 200:
                updated_nexus = response.json()["updated_nexus"]
                st.download_button(
                    label="Download Updated NEXUS",
                    data=updated_nexus,
                    file_name="updated_matrix.nex",
                    mime="text/plain"
                )
                st.success("NEXUS generated successfully!")
            else:
                st.error(f"Error generating NEXUS: {response.text}")
