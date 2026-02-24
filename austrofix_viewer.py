import streamlit as st
import zipfile
import io
import uuid
from pathlib import Path
from datetime import datetime
import base64

st.set_page_config(
    page_title="Austrofix File Viewer",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'batches' not in st.session_state:
    st.session_state.batches = []

def extract_pdf5a_files(uploaded_file):
    """Extract PDF files from Austrofix (ZIP) archive"""
    extracted_files = []
    
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            # List all files in the archive
            file_list = zip_ref.namelist()
            
            # Extract PDF files
            for file_name in file_list:
                if file_name.lower().endswith('.pdf'):
                    file_data = zip_ref.read(file_name)
                    extracted_files.append({
                        'name': file_name,
                        'data': file_data,
                        'size': len(file_data)
                    })
    except zipfile.BadZipFile:
        st.error(f"Error: {uploaded_file.name} is not a valid ZIP/Austrofix file")
    except Exception as e:
        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
    
    return extracted_files

def create_batch(uploaded_files):
    """Create a new batch from uploaded files"""
    batch_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    all_extracted_files = []
    
    for uploaded_file in uploaded_files:
        extracted = extract_pdf5a_files(uploaded_file)
        for file_info in extracted:
            file_info['source_austrofix'] = uploaded_file.name
        all_extracted_files.extend(extracted)
    
    batch = {
        'batch_id': batch_id,
        'timestamp': timestamp,
        'austrofix_count': len(uploaded_files),
        'pdf_count': len(all_extracted_files),
        'files': all_extracted_files
    }
    
    return batch

def display_pdf(pdf_data):
    """Display PDF using base64 encoding"""
    base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Main UI
st.title("📄 Austrofix File Viewer MVP")
st.markdown("Upload Austrofix files (.zip) to extract and view contained PDFs")

# File upload section
st.header("Upload Files")
uploaded_files = st.file_uploader(
    "Choose Austrofix file(s)",
    type=['zip'],
    accept_multiple_files=True,
    help="Upload one or more Austrofix (.zip) files containing PDFs"
)

if uploaded_files:
    if st.button("Process Files", type="primary"):
        with st.spinner("Processing Austrofix files..."):
            batch = create_batch(uploaded_files)
            st.session_state.batches.insert(0, batch)  # Add to beginning
            st.success(f"✅ Created Batch {batch['batch_id']} with {batch['pdf_count']} PDF(s) from {batch['austrofix_count']} Austrofix file(s)")
            st.rerun()

# Display batches
if st.session_state.batches:
    st.header("Processed Batches")
    
    for batch in st.session_state.batches:
        with st.expander(
            f"🗂️ Batch {batch['batch_id']} - {batch['pdf_count']} PDFs - {batch['timestamp']}",
            expanded=True
        ):
            # Batch metadata
            col1, col2, col3 = st.columns(3)
            col1.metric("Batch ID", batch['batch_id'])
            col2.metric("Austrofix Files", batch['austrofix_count'])
            col3.metric("Extracted PDFs", batch['pdf_count'])
            
            st.divider()
            
            # File list and viewer
            if batch['files']:
                # File selector
                file_names = [f"{i+1}. {f['name']} ({f['size']:,} bytes) - from {f['source_austrofix']}" 
                             for i, f in enumerate(batch['files'])]
                
                selected_file_idx = st.selectbox(
                    "Select PDF to view:",
                    range(len(file_names)),
                    format_func=lambda x: file_names[x],
                    key=f"select_{batch['batch_id']}"
                )
                
                # Display selected PDF
                if selected_file_idx is not None:
                    selected_file = batch['files'][selected_file_idx]
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.subheader(f"📄 {selected_file['name']}")
                    
                    with col2:
                        # Download button
                        st.download_button(
                            label="⬇️ Download PDF",
                            data=selected_file['data'],
                            file_name=selected_file['name'],
                            mime="application/pdf"
                        )
                    
                    # PDF viewer
                    display_pdf(selected_file['data'])
            else:
                st.info("No PDF files found in this batch")
            
            # Delete batch button
            if st.button(f"🗑️ Delete Batch", key=f"delete_{batch['batch_id']}"):
                st.session_state.batches.remove(batch)
                st.rerun()

else:
    st.info("👆 Upload Austrofix files above to get started")

# Sidebar with stats
with st.sidebar:
    st.header("📊 Statistics")
    total_batches = len(st.session_state.batches)
    total_pdfs = sum(batch['pdf_count'] for batch in st.session_state.batches)
    
    st.metric("Total Batches", total_batches)
    st.metric("Total PDFs", total_pdfs)
    
    st.divider()
    
    st.subheader("About")
    st.markdown("""
    **Austrofix File Viewer MVP**
    
    This app allows you to:
    - Upload single or multiple Austrofix files
    - Automatically extract PDFs (pdf5a format)
    - Group files by batch ID
    - View and download individual PDFs
    
    **Next Steps:**
    - AI agent for content analysis
    - Metadata extraction
    - Document classification
    """)
    
    if st.session_state.batches:
        st.divider()
        if st.button("🗑️ Clear All Batches", type="secondary"):
            st.session_state.batches = []
            st.rerun()
