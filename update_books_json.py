import json
import os

def slugify(text):
    return "".join(c if c.isalnum() else "_" for c in text).lower()

def main():
    json_path = 'data/books.json'
    covers_dir = 'static/images/covers'
    
    # Get list of existing cover files
    existing_covers = set(os.listdir(covers_dir))
    
    with open(json_path, 'r', encoding='utf-8') as f:
        books = json.load(f)
    
    updated_count = 0
    
    for book in books:
        title = book.get('title')
        if not title:
            continue
            
        filename = f"{slugify(title)}.jpg"
        
        # If we have the file locally, update the JSON
        if filename in existing_covers:
            current_path = book.get('cover_image', '')
            new_path = f"/images/covers/{filename}"
            
            if current_path != new_path:
                book['cover_image'] = new_path
                updated_count += 1
                # print(f"Updated {title} -> {new_path}")
    
    if updated_count > 0:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(books, f, indent=2, ensure_ascii=False)
        print(f"Updated books.json with {updated_count} local covers.")
    else:
        print("No new local covers matched.")

if __name__ == "__main__":
    main()
