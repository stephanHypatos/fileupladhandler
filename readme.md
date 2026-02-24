# Austrofix File Viewer MVP

A Streamlit application for uploading, extracting, and viewing PDFs from Austrofix files.

## Features

### Current Implementation
- **Multi-file upload**: Upload one or multiple Austrofix (.zip) files
- **Batch management**: Each upload session creates a unique batch ID
- **PDF extraction**: Automatically extracts all PDFs from Austrofix archives
- **File tracking**: Links each extracted PDF to its source Austrofix file
- **Interactive viewer**: Built-in PDF viewer with file selection
- **Download capability**: Download individual PDFs
- **Batch statistics**: Overview of batches and file counts

### Architecture
```
Austrofix File (.zip)
    └── Contains multiple PDFs (pdf5a format)
        └── Extracted and displayed individually
        └── Tracked by batch ID
        └── Linked to source file
```

## Setup

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run austrofix_viewer.py
```

3. Open your browser to `http://localhost:8501`

## Usage

1. **Upload Files**
   - Click "Browse files" or drag and drop Austrofix (.zip) files
   - You can upload single or multiple files at once

2. **Process Files**
   - Click "Process Files" button
   - A unique batch ID will be created
   - All PDFs will be extracted and displayed

3. **View PDFs**
   - Expand a batch to see its contents
   - Select a PDF from the dropdown
   - View it in the embedded PDF viewer
   - Download individual files as needed

4. **Manage Batches**
   - Delete individual batches with the delete button
   - Clear all batches from the sidebar
   - View statistics in the sidebar

## Data Structure

### Batch Object
```python
{
    'batch_id': '3f2a8b1c',  # Unique 8-character ID
    'timestamp': '2024-02-25 14:30:00',
    'austrofix_count': 2,  # Number of uploaded Austrofix files
    'pdf_count': 15,  # Total extracted PDFs
    'files': [
        {
            'name': 'document.pdf',
            'data': b'...',  # Binary PDF data
            'size': 245678,  # Size in bytes
            'source_austrofix': 'batch_001.zip'
        },
        # ... more files
    ]
}
```

## Next Steps (For Future Development)

1. **AI Agent Integration**
   - Document content analysis
   - Text extraction and OCR
   - Document classification
   - Entity recognition

2. **Enhanced Metadata**
   - Document type detection
   - Date extraction
   - Sender/recipient identification
   - Invoice number extraction

3. **Advanced Features**
   - Search across documents
   - Batch processing actions
   - Export to database
   - API integration

## Technical Notes

- PDFs are stored in session state (memory-based)
- For production, consider database storage
- Austrofix files are expected to be ZIP archives
- PDF viewer requires browser PDF support

## Troubleshooting

**PDFs not displaying?**
- Ensure your browser supports embedded PDFs
- Try downloading the PDF to view locally
- Check that the Austrofix file is a valid ZIP archive

**Upload fails?**
- Verify file is a valid ZIP file
- Check file size limits (Streamlit default: 200MB)
- Ensure PDFs inside are not corrupted
