import os
from icrawler.builtin import GoogleImageCrawler
from icrawler.downloader import ImageDownloader


# Custom downloader that renames files using a filename map
class RenamingImageDownloader(ImageDownloader):
    def __init__(self, *args, **kwargs):
        self.filename_map = {}
        self.counter = 0
        super().__init__(*args, **kwargs)

    def get_filename(self, task, default_ext):
        filename = self.filename_map.get(self.counter)
        if filename:
            filename = filename
        else:
            filename = f"{str(self.counter).zfill(7)}{default_ext}"
        self.counter += 1
        return filename


# Tarot card search queries and desired filenames
cards = {
    "The Empress": "the-empress",
    "The Magician": "the-magician",
    "The High Priestess": "the-high-priestess",
    "The Lovers": "the-lovers",
    "Temperance": "temperance",
    "Seven of Swords": "seven-of-swords",
    "Five of Cups": "five-of-cups",
    "Three of Pentacles": "three-of-pentacles",
    "Nine of Wands": "nine-of-wands",
    "Knight of Cups": "knight-of-cups"
}

deck_name = "Heaven and Earth Tarot"
image_suffix = "site:pinterest.com -hands -background -spread -box"

# Ensure output folder exists
output_dir = "./images"
os.makedirs(output_dir, exist_ok=True)

# Run the crawler for each tarot card
for card_name, base_filename in cards.items():
    search_query = f"{card_name} {deck_name} {image_suffix}"
    print(f"\n📥 Downloading: {search_query} -> {base_filename}")

    # Map for 5 images
    filename_map = {i: f"{base_filename}-{i+1}.jpg" for i in range(5)}

    # Set up the crawler and manually assign the filename_map
    crawler = GoogleImageCrawler(
        downloader_cls=RenamingImageDownloader,
        downloader_threads=4,
        storage={'root_dir': output_dir}
    )

    # Set the filename map on the actual downloader instance
    crawler.downloader.filename_map = filename_map

    # Start crawling
    crawler.crawl(keyword=search_query, max_num=5)

print("\n✅ Download complete. Check the 'images' folder.")
