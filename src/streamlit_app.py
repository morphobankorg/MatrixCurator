import streamlit as st
import os
import time
from utils import parse_page_range_string
from parser import ParserService
from llm import ExtractionEvaluationService
from nex import NexService
from config import settings

st.title("MorphoBank PBDB to NEXUS File Generator")

st.write("To begin, please provide your research article and the NEXUS file you wish to update.")

article_upload = st.file_uploader("Upload Research Article (.pdf, .docx, .txt)")

if article_upload is not None:

    article_filename, article_file_extension = os.path.splitext(article_upload.name)

    if article_file_extension == ".pdf":
        selected_parser = st.selectbox("Select Document Parsing Method",("Gemini", "llamaparse", "pyMuPDF"))

    elif article_file_extension == ".docx" or ".doc":
        selected_parser = st.selectbox("Select Document Parsing Method",("Gemini", "llamaparse", "python-docx"))

    elif article_file_extension == ".txt":
        selected_parser = st.selectbox("Select Document Parsing Method",("plain-txt"))

apt_col1, apt_col2 = st.columns(2)

with apt_col1:
    total_characters = st.number_input(
        "Total Number of Morphological Characters", 
        step=1)
    
with apt_col2:
    target_pages = ""
    if article_upload:
        # Show the input unless the file is a ".docx" AND the parser is "Gemini"
        if not (article_file_extension == ".docx" and selected_parser == "Gemini"):
            target_pages = st.text_input(
                "Specify Page Range(s) for Character States (e.g., 3-4, 7)", 
                placeholder="3-4")
    
zero_indexed = st.checkbox("Character numbering in article is zero-indexed (starts from 0)")

llm_col1, llm_col2 = st.columns(2)
with llm_col1:
    extraction_model = st.selectbox(
        "Select Model for Character Extraction",
        settings.model_names,
        index=settings.default_extraction_idx,
        key="extraction_model"
    )

with llm_col2:
    evaluation_model = st.selectbox(
        "Select Model for Evaluation",
        settings.model_names,
        index=settings.default_evaluation_idx,
        key="evaluation_model"
    )

nexus_upload = st.file_uploader("Upload NEXUS File to Update (.nex)", type="nex")
if nexus_upload is not None:
    nexus_filename, nexus_file_extension = os.path.splitext(nexus_upload.name)

character_state_view = st.empty()

# After model selection dropdowns
extraction_model_id = settings.MODELS[extraction_model]  # Convert to API ID
evaluation_model_id = settings.MODELS[evaluation_model]  # Convert to API ID

with st.sidebar:

    if st.button("Generate Updated NEXUS File"):
        start_time = time.time()

        with st.status("Processing your files... Please wait.", expanded=True) as status:

            pages = parse_page_range_string(target_pages)

            st.write("Step 1/4: Parsing article...")
            parser_service = ParserService(selected_parser)
            parsed_article = parser_service.parse(file=article_upload, pages=pages)

            st.write("Step 2/4: Initializing AI models and context cache...")
            if selected_parser == "Gemini":
                extraction_evaluation_service = ExtractionEvaluationService(
                    extraction_model=extraction_model_id, 
                    evaluation_model=evaluation_model_id,
                    total_characters=total_characters,
                    context_upload=parsed_article,
                    zero_indexed=zero_indexed
                )
            else:
                extraction_evaluation_service = ExtractionEvaluationService(
                    extraction_model=extraction_model_id, 
                    evaluation_model=evaluation_model_id,
                    total_characters=total_characters,
                    context=parsed_article,
                    zero_indexed=zero_indexed
                )

            st.write("Step 3/4: Extracting and evaluating character states...")
            progress_bar = st.progress(0)

            def update_progress(progress):
                progress_bar.progress(min(int(progress * 100), 100))

            character_states_list, failed_indexes = extraction_evaluation_service.run_cycle(progress_callback=update_progress)

            st.write("Step 4/4: Updating NEXUS file with extracted states...")
            nex_service = NexService(nexus_upload)
            updated_nexus_file = nex_service.update(character_states_list=character_states_list)

            end_time = time.time()
            total_time = str(round((end_time-start_time),1))

            if len(failed_indexes) > 0:
                # Check if there are still invalid batches
                    status.update(label="Partial success: Some characters require review before finalization.", state="complete", expanded=True)
                    character_state_view.warning(f"Action required: The following character(s) could not be automatically processed and need your review. Problematic character indices: {failed_indexes}")
            else:  
                status.update(label="Processing finished! The updated NEXUS file has been generated.", state="complete", expanded=False)

        # Create a download button

        st.info(f"Processing completed in {total_time} seconds.")
        download_button = st.download_button(
            label="Download Updated NEXUS File",
            data=updated_nexus_file,
            file_name=nexus_filename + "_KEY" + ".nex",
        )