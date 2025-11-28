# Document Database

This directory contains HTML documents and other files served by the application.

## Adding Documents

Simply place HTML, PDF, or text files in this directory and they will be automatically available through the API:

- List all documents: `GET /documents/list`
- View document directory: `GET /documents/`
- Retrieve a document: `GET /documents/{filename}`

## Supported File Types

- HTML (.html, .htm)
- PDF (.pdf)
- Text (.txt)
- Markdown (.md)
- JSON (.json)
- XML (.xml)

## Example Documents

The following sample documents are included:
- `sample1.html` - Introduction to Post-Quantum Cryptography
- `sample2.html` - OQS-OpenSSL Integration Guide

Add your own documents here to demonstrate the "server maintains a database of web pages/documents" requirement.

