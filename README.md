# 🎸 Metal Archives Discography Scraper

Extracts **full-length albums** from **any "List of [genre] metal bands"** Wikipedia page and matches them to **Metal Archives** discographies.

## ✨ **Features**
- ✅ Works with **ANY** Wikipedia "List of [genre] metal/rock bands" page
- ✅ Handles **lists AND tables** automatically  
- ✅ **Smart genre detection** from URL (doom, black, death, stoner, etc.)
- ✅ Verifies bands have correct genre on Metal Archives
- ✅ Extracts **full-length albums only** with ratings
- ✅ Outputs clean JSON: `doom_albums.json`, `black_albums.json`, etc.

## 🚀 **Quick Start**

1. **Install dependencies** (one-time):
```bash
pip install selenium beautifulsoup4 webdriver-manager lxml

    Run any genre (double-click or terminal):

bash
# Doom metal
python scraper.py

# Black metal  
python scraper.py "https://en.wikipedia.org/wiki/List_of_black_metal_bands"

# Stoner rock/metal
python scraper.py "https://en.wikipedia.org/wiki/List_of_stoner_rock_and_metal_bands"

📊 Example Output

json
[
  {
    "band_name": "Electric Wizard", 
    "album_name": "Dopamine", 
    "year": 2012,
    "genres": "Doom/Stoner Metal",
    "rating": "87%",
    "link": "https://www.metal-archives.com/albums/Electric_Wizard/Dopamine/234567"
  }
]

🔧 Easy Customization

Just edit line 30 in scraper.py:

python
wiki_url = "https://en.wikipedia.org/wiki/List_of_YOUR_GENRE_metal_bands"

⚠️ Notes

    Downloads ChromeDriver automatically

    Tests first 5 bands (change bands[:5] to process all)

    Includes polite delays to respect websites

    Works on Windows/Mac/Linux

🛠️ Requirements

    Python 3.8+

    Chrome browser

    30-60 seconds per genre (first 5 bands)
