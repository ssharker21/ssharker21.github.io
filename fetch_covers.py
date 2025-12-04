import json
import requests
import time

# Google Books API endpoint
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

def get_cover_from_google_books(isbn, title, author):
    query = ""
    if isbn:
        query = f"isbn:{isbn}"
    else:
        # Fallback to title and author if no ISBN
        query = f"intitle:{title}+inauthor:{author}"
    
    try:
        response = requests.get(GOOGLE_BOOKS_API, params={"q": query})
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                volume_info = data["items"][0]["volumeInfo"]
                if "imageLinks" in volume_info:
                    # Prefer extraLarge, large, medium, then thumbnail
                    images = volume_info["imageLinks"]
                    for size in ["extraLarge", "large", "medium", "thumbnail", "smallThumbnail"]:
                        if size in images:
                            # Google Books images are http by default, switch to https
                            return images[size].replace("http://", "https://")
    except Exception as e:
        print(f"Error fetching cover for {title}: {e}")
    return None

def main():
    json_path = 'data/books.json'
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            books = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {json_path}")
        return

    updated_count = 0
    for book in books:
        # Skip if already has a custom cover image
        if book.get('cover_image'):
            continue

        print(f"Checking cover for: {book.get('title')}")
        
        # Try to fetch cover
        cover_url = get_cover_from_google_books(
            book.get('isbn'), 
            book.get('title'), 
            book.get('author')
        )
        
        if cover_url:
            book['cover_image'] = cover_url
            print(f"  Found cover: {cover_url}")
            updated_count += 1
        else:
            print("  No cover found.")
        
        # Be nice to the API
        time.sleep(0.2)

    if updated_count > 0:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(books, f, indent=2, ensure_ascii=False)
        print(f"\nUpdated {updated_count} books with new covers.")
    else:
        print("\nNo new covers found.")

if __name__ == "__main__":
    main()
