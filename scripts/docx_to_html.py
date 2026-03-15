import zipfile
import xml.etree.ElementTree as ET
import sys
import os

NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
}

def extract_comments(docx_zip):
    try:
        comments_xml = docx_zip.read('word/comments.xml')
    except KeyError:
        return {}

    root = ET.fromstring(comments_xml)
    comments = {}
    
    for comment_elem in root.findall('.//w:comment', NAMESPACES):
        comment_id = comment_elem.get(f'{{{NAMESPACES["w"]}}}id')
        author = comment_elem.get(f'{{{NAMESPACES["w"]}}}author', 'Unknown')
        date = comment_elem.get(f'{{{NAMESPACES["w"]}}}date', '')
        
        # Extract text from paragraphs within the comment
        text_parts = []
        for p in comment_elem.findall('.//w:p', NAMESPACES):
            p_text = ''.join(t.text for t in p.findall('.//w:t', NAMESPACES) if t.text)
            if p_text:
                text_parts.append(p_text)
                
        comments[comment_id] = {
            'author': author,
            'date': date,
            'text': '\n'.join(text_parts)
        }
        
    return comments

def parse_document(docx_zip):
    document_xml = docx_zip.read('word/document.xml')
    root = ET.fromstring(document_xml)
    
    html_parts = []
    
    # Iterate over body elements (paragraphs, mostly)
    body = root.find('w:body', NAMESPACES)
    if body is None:
        return ""
        
    for elem in body:
        if elem.tag == f'{{{NAMESPACES["w"]}}}p':
            html_parts.append('<p>')
            
            # A paragraph can contain runs, comment starts, comment ends
            for child in elem:
                if child.tag == f'{{{NAMESPACES["w"]}}}r':
                    # Parse run (text + formatting)
                    text_nodes = child.findall('.//w:t', NAMESPACES)
                    text = ''.join(t.text for t in text_nodes if t.text)
                    if not text:
                        continue
                        
                    # basic formatting
                    rPr = child.find('w:rPr', NAMESPACES)
                    is_bold = rPr is not None and rPr.find('w:b', NAMESPACES) is not None
                    is_italic = rPr is not None and rPr.find('w:i', NAMESPACES) is not None
                    
                    if is_bold: text = f'<b>{text}</b>'
                    if is_italic: text = f'<i>{text}</i>'
                    
                    html_parts.append(text)
                    
                elif child.tag == f'{{{NAMESPACES["w"]}}}commentRangeStart':
                    c_id = child.get(f'{{{NAMESPACES["w"]}}}id')
                    html_parts.append(f'<span class="docx-highlight" data-comment-id="{c_id}">')
                    
                elif child.tag == f'{{{NAMESPACES["w"]}}}commentRangeEnd':
                    html_parts.append('</span>')
                    
            html_parts.append('</p>\n')
            
    return ''.join(html_parts)

def generate_html(title, document_html, comments_dict):
    comments_html = []
    for c_id, comment in comments_dict.items():
        date_str = comment['date'][:10] if comment['date'] else ''
        comments_html.append(f'''
        <div class="docx-comment-card" id="comment-{c_id}">
            <div class="docx-comment-header">
                <span class="docx-comment-author">{comment['author']}</span>
            </div>
            <div class="docx-comment-body">
                {comment['text']}
            </div>
        </div>
        ''')
        
    template = f"""---
title: "{title}"
type: page
layout: single
---

<style>
    .docx-container {{
        display: flex;
        flex-direction: row;
        gap: 2rem;
        margin-top: 2rem;
        align-items: flex-start;
    }}

    .docx-document {{
        flex: 2;
        font-family: inherit;
        font-size: 1.1rem;
        line-height: 1.6rem;
        text-align: justify;
    }}
    
    .docx-document p {{
        margin-bottom: 1rem;
    }}

    .docx-sidebar {{
        flex: 1;
        position: sticky;
        top: 2rem;
        max-height: 80vh;
        overflow-y: auto;
        padding-right: 1rem;
    }}

    .docx-highlight {{
        background-color: transparent;
        border-bottom: 2px solid #500bff;
        cursor: pointer;
        transition: background-color 0.2s ease;
        padding: 0 2px;
    }}

    .docx-highlight:hover, .docx-highlight.active {{
        background-color: rgba(80, 11, 255, 0.15);
    }}

    .docx-comment-card {{
        background-color: #FEFEFA;
        border: 1px solid #7c7c7c;
        border-radius: 4px;
        padding: 1rem;
        margin-bottom: 1rem;
        opacity: 0.6;
        transition: opacity 0.2s ease, border-color 0.2s ease, box-shadow 0.2s;
        cursor: pointer;
    }}

    .docx-comment-card.active {{
        opacity: 1;
        border-color: #500bff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}

    .docx-comment-header {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        font-style: italic;
        color: #7c7c7c;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 0.2rem;
    }}

    .docx-comment-author {{
        font-weight: bold;
        color: #000;
        font-style: normal;
    }}

    .docx-comment-body {{
        font-size: 0.95rem;
        line-height: 1.4rem;
        font-family: inherit;
    }}
    
    @media (max-width: 768px) {{
        .docx-container {{
            flex-direction: column;
        }}
        .docx-sidebar {{
            position: static;
            max-height: none;
            border-top: 2px solid #7c7c7c;
            padding-top: 2rem;
            margin-top: 2rem;
        }}
    }}
</style>

<div class="docx-container">
    <div class="docx-document">
        {document_html}
    </div>
    <div class="docx-sidebar">
        {''.join(comments_html)}
    </div>
</div>

<script>
    document.addEventListener('DOMContentLoaded', () => {{
        const highlights = document.querySelectorAll('.docx-highlight');
        const cards = document.querySelectorAll('.docx-comment-card');

        function toggleComment(commentId) {{
            const wasActive = document.querySelector(`.docx-highlight[data-comment-id="${{commentId}}"]`).classList.contains('active');
            
            // Remove active class from all
            highlights.forEach(h => h.classList.remove('active'));
            cards.forEach(c => c.classList.remove('active'));

            if (!wasActive) {{
                // Add active to targeted
                const targetHighlights = document.querySelectorAll(`.docx-highlight[data-comment-id="${{commentId}}"]`);
                const targetCard = document.getElementById(`comment-${{commentId}}`);

                targetHighlights.forEach(h => h.classList.add('active'));
                if (targetCard) {{
                    targetCard.classList.add('active');
                }}
            }}
        }}

        highlights.forEach(highlight => {{
            highlight.addEventListener('click', (e) => {{
                e.preventDefault();
                const cId = highlight.getAttribute('data-comment-id');
                toggleComment(cId);
            }});
        }});
        
        cards.forEach(card => {{
            card.addEventListener('click', () => {{
                const cId = card.id.replace('comment-', '');
                toggleComment(cId);
            }});
        }});
    }});
</script>
"""
    return template

def convert(title, input_docx, output_md):
    print(f"Converting {{input_docx}} to {{output_md}}...")
    with zipfile.ZipFile(input_docx, 'r') as docx_zip:
        comments = extract_comments(docx_zip)
        document_html = parse_document(docx_zip)
        
    final_html = generate_html(title, document_html, comments)
    
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    print("Successfully generated Markdown page!")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python docx_to_html.py <Title> <input.docx> <output.md>")
        sys.exit(1)
        
    convert(sys.argv[1], sys.argv[2], sys.argv[3])
