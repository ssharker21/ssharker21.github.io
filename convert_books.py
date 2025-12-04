import csv
import json
import os
from datetime import datetime

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y/%m/%d').strftime('%Y-%m-%d')
    except ValueError:
        return None

def clean_isbn(isbn_str):
    # Remove =" and " wrapper from CSV export
    if isbn_str.startswith('="') and isbn_str.endswith('"'):
        return isbn_str[2:-1]
    return isbn_str

csv_path = 'goodreads_library_export.csv'
json_path = 'data/books.json'

books = []

# Load existing covers if available
existing_covers = {}
if os.path.exists(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            existing_books = json.load(f)
            for b in existing_books:
                # Create a key based on title and author (or ISBN if unique enough, but title/author is safer for matching back)
                # Actually, let's use a composite key or just try to match by title/author
                key = (b.get('title'), b.get('author'))
                if b.get('cover_image'):
                    existing_covers[key] = b.get('cover_image')
    except Exception as e:
        print(f"Warning: Could not load existing covers: {e}")

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Filter for read books or books with a date read?
        # The user said "reverse chronological order", implying date read or added.
        # Let's include all, but sort by Date Read, then Date Added.
        
        date_read = parse_date(row.get('Date Read'))
        date_added = parse_date(row.get('Date Added'))
        
        # Only include if we have a date to sort by, or maybe just put them at the end?
        # Goodreads export usually has everything.
        
        if not date_read:
            continue

        title = row.get('Title')
        author = row.get('Author')
        
        book = {
            'title': title,
            'author': author,
            'isbn': clean_isbn(row.get('ISBN')),
            'isbn13': clean_isbn(row.get('ISBN13')),
            'my_rating': row.get('My Rating'),
            'average_rating': row.get('Average Rating'),
            'publisher': row.get('Publisher'),
            'binding': row.get('Binding'),
            'pages': row.get('Number of Pages'),
            'year_published': row.get('Year Published'),
            'original_pub_year': row.get('Original Publication Year'),
            'date_read': date_read,
            'date_added': date_added,
            'shelves': row.get('Bookshelves'),
            'review': "" # Clear review as requested
        }
        
        # Restore cover image if it exists
        if (title, author) in existing_covers:
            book['cover_image'] = existing_covers[(title, author)]
            
        books.append(book)

# Sort by Date Read (descending), then Date Added (descending)
# Treat None as oldest
books.sort(key=lambda x: (x['date_read'] or '', x['date_added'] or ''), reverse=True)

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(books, f, indent=2, ensure_ascii=False)

print(f"Converted {len(books)} books to {json_path}")
