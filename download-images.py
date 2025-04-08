import os
import shutil
from icrawler.builtin import GoogleImageCrawler
from icrawler.downloader import ImageDownloader


# Custom downloader that renames the file after download
class RenamingImageDownloader(ImageDownloader):
    def __init__(self, *args, filename_map=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename_map = filename_map or {}
        print("RenamingImageDownloader initialized with filename_map:", self.filename_map)

    def download(self, task, default_ext, timeout=5, **kwargs):
        print(f"Downloading task: {task}")
        result = super().download(task, default_ext, timeout, **kwargs)
        if result:
            original_path = os.path.join(self.storage['root_dir'], task['filename'])
            new_filename = self.filename_map.get(task['file_idx'], task['filename'])
            print(f"Original path: {original_path}, New filename: {new_filename}, file_idx: {task.get('file_idx')}")
            new_path = os.path.join(self.storage['root_dir'], new_filename)
            shutil.move(original_path, new_path)
        return result


# Tarot card search queries and desired filenames
cards = {
    "The Hanged Man": "the-hanged-man",
}

deck_name = "Heaven and Earth Tarot"
image_suffix = "site:pinterest.com -hands -background -spread -box"

# Ensure output folder exists
output_dir = "./images"
os.makedirs(output_dir, exist_ok=True)


# Run the crawler for each tarot card
for index, (card_name, base_filename) in enumerate(cards.items()):
    search_query = f"{card_name} {deck_name} {image_suffix}"
    print(f"Downloading: {search_query} -> {base_filename}")

    crawler = GoogleImageCrawler(
        downloader_cls=RenamingImageDownloader,
        downloader_threads=4,
        storage={'root_dir': output_dir}
    )

    filename_map = {index * 5 + i: f"{base_filename}-{i+1}.jpg" for i in range(5)}
    crawler.downloader.filename_map = filename_map
    print(f"Filename map set for {card_name}: {crawler.downloader.filename_map}")
    crawler.crawl(keyword=search_query, max_num=5, file_idx_offset=index * 5)

print("Download complete from Google Images in the 'images' folder.")