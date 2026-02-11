import json
import requests
import os
import time
from urllib.parse import urlparse
import urllib3
import random

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_image(url, save_path):
    # Retry logic for rate limiting
    max_retries = 5
    base_delay = 10
    
    for attempt in range(max_retries):
        try:
            # Some servers might block requests without a User-Agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, stream=True, verify=False, headers=headers)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                return True
            elif response.status_code == 429:
                # Rate limited
                wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"  Rate limited (429). Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"Status code {response.status_code} for {url}")
                return False
                
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False
            
    print(f"Failed to download {url} after {max_retries} retries")
    return False

def slugify(text):
    return "".join(c if c.isalnum() else "_" for c in text).lower()

def main():
    json_path = 'data/books.json'
    covers_dir = 'static/images/covers'
    
    if not os.path.exists(covers_dir):
        os.makedirs(covers_dir)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        books = json.load(f)
    
    updated_count = 0
    
    for book in books:
        title = book.get('title')
        cover_image = book.get('cover_image')
        
        if not cover_image:
            continue
            
        # Skip if already a local path
        if cover_image.startswith('/images/covers/'):
            continue
            
        print(f"Processing: {title}")
        
        # Create a filename based on title
        filename = f"{slugify(title)}.jpg"
        save_path = os.path.join(covers_dir, filename)
        
        # Download
        if download_image(cover_image, save_path):
            # Update path in JSON
            # We use root-relative path for the site
            new_path = f"/images/covers/{filename}"
            book['cover_image'] = new_path
            updated_count += 1
            print(f"  Downloaded to {new_path}")
        else:
            print(f"  Failed to download cover for {title}")
            
        # Be nice to servers
        time.sleep(5)
        
    if updated_count > 0:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(books, f, indent=2, ensure_ascii=False)
        print(f"\nSuccessfully downloaded and updated {updated_count} covers.")
    else:
        print("\nNo covers needed updating.")

if __name__ == "__main__":
    main()
