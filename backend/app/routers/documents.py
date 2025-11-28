"""
Document Serving Router
=======================

This router serves HTML documents and other files stored in the server's document database.
This demonstrates the project requirement: "server maintains a database of web pages/documents"
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
from typing import List
from pydantic import BaseModel
import os

router = APIRouter(prefix="/documents", tags=["documents"])

# Directory where documents are stored
DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "documents"

# Ensure documents directory exists
DOCUMENTS_DIR.mkdir(exist_ok=True)


class DocumentInfo(BaseModel):
    """Information about a document"""
    id: str
    filename: str
    title: str
    content_type: str
    size: int


@router.get("/list", response_model=List[DocumentInfo])
async def list_documents():
    """
    List all available documents in the database.
    
    Returns a list of document metadata (filename, title, content type, size).
    """
    documents = []
    
    if not DOCUMENTS_DIR.exists():
        return documents
    
    # Scan documents directory for HTML and other files
    for file_path in DOCUMENTS_DIR.iterdir():
        if file_path.is_file():
            # Extract metadata
            filename = file_path.name
            file_ext = file_path.suffix.lower()
            
            # Determine content type
            content_types = {
                '.html': 'text/html',
                '.htm': 'text/html',
                '.pdf': 'application/pdf',
                '.txt': 'text/plain',
                '.md': 'text/markdown',
                '.json': 'application/json',
                '.xml': 'application/xml'
            }
            content_type = content_types.get(file_ext, 'application/octet-stream')
            
            # Get file size
            size = file_path.stat().st_size
            
            # Extract title from filename or read from HTML
            title = filename
            if file_ext == '.html':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Try to extract title from <title> tag
                        if '<title>' in content:
                            start = content.find('<title>') + 7
                            end = content.find('</title>', start)
                            if end > start:
                                title = content[start:end].strip()
                except:
                    pass
            
            documents.append(DocumentInfo(
                id=filename,
                filename=filename,
                title=title,
                content_type=content_type,
                size=size
            ))
    
    # Sort by filename
    documents.sort(key=lambda x: x.filename)
    return documents


@router.get("/{document_id}")
async def get_document(document_id: str):
    """
    Retrieve a specific document by ID (filename).
    
    Args:
        document_id: The filename of the document to retrieve
    
    Returns:
        The document file (HTML, PDF, etc.)
    
    Raises:
        404: If document not found
    """
    # Security: Prevent directory traversal
    if '..' in document_id or '/' in document_id or '\\' in document_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    file_path = DOCUMENTS_DIR / document_id
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found"
        )
    
    # Determine media type from extension
    ext = file_path.suffix.lower()
    media_types = {
        '.html': 'text/html',
        '.htm': 'text/html',
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.json': 'application/json',
        '.xml': 'application/xml'
    }
    media_type = media_types.get(ext, 'application/octet-stream')
    
    # For HTML files, return as HTMLResponse for proper rendering
    if ext in ['.html', '.htm']:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content=content)
    
    # For other files, return as FileResponse
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=document_id
    )


@router.get("/")
async def documents_root():
    """
    Get a list of available documents as HTML.
    Useful for browsing documents in a browser.
    """
    documents = await list_documents()
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Database</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4a7cff;
            padding-bottom: 10px;
        }
        .doc-list {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
            margin-top: 20px;
        }
        .doc-item {
            padding: 15px;
            border-bottom: 1px solid #eee;
            transition: background 0.2s;
        }
        .doc-item:hover {
            background: #f9f9f9;
        }
        .doc-item:last-child {
            border-bottom: none;
        }
        .doc-item a {
            text-decoration: none;
            color: #4a7cff;
            font-weight: 600;
            font-size: 18px;
        }
        .doc-item a:hover {
            text-decoration: underline;
        }
        .doc-meta {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }
        .empty {
            text-align: center;
            color: #999;
            padding: 40px;
        }
    </style>
</head>
<body>
    <h1>📄 Document Database</h1>
    <div class="doc-list">
"""
    
    if not documents:
        html += '<div class="empty">No documents available. Add HTML files to the <code>backend/documents</code> directory.</div>'
    else:
        for doc in documents:
            size_kb = doc.size / 1024
            html += f"""
        <div class="doc-item">
            <a href="/documents/{doc.filename}">{doc.title}</a>
            <div class="doc-meta">
                {doc.content_type} • {size_kb:.1f} KB
            </div>
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    return HTMLResponse(content=html)

