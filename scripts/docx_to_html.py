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

def generate_html(document_html, comments_dict):
    comments_html = []
    for c_id, comment in comments_dict.items():
        date_str = comment['date'][:10] if comment['date'] else ''
        comments_html.append(f'''
        <div class="docx-comment-card" id="comment-{c_id}">
            <div class="docx-comment-header">
                <span class="docx-comment-author">{comment['author']}</span>
                <span class="docx-comment-date">{date_str}</span>
            </div>
            <div class="docx-comment-body">
                {comment['text']}
            </div>
        </div>
        ''')
        
    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Document</title>
    <style>
        :root {{
            --bg-color: #ffffff;
            --text-color: #333333;
            --sidebar-bg: #f9f9f9;
            --card-bg: #ffffff;
            --card-border: #e0e0e0;
            --highlight-bg: rgba(255, 213, 0, 0.4);
            --highlight-active: rgba(255, 213, 0, 0.8);
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-color: #121212;
                --text-color: #e0e0e0;
                --sidebar-bg: #1e1e1e;
                --card-bg: #2d2d2d;
                --card-border: #444444;
                --highlight-bg: rgba(255, 213, 0, 0.3);
                --highlight-active: rgba(255, 213, 0, 0.6);
            }}
        }}

        body {{
            margin: 0;
            padding: 0;
            font-family: var(--font-family);
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
        }}

        .docx-container {{
            display: flex;
            max-width: 1200px;
            margin: 0 auto;
            height: 100vh;
            overflow: hidden;
        }}

        .docx-document {{
            flex: 2;
            padding: 2rem 4rem;
            overflow-y: auto;
            font-size: 1.1rem;
        }}
        
        .docx-document p {{
            margin-bottom: 1.2rem;
            text-align: justify;
        }}

        .docx-sidebar {{
            flex: 1;
            background-color: var(--sidebar-bg);
            padding: 2rem;
            overflow-y: auto;
            border-left: 1px solid var(--card-border);
        }}

        .docx-highlight {{
            background-color: var(--highlight-bg);
            border-bottom: 2px solid #ffd500;
            cursor: pointer;
            transition: background-color 0.2s ease;
            padding: 0 2px;
            border-radius: 2px;
        }}

        .docx-highlight:hover, .docx-highlight.active {{
            background-color: var(--highlight-active);
        }}

        .docx-comment-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
            opacity: 0.7;
        }}

        .docx-comment-card.active {{
            opacity: 1;
            border-color: #ffd500;
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
            transform: scale(1.02);
        }}

        .docx-comment-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            color: #888;
        }}

        .docx-comment-author {{
            font-weight: 600;
            color: var(--text-color);
        }}

        .docx-comment-body {{
            font-size: 0.95rem;
        }}
        
        /* Mobile responsive */
        @media (max-width: 768px) {{
            .docx-container {{
                flex-direction: column;
                height: auto;
                overflow: visible;
            }}
            .docx-document {{
                padding: 1rem;
            }}
            .docx-sidebar {{
                border-left: none;
                border-top: 1px solid var(--card-border);
            }}
        }}
    </style>
</head>
<body>

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

            function activateComment(commentId) {{
                // Remove active class from all
                highlights.forEach(h => h.classList.remove('active'));
                cards.forEach(c => c.classList.remove('active'));

                // Add active to targeted
                const targetHighlights = document.querySelectorAll(`.docx-highlight[data-comment-id="${{commentId}}"]`);
                const targetCard = document.getElementById(`comment-${{commentId}}`);

                targetHighlights.forEach(h => h.classList.add('active'));
                if (targetCard) {{
                    targetCard.classList.add('active');
                    targetCard.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
                }}
            }}

            highlights.forEach(highlight => {{
                highlight.addEventListener('mouseenter', () => {{
                    const cId = highlight.getAttribute('data-comment-id');
                    activateComment(cId);
                }});
                
                // Add click for mobile users
                highlight.addEventListener('click', () => {{
                    const cId = highlight.getAttribute('data-comment-id');
                    activateComment(cId);
                }});
            }});
            
            cards.forEach(card => {{
                card.addEventListener('mouseenter', () => {{
                    const cId = card.id.replace('comment-', '');
                    activateComment(cId);
                    
                    // scroll document to the highlight
                    const docHighlight = document.querySelector(`.docx-highlight[data-comment-id="${{cId}}"]`);
                    if (docHighlight) {{
                        docHighlight.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }}
                }});
            }});
        }});
    </script>
</body>
</html>"""
    return template

def convert(input_docx, output_html):
    print(f"Converting {{input_docx}} to {{output_html}}...")
    with zipfile.ZipFile(input_docx, 'r') as docx_zip:
        comments = extract_comments(docx_zip)
        document_html = parse_document(docx_zip)
        
    final_html = generate_html(document_html, comments)
    
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    print("Successfully generated HTML!")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python docx_to_html.py <input.docx> <output.html>")
        sys.exit(1)
        
    convert(sys.argv[1], sys.argv[2])
