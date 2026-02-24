import streamlit as st
import io
import uuid
from pathlib import Path
from datetime import datetime
import base64
from pypdf import PdfReader

st.set_page_config(
    page_title="Austrofix File Viewer",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'batches' not in st.session_state:
    st.session_state.batches = []

def extract_pdf5a_files(uploaded_file):
    """Extract embedded files from PDF/A-5 (Austrofix) document"""
    extracted_files = []
    
    try:
        # Read the PDF
        pdf_reader = PdfReader(uploaded_file)
        
        # Check for embedded files
        if '/Names' in pdf_reader.trailer['/Root']:
            names = pdf_reader.trailer['/Root']['/Names']
            if '/EmbeddedFiles' in names:
                embedded_files = names['/EmbeddedFiles']
                
                # Navigate the name tree to find files
                if '/Names' in embedded_files:
                    names_array = embedded_files['/Names']
                    
                    # Process pairs: [filename, file_spec, filename, file_spec, ...]
                    for i in range(0, len(names_array), 2):
                        file_name = names_array[i]
                        file_spec = names_array[i + 1]
                        
                        # Get the embedded file stream
                        if '/EF' in file_spec and '/F' in file_spec['/EF']:
                            file_stream = file_spec['/EF']['/F']
                            file_data = file_stream.get_data()
                            
                            # Determine MIME type
                            mime_type = 'application/octet-stream'
                            if '/Subtype' in file_spec:
                                mime_type = str(file_spec['/Subtype']).replace('/', '')
                            
                            # Get file extension from name or MIME type
                            file_extension = Path(file_name).suffix.lower()
                            if not file_extension:
                                # Try to determine from MIME type
                                mime_map = {
                                    'text/xml': '.xml',
                                    'application/xml': '.xml',
                                    'application/pdf': '.pdf',
                                    'application/vnd.ms-excel': '.xls',
                                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx'
                                }
                                file_extension = mime_map.get(mime_type, '')
                            
                            extracted_files.append({
                                'name': file_name,
                                'data': file_data,
                                'size': len(file_data),
                                'mime_type': mime_type,
                                'extension': file_extension
                            })
                
    except Exception as e:
        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        # Try to show more details for debugging
        st.exception(e)
    
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
    "Choose Austrofix (PDF/A-5) file(s)",
    type=['pdf'],
    accept_multiple_files=True,
    help="Upload one or more PDF/A-5 (Austrofix) files containing embedded attachments"
)

if uploaded_files:
    if st.button("Process Files", type="primary"):
        with st.spinner("Processing Austrofix files..."):
            batch = create_batch(uploaded_files)
            st.session_state.batches.insert(0, batch)  # Add to beginning
            st.success(f"✅ Created Batch {batch['batch_id']} with {batch['pdf_count']} embedded file(s) from {batch['austrofix_count']} Austrofix file(s)")
            st.rerun()

# Display batches
if st.session_state.batches:
    st.header("Processed Batches")
    
    for batch in st.session_state.batches:
        with st.expander(
            f"🗂️ Batch {batch['batch_id']} - {batch['pdf_count']} Files - {batch['timestamp']}",
            expanded=True
        ):
            # Batch metadata
            col1, col2, col3 = st.columns(3)
            col1.metric("Batch ID", batch['batch_id'])
            col2.metric("Austrofix Files", batch['austrofix_count'])
            col3.metric("Embedded Files", batch['pdf_count'])
            
            st.divider()
            
            # File list and viewer
            if batch['files']:
                # Get file type icon
                def get_file_icon(extension):
                    icon_map = {
                        '.pdf': '📄',
                        '.xml': '📋',
                        '.xls': '📊',
                        '.xlsx': '📊',
                        '.txt': '📝',
                        '.csv': '📊'
                    }
                    return icon_map.get(extension.lower(), '📎')
                
                # File selector with type indicators
                file_names = [
                    f"{get_file_icon(f.get('extension', ''))} {i+1}. {f['name']} ({f['size']:,} bytes) - from {f['source_austrofix']}" 
                    for i, f in enumerate(batch['files'])
                ]
                
                selected_file_idx = st.selectbox(
                    "Select file to view:",
                    range(len(file_names)),
                    format_func=lambda x: file_names[x],
                    key=f"select_{batch['batch_id']}"
                )
                
                # Display selected file
                if selected_file_idx is not None:
                    selected_file = batch['files'][selected_file_idx]
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.subheader(f"{get_file_icon(selected_file.get('extension', ''))} {selected_file['name']}")
                        st.caption(f"Type: {selected_file.get('mime_type', 'unknown')} | Size: {selected_file['size']:,} bytes")
                    
                    with col2:
                        # Download button with appropriate MIME type
                        st.download_button(
                            label="⬇️ Download",
                            data=selected_file['data'],
                            file_name=selected_file['name'],
                            mime=selected_file.get('mime_type', 'application/octet-stream')
                        )
                    
                    # Display file content based on type
                    extension = selected_file.get('extension', '').lower()
                    
                    if extension == '.pdf':
                        # PDF viewer
                        display_pdf(selected_file['data'])
                    elif extension in ['.xml', '.txt']:
                        # Text viewer
                        try:
                            text_content = selected_file['data'].decode('utf-8')
                            st.code(text_content, language='xml' if extension == '.xml' else 'text')
                        except:
                            st.warning("Unable to decode text content. Use download button to save the file.")
                    elif extension in ['.xls', '.xlsx']:
                        # Excel preview
                        st.info("📊 Excel file detected. Download the file to view in Excel or a spreadsheet application.")
                        # Could add pandas preview here if needed
                    else:
                        st.info(f"Preview not available for {selected_file.get('mime_type', 'this file type')}. Use the download button to save the file.")
            else:
                st.info("No embedded files found in this batch")
            
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
    total_files = sum(batch['pdf_count'] for batch in st.session_state.batches)
    
    st.metric("Total Batches", total_batches)
    st.metric("Total Files", total_files)
    
    # File type breakdown
    if st.session_state.batches:
        st.divider()
        st.subheader("File Types")
        file_types = {}
        for batch in st.session_state.batches:
            for file in batch['files']:
                ext = file.get('extension', 'unknown')
                file_types[ext] = file_types.get(ext, 0) + 1
        
        for ext, count in sorted(file_types.items()):
            st.text(f"{ext or 'unknown'}: {count}")
    
    st.divider()
    
    st.subheader("About")
    st.markdown("""
    **Austrofix (PDF/A-5) File Viewer**
    
    This app allows you to:
    - Upload PDF/A-5 (Austrofix) files
    - Extract embedded attachments (XML, PDF, XLS, etc.)
    - Group files by batch ID
    - View and download individual files
    
    **Supported formats:**
    - XML (with syntax highlighting)
    - PDF (embedded viewer)
    - Excel (XLS/XLSX)
    - Plain text
    
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
