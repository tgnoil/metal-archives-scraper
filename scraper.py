from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time
import re
import sys


def setup_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def extract_genre_from_url(wiki_url):
    """Extract genre term from Wikipedia URL - gets single word before _metal/_rock"""
    filename = wiki_url.split('/')[-1].lower()
    
    # NEW: Take everything after "list_of_" and before FIRST _metal OR _rock
    if 'list_of_' in filename:
        content = filename.replace('list_of_', '')
        if '_metal' in content:
            genre = content.split('_metal')[0]
        elif '_rock' in content:
            genre = content.split('_rock')[0]
        else:
            genre = content.split('_bands')[0]
        
        # Clean up: take first word only (handles "stoner_rock_and")
        genre = genre.split('_')[0]  # Just "stoner"
        return genre if genre else "doom"
    
    # Fallback
    return "doom"


def extract_bands_from_wiki(soup, wiki_url):
    """Extract band names from Wikipedia page - handles BOTH lists AND tables"""
    genre_term = extract_genre_from_url(wiki_url)
    print(f"🎯 Extracting {genre_term} bands from lists AND tables...")
    
    bands = []
    content = soup.find("div", {"class": "mw-parser-output"})
    if not content:
        return bands
    
    # STRATEGY 1: Lists (works for Doom, Stoner pages)
    print("  📋 Checking lists...")
    list_count = 0
    for li in content.find_all("li", recursive=True):
        a = li.find("a", title=True)
        if a and not a.find("img"):
            band_name = a.get_text(strip=True)
            if (band_name and len(band_name) > 1 and 
                not any(x in band_name.lower() for x in ['about', 'metal.de', 'allmusic', 'list of'])):
                bands.append(band_name)
                list_count += 1
    
    # STRATEGY 2: Tables (works for Black, Death, Thrash pages)
    print("  📊 Checking tables...")
    table_count = 0
    tables = content.find_all("table", class_="wikitable")
    for table in tables:
        for row in table.find_all("tr")[1:]:  # Skip header
            cells = row.find_all(["td", "th"])
            if cells:
                # First cell usually contains band name link
                a = cells[0].find("a")
                if a and not a.find("img"):
                    band_name = a.get_text(strip=True)
                    if (band_name and len(band_name) > 1 and 
                        genre_term not in band_name.lower()):  # Avoid genre pages
                        bands.append(band_name)
                        table_count += 1
    
    # Clean and dedupe
    bands = sorted(list(set(bands)))
    bands = [name.replace(" (band)", "").strip() for name in bands]
    
    print(f"  ✓ Found {list_count} from lists + {table_count} from tables = {len(bands)} unique bands")
    return bands


def main(wiki_url=None):
    if not wiki_url:
        # =====================================================
        # 🚨 EASY URL SWAP - Change this line for any genre! 🚨
        # =====================================================
        # Examples:
        # wiki_url = "https://en.wikipedia.org/wiki/List_of_doom_metal_bands"
        # wiki_url = "https://en.wikipedia.org/wiki/List_of_thrash_metal_bands"
        # wiki_url = "https://en.wikipedia.org/wiki/List_of_folk_metal_bands"
        # wiki_url = "https://en.wikipedia.org/wiki/List_of_heavy_metal_bands"
        # wiki_url = "https://en.wikipedia.org/wiki/List_of_speed_metal_bands"
        # wiki_url = "https://en.wikipedia.org/wiki/List_of_black_metal_bands,_0%E2%80%93K" 
        # wiki_url = "https://en.wikipedia.org/wiki/List_of_black_metal_bands,_L%E2%80%93Z" 
        # wiki_url = "https://en.wikipedia.org/wiki/List_of_death_metal_bands,_!%E2%80%93K"
        # wiki_url = "https://en.wikipedia.org/wiki/List_of_death_metal_bands,_L%E2%80%93Z"
        wiki_url = "https://en.wikipedia.org/wiki/List_of_black_metal_bands,_0%E2%80%93K"
        # =====================================================
    
    if len(sys.argv) > 1:
        wiki_url = sys.argv[1]
    
    genre_term = extract_genre_from_url(wiki_url)
    print(f"🚀 Starting {genre_term.title()} metal scraper from: {wiki_url}")
    driver = setup_driver()
    print("✓ Chrome driver ready!")
    
    # 1. Extract bands from Wikipedia
    print("📖 Loading Wikipedia...")
    driver.get(wiki_url)
    time.sleep(3)
    print("✓ Wikipedia loaded!")
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    bands = extract_bands_from_wiki(soup, wiki_url)
    print(f"✓ Extracted {len(bands)} unique {genre_term} bands")
    
    if not bands:
        print("❌ No bands found! Check the Wikipedia URL.")
        driver.quit()
        return
    
    # 2. Scrape Metal Archives
    results = []
    # =====================================================
    # 🚨 Change bands[:#] to slice - or remove to get full list 🚨
    # =====================================================
    for i, band_name in enumerate(bands[:], 1):  
    # =====================================================
        print(f"\n{band_name}")
        
        # Search MA
        search_url = f"https://www.metal-archives.com/search?searchString={band_name.replace(' ', '%20')}&type=band_name"
        driver.get(search_url)
        time.sleep(2)
        
        try:
            # Extract ALL band URLs from search results FIRST
            band_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/bands/')]")
            band_urls = []
            for link in band_links:
                url = link.get_attribute('href')
                if url and url not in band_urls:
                    band_urls.append(url)

            print(f"  Found {len(band_urls)} unique band URLs")

            correct_band = None
            band_name_correct = None
            genres = genre_term.title()

            # Now test URLs sequentially
            for j, test_url in enumerate(band_urls[:5]):  # Check first 5 URLs
                print(f"  Testing {j+1}/5: {test_url}")
                
                driver.get(test_url)
                time.sleep(2)
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                # Genre selector
                genre_dl = soup.find('dl', class_='float_right')
                genres_text = genre_term.title()
                if genre_dl:
                    genre_dt = genre_dl.find('dt', string=re.compile('Genre', re.I))
                    if genre_dt:
                        genre_dd = genre_dt.find_next_sibling('dd')
                        if genre_dd:
                            genres_text = genre_dd.get_text(strip=True)
                
                genres_lower = genres_text.lower()
                print(f"    Genre: '{genres_text}'")
                
                # DYNAMIC GENRE MATCHING
                if genre_term.lower() in genres_lower:
                    correct_band = test_url
                    band_name_correct = soup.find('h1').get_text(strip=True).split(' - ')[0] if soup.find('h1') else test_url.split('/')[-1].replace('_', ' ')
                    genres = genres_text
                    print(f"  ✓ {genre_term.upper()} MATCH: {correct_band}")
                    break

            if not correct_band:
                print("  → No matching band found in top 5 results")
                continue
                
            time.sleep(1)

            # Now process the correct band
            print(f"  → Processing: {band_name_correct}")
            print(f"  → Genres: {genres}")
            
            # Try Main tab first
            print("  → Trying Main tab...")
            main_tab = driver.find_elements(By.XPATH, "//a[contains(@href, '/tab/main')]")
            main_albums = []
            
            if main_tab:
                main_tab[0].click()
                time.sleep(2)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                table = soup.find('table', class_='discog')
                
                if table:
                    rows = table.find('tbody').find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) == 4:
                            album_link = cols[0].find('a')
                            album_type = cols[1].get_text(strip=True)
                            year_text = cols[2].get_text(strip=True)
                            rating_elem = cols[3].find('a')
                            rating = rating_elem.get_text(strip=True) if rating_elem else None
                            
                            year_match = re.search(r'\b(19|20)\d{2}\b', year_text)
                            if (album_link and year_match and 'Full-length' in album_type):
                                main_albums.append({
                                    "band_name": band_name_correct,
                                    "album_name": album_link.get_text(strip=True),
                                    "year": int(year_match.group(0)),
                                    "genres": genres,
                                    "rating": rating,
                                    "link": album_link['href'] if album_link['href'].startswith('http') else "https://www.metal-archives.com" + album_link['href']
                                })
            
            if main_albums:
                results.extend(main_albums)
                print(f"  → Main tab: {len(main_albums)} full-length albums")
            else:
                # Fallback: Complete discography
                print("  → Main empty, trying Complete discography...")
                band_id_match = re.search(r'/bands/[^/]+/(\d+)', correct_band)
                if band_id_match:
                    band_id = band_id_match.group(1)
                    complete_url = f"https://www.metal-archives.com/band/discography/id/{band_id}/tab/all"
                    print(f"  → Loading: {complete_url}")
                    
                    driver.get(complete_url)
                    time.sleep(3)
                    
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    table = (soup.find('table', class_='discog') or 
                            soup.find('table', class_='discography_table') or 
                            soup.find('table', {'width': '100%'}))
                    
                    if table:
                        rows = table.find_all('tr')[1:]  # Skip header
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 3:
                                # Handle both column orders
                                if cols[0].find('a'):
                                    album_link = cols[0].find('a')
                                    type_cell = cols[1].get_text(strip=True)
                                    year_text = cols[2].get_text(strip=True)
                                else:
                                    year_text = cols[0].get_text(strip=True)
                                    album_link = cols[1].find('a')
                                    type_cell = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                                
                                rating = cols[-1].get_text(strip=True) if len(cols) > 3 else None
                                year_match = re.search(r'\b(19|20)\d{2}\b', year_text)
                                
                                if (album_link and year_match and 
                                    any(term in type_cell for term in ['Full-length', 'Album', 'LP']) and
                                    all(term not in type_cell for term in ['Single', 'Demo', 'Live', 'Split'])):
                                    
                                    results.append({
                                        "band_name": band_name_correct,
                                        "album_name": album_link.get_text(strip=True),
                                        "year": int(year_match.group(0)),
                                        "genres": genres,
                                        "rating": rating,
                                        "link": album_link['href'] if album_link['href'].startswith('http') else "https://www.metal-archives.com" + album_link['href']
                                    })
                        
                        print(f"  → Complete tab: {len([r for r in results if r['band_name'] == band_name_correct])} albums")
                else:
                    print("  → Could not extract band ID")
        except Exception as e:
            print(f"  → Error: {str(e)[:100]}")
    
    driver.quit()
    print(f"\n🎉 COMPLETE! {len(results)} albums extracted")
    
    # Save JSON
    filename = f"{extract_genre_from_url(wiki_url)}_albums.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved to {filename}")

if __name__ == "__main__":
    main()
