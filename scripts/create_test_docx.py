import zipfile
import os

def create_docx(filename):
    print(f"Creating {filename}...")
    
    # We will build a minimal valid docx file from scratch
    # that contains a few paragraphs and two comments.

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
</Types>
"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
</Relationships>
"""

    document = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <w:body>
        <w:p>
            <w:r><w:t>This is a test document to verify the docx parser.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>Here is a sentence with a </w:t></w:r>
            <w:commentRangeStart w:id="0"/>
            <w:r><w:t>highlighted section</w:t></w:r>
            <w:commentRangeEnd w:id="0"/>
            <w:r><w:commentReference w:id="0"/></w:r>
            <w:r><w:t> that has a comment attached to it.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>This is a completely normal paragraph.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>Another sentence, but this time with </w:t></w:r>
            <w:r><w:rPr><w:b/></w:rPr><w:t>bold text</w:t></w:r>
            <w:r><w:t>! And </w:t></w:r>
            <w:commentRangeStart w:id="1"/>
            <w:r><w:t>another comment right here</w:t></w:r>
            <w:commentRangeEnd w:id="1"/>
            <w:r><w:commentReference w:id="1"/></w:r>
            <w:r><w:t>.</w:t></w:r>
        </w:p>
        <w:sectPr/>
    </w:body>
</w:document>
"""

    comments = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:comment w:id="0" w:author="Summit Sarkar" w:date="2026-03-15T10:00:00Z" w:initials="SS">
        <w:p>
            <w:r><w:t>This is the text for the first comment. It provides some useful context.</w:t></w:r>
        </w:p>
    </w:comment>
    <w:comment w:id="1" w:author="Gerwin Kiessling" w:date="2026-03-15T11:00:00Z" w:initials="GK">
        <w:p>
            <w:r><w:t>Excellent point! This is the second comment.</w:t></w:r>
        </w:p>
    </w:comment>
</w:comments>
"""

    with zipfile.ZipFile(filename, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', rels)
        zf.writestr('word/_rels/document.xml.rels', doc_rels)
        zf.writestr('word/document.xml', document)
        zf.writestr('word/comments.xml', comments)
        
    print("Done!")

if __name__ == "__main__":
    create_docx("scripts/test_doc.docx")
