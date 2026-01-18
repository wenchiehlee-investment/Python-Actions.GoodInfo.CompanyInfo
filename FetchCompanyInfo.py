import pandas as pd
import requests
import urllib3
import re
import time
import os
from io import StringIO
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

# Try to import Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Try to import Google GenAI
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Suppress only the single warning from urllib3 needed.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ... [Existing Constants] ...
INPUT_CSV = "StockID_TWSE_TPEX.csv"
OUTPUT_CSV = "raw_companyinfo.csv"
BASE_URL = "https://isin.twse.com.tw/isin/C_public.jsp?strMode={mode}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

CONCEPT_KEYWORDS = {
    "nVidia概念": ["nvidia", "輝達"],
    "Google概念": ["google", "谷歌"],
    "Amazon概念": ["amazon", "亞馬遜"],
    "Meta概念": ["meta", "facebook", "臉書"],
    "OpenAI概念": ["openai", "open ai", "chatgpt"],
    "Microsoft概念": ["microsoft", "msft", "微軟"],
    "AMD概念": ["amd", "超微"],
    "Apple概念": ["apple", "蘋果"],
    "Oracle概念": ["oracle", "甲骨文"],
    "Micro概念": ["supermicro", "美超微", "super micro"],
}
CONCEPT_COLUMNS = list(CONCEPT_KEYWORDS.keys())

def build_concept_flags(concepts_text):
    if pd.isna(concepts_text) or concepts_text is None:
        text = ""
    else:
        text = str(concepts_text)

    lowered = text.lower()
    tokens = [t.strip().lower() for t in re.split(r"[;,、/|\\s]+", text) if t.strip()]

    flags = {}
    for col, keywords in CONCEPT_KEYWORDS.items():
        found = False
        for kw in keywords:
            kw_l = kw.lower()
            if kw_l in lowered or any(kw_l in token for token in tokens):
                found = True
                break
        flags[col] = 1 if found else 0
    return flags

def add_concept_flag_columns(df):
    if "相關概念" not in df.columns:
        for col in CONCEPT_COLUMNS:
            df[col] = 0
        return df

    flags_df = df["相關概念"].apply(build_concept_flags).apply(pd.Series)
    for col in CONCEPT_COLUMNS:
        df[col] = flags_df[col].fillna(0).astype(int)
    return df

def get_selenium_driver():
    if not SELENIUM_AVAILABLE:
        return None

    print("Initializing Selenium Driver...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        # Increase timeout for CI environments (60 seconds)
        driver.set_page_load_timeout(60)
        return driver
    except Exception as e:
        print(f"Failed to initialize Selenium: {e}")
        return None

def get_goodinfo_group_map(driver):
    """
    Fetches the mapping of Stock ID -> Group Name from GoodInfo's Group List page.
    This is much more efficient than visiting every stock page.
    """
    if driver is None:
        return {}
        
    print("Fetching GoodInfo Group Map...")
    group_map = {}
    
    try:
        # 1. Get list of all groups
        url_all_groups = "https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E9%9B%86%E5%9C%98%E8%82%A1&SHEET=%E8%82%A1%E7%A5%A8%E6%B8%85%E5%96%AE"
        try:
            driver.get(url_all_groups)
        except Exception as e:
            print(f"Timeout or error loading Group List page: {e}")
            return {} # Abort if main list fails
        
        # Wait for links to appear
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'MARKET_CAT=%E9%9B%86%E5%9C%98%E8%82%A1')]"))
        )
        
        links = driver.find_elements(By.XPATH, "//a[contains(@href, 'MARKET_CAT=%E9%9B%86%E5%9C%98%E8%82%A1')]")
        
        group_links = set()
        for link in links:
            href = link.get_attribute('href')
            text = link.text.strip()
            if "INDUSTRY_CAT" in href and text:
                group_links.add((text, href))
        
        print(f"Found {len(group_links)} unique groups. Mapping stocks...")
        
        # 2. Iterate ALL groups
        total_groups = len(group_links)
        for i, (group_name, href) in enumerate(group_links):
            print(f"  [{i+1}/{total_groups}] Mapping Group: {group_name}")
            try:
                driver.get(href)
                time.sleep(1.5) # Short wait
                
                # Restrict search to the main stock list table to avoid sidebar links
                stock_links = driver.find_elements(By.XPATH, "//table[@id='tblStockList']//a[contains(@href, 'StockDetail.asp?STOCK_ID=')]")
                
                for sl in stock_links:
                    shref = sl.get_attribute('href')
                    if "STOCK_ID=" in shref:
                        try:
                            sid = shref.split("STOCK_ID=")[1].split("&")[0]
                            if sid in group_map:
                                if group_name not in group_map[sid]:
                                    group_map[sid] += f", {group_name}"
                            else:
                                group_map[sid] = group_name
                        except:
                            pass
            except Exception as e:
                print(f"  Skipping group {group_name} due to error: {e}")
                continue
                        
    except Exception as e:
        print(f"Error fetching group map: {e}")
        
    print(f"Mapped {len(group_map)} stocks to groups.")
    return group_map

def fetch_goodinfo_data(driver, stock_id):
    if driver is None:
        return None, None, None

    url = f"https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={stock_id}"
    
    try:
        try:
            driver.get(url)
        except Exception as e:
            print(f"  Timeout/Error loading page for {stock_id}: {e}")
            return None, None
        
        # Wait for the "Initializing" to pass and content to load
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "td")))
        except:
            pass 

        html = driver.page_source
        
        def extract(field_name):
            # Case A: Special for Main Business (often in a <p>)
            if field_name == "主要業務":
                # <nobr>主要業務</nobr>...<p...>(Value)</p>
                p_match = re.search(fr"<nobr>{field_name}</nobr>.*?<p[^>]*>(.*?)</p>", html, re.DOTALL | re.IGNORECASE)
                if p_match:
                    return re.sub(r'<[^>]+>', '', p_match.group(1)).strip().replace('&nbsp;', ' ')
            
            # General fallback
            patterns = [
                fr"<nobr>{field_name}</nobr>.*?<td[^>]*>(.*?)</td>",
                fr">{field_name}</td>\s*<td[^>]*>(.*?)</td>",
                fr">{field_name}</nobr>.*?<td[^>]*>(.*?)</td>"
            ]
            
            for pat in patterns:
                m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
                if m:
                    return re.sub(r'<[^>]+>', '', m.group(1)).strip().replace('&nbsp;', ' ')
            return None

        def extract_market_cap():
            patterns = [
                r"<nobr>\s*市值(?:\s*\([^<]*\))?\s*</nobr>.*?<td[^>]*>(.*?)</td>",
                r">市值(?:\s*\([^<]*\))?</td>\s*<td[^>]*>(.*?)</td>",
                r">市值(?:\s*\([^<]*\))?</nobr>.*?<td[^>]*>(.*?)</td>"
            ]
            for pat in patterns:
                m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
                if m:
                    return re.sub(r'<[^>]+>', '', m.group(1)).strip().replace('&nbsp;', ' ')
            return None

        main_biz = extract("主要業務")
        concepts = extract("相關概念")
        market_cap = extract_market_cap()
        
        return main_biz, concepts, market_cap

    except Exception as e:
        print(f"Error fetching GoodInfo for {stock_id}: {e}")
        return None, None, None

def fetch_gemini_concepts(stock_list):
    """
    Uses Gemini API to identify concept stocks for specific tech giants.
    stock_list: list of tuples (id, name)
    Returns: dict { 'StockID': 'Concepts' }
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key or not GENAI_AVAILABLE:
        print("Skipping Gemini analysis (API Key missing or SDK not found).")
        return {}

    print("Initializing Gemini Client...")
    client = genai.Client(api_key=api_key)
    
    # Process in chunks to avoid context limits
    chunk_size = 40
    results = {}
    
    total_chunks = (len(stock_list) + chunk_size - 1) // chunk_size
    
    for i in range(0, len(stock_list), chunk_size):
        chunk = stock_list[i:i + chunk_size]
        print(f"  Sending chunk {i//chunk_size + 1}/{total_chunks} to Gemini...")
        
        # Format list for prompt
        stock_text = "\n".join([f"{s[0]} {s[1]}" for s in chunk])
        
        prompt = f"""
        You are a financial analyst specializing in Taiwan tech stocks.
        Analyze the following list of companies.
        
        Task: Identify if each company is part of the supply chain or a "concept stock" for these specific Tech Giants:
        [Nvidia, Oracle, Google, Amazon, Meta, OpenAI]
        
        Rules:
        1. Only return the names of the Tech Giants from the list above that the company is related to.
        2. If related to multiple, separate with commas (e.g., "Nvidia, Google").
        3. If not related to any of these specific giants, return "None".
        4. Output strictly in CSV format: StockID, Matched_Concepts
        5. Do not output markdown code blocks.
        
        Stocks:
        {stock_text}
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            # Parse CSV response
            lines = response.text.strip().split('\n')
            for line in lines:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    sid = parts[0].strip()
                    concepts = parts[1].strip()
                    if concepts.lower() != "none" and "stockid" not in sid.lower():
                        results[sid] = concepts
            
            time.sleep(2) # Rate limit nice-ness
            
        except Exception as e:
            print(f"  Gemini Error: {e}")
            
    return results

# ... [fetch_isin_table function] ...

def main():
    # ... [Existing logic: Load CSV, Fetch ISIN, Fetch ETF] ...
    
    # 1) 讀 base CSV
    base = pd.read_csv(INPUT_CSV, dtype={"代號": str})
    base["代號"] = base["代號"].astype(str).str.strip()

    # ... [Fetch ISIN] ...
    # (Abbreviated for patch context, assuming previous structure is maintained)
    # Actually I need to be careful with 'replace' tool context.
    # I will target specific insertion points or rewrite main.
    
    # Let's rewrite main to be safe.
    
    # ... [Fetch ETF] ...
    
    # ... [Merge] ...
    
    # === Fetch GoodInfo (Selenium) ===
    # ... [Existing Code] ...
    
    # === Fetch Gemini Concepts ===
    # New Logic Here
    
    # ... [Save]
    if not SELENIUM_AVAILABLE:
        return None
    
    print("Initializing Selenium Driver...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        # Set a strict page load timeout (30 seconds) to prevent hanging
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        print(f"Failed to initialize Selenium: {e}")
        return None

def get_goodinfo_group_map(driver):
    """
    Fetches the mapping of Stock ID -> Group Name from GoodInfo's Group List page.
    This is much more efficient than visiting every stock page.
    """
    if driver is None:
        return {}
        
    print("Fetching GoodInfo Group Map...")
    group_map = {}
    
    try:
        # 1. Get list of all groups
        url_all_groups = "https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E9%9B%86%E5%9C%98%E8%82%A1&SHEET=%E8%82%A1%E7%A5%A8%E6%B8%85%E5%96%AE"
        try:
            driver.get(url_all_groups)
        except Exception as e:
            print(f"Timeout or error loading Group List page: {e}")
            return {} # Abort if main list fails
        
        # Wait for links to appear
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'MARKET_CAT=%E9%9B%86%E5%9C%98%E8%82%A1')]"))
        )
        
        links = driver.find_elements(By.XPATH, "//a[contains(@href, 'MARKET_CAT=%E9%9B%86%E5%9C%98%E8%82%A1')]")
        
        group_links = set()
        for link in links:
            href = link.get_attribute('href')
            text = link.text.strip()
            if "INDUSTRY_CAT" in href and text:
                group_links.add((text, href))
        
        print(f"Found {len(group_links)} unique groups. Mapping stocks...")
        
        # 2. Iterate ALL groups
        total_groups = len(group_links)
        for i, (group_name, href) in enumerate(group_links):
            print(f"  [{i+1}/{total_groups}] Mapping Group: {group_name}")
            try:
                driver.get(href)
                time.sleep(1.5) # Short wait
                
                # Restrict search to the main stock list table to avoid sidebar links (e.g. Recently Viewed)
                # Table ID is usually 'tblStockList'
                stock_links = driver.find_elements(By.XPATH, "//table[@id='tblStockList']//a[contains(@href, 'StockDetail.asp?STOCK_ID=')]")
                
                for sl in stock_links:
                    shref = sl.get_attribute('href')
                    if "STOCK_ID=" in shref:
                        try:
                            sid = shref.split("STOCK_ID=")[1].split("&")[0]
                            if sid in group_map:
                                if group_name not in group_map[sid]:
                                    group_map[sid] += f", {group_name}"
                            else:
                                group_map[sid] = group_name
                        except:
                            pass
            except Exception as e:
                print(f"  Skipping group {group_name} due to error: {e}")
                continue
                        
    except Exception as e:
        print(f"Error fetching group map: {e}")
        
    print(f"Mapped {len(group_map)} stocks to groups.")
    return group_map

def _process_gemini_batch(client, stock_chunk, max_retries=5):
    """Helper to process a single batch of stocks with Gemini."""
    results = {}
    # Format list for prompt
    stock_text = "\n".join([f"{s[0]} {s[1]}" for s in stock_chunk])

    prompt = f"""
    You are a financial analyst specializing in Taiwan tech stocks.
    Analyze the following list of companies.

    Task: Identify if each company is part of the supply chain or a "concept stock" for these specific Tech Giants:
    [Nvidia, Oracle, Google, Amazon, Meta, OpenAI, Microsoft, AMD, Apple]

    Rules:
    1. Only return the names of the Tech Giants from the list above that the company is related to.
    2. If related to multiple, separate with semicolons (e.g., "Nvidia;Google").
    3. If not related to any of these specific giants, return "None".
    4. Output strictly in CSV format: StockID, Matched_Concepts
    5. Do not output markdown code blocks.

    Stocks:
    {stock_text}
    """

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            # Parse CSV response
            text = response.text
            if text.startswith("```"): # Cleanup markdown
                text = text.strip("`").replace("csv\n", "", 1)

            lines = text.strip().split('\n')
            for line in lines:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    sid = parts[0].strip()
                    # Replace any remaining commas with semicolons
                    concepts = parts[1].strip().replace(',', ';')

                    # Basic validation
                    if concepts.lower() != "none" and sid.isdigit():
                        results[sid] = concepts

            # Success - wait before next request
            time.sleep(3)
            return results

        except Exception as e:
            error_str = str(e)
            # Check if it's a 503 (overloaded) or rate limit error
            if '503' in error_str or 'overloaded' in error_str.lower() or 'rate' in error_str.lower():
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 3  # Exponential backoff: 3, 6, 12, 24, 48 seconds
                    print(f"  Gemini API overloaded/rate limited, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  Gemini API Error after {max_retries} attempts: {e}")
            else:
                # Non-retryable error
                print(f"  Gemini API Error: {e}")
                break

    return results

def fetch_gemini_concepts(stock_list):
    """
    Uses Gemini API to identify concept stocks for specific tech giants.
    stock_list: list of tuples (id, name)
    Returns: dict { 'StockID': 'Concepts' }
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key or not GENAI_AVAILABLE:
        print("Skipping Gemini analysis (API Key missing or SDK not found).")
        return {}

    print("Initializing Gemini Client...")
    try:
        client = genai.Client(api_key=api_key)
        
        # Process in chunks to avoid context limits
        chunk_size = 40
        all_results = {}
        
        total_chunks = (len(stock_list) + chunk_size - 1) // chunk_size
        
        for i in range(0, len(stock_list), chunk_size):
            chunk = stock_list[i:i + chunk_size]
            print(f"  Sending chunk {i//chunk_size + 1}/{total_chunks} to Gemini...")
            
            batch_results = _process_gemini_batch(client, chunk)
            all_results.update(batch_results)
                
        return all_results
    except Exception as e:
        print(f"Failed to init Gemini Client: {e}")
        return {}
def fetch_goodinfo_data(driver, stock_id, max_retries=2):
    if driver is None:
        return None, None, None

    url = f"https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={stock_id}"

    for attempt in range(max_retries):
        try:
            try:
                driver.get(url)
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                    print(f"  Timeout loading page for {stock_id}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  Final timeout/error loading page for {stock_id}: {e}")
                    return None, None, None

            # Wait for the "Initializing" to pass and content to load
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "td")))
            except:
                pass

            html = driver.page_source

            def extract(field_name):
                # Case A: Special for Main Business (often in a <p>)
                if field_name == "主要業務":
                    # <nobr>主要業務</nobr>...<p...>(Value)</p>
                    p_match = re.search(fr"<nobr>{field_name}</nobr>.*?<p[^>]*>(.*?)</p>", html, re.DOTALL | re.IGNORECASE)
                    if p_match:
                        return re.sub(r'<[^>]+>', '', p_match.group(1)).strip().replace('&nbsp;', ' ')

                # General fallback
                patterns = [
                    fr"<nobr>{field_name}</nobr>.*?<td[^>]*>(.*?)</td>",
                    fr">{field_name}</td>\s*<td[^>]*>(.*?)</td>",
                    fr">{field_name}</nobr>.*?<td[^>]*>(.*?)</td>"
                ]

                for pat in patterns:
                    m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
                    if m:
                        return re.sub(r'<[^>]+>', '', m.group(1)).strip().replace('&nbsp;', ' ')
                return None

            def extract_market_cap():
                patterns = [
                    r"<nobr>\s*市值(?:\s*\([^<]*\))?\s*</nobr>.*?<td[^>]*>(.*?)</td>",
                    r">市值(?:\s*\([^<]*\))?</td>\s*<td[^>]*>(.*?)</td>",
                    r">市值(?:\s*\([^<]*\))?</nobr>.*?<td[^>]*>(.*?)</td>"
                ]
                for pat in patterns:
                    m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
                    if m:
                        return re.sub(r'<[^>]+>', '', m.group(1)).strip().replace('&nbsp;', ' ')
                return None

            main_biz = extract("主要業務")
            concepts = extract("相關概念")
            market_cap = extract_market_cap()
            if not market_cap:
                market_cap = extract("市值") or extract("目前市值") or extract("總市值")

            # Group is now handled globally, removed from here

            return main_biz, concepts, market_cap

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"  Error fetching GoodInfo for {stock_id}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(wait_time)
                continue
            else:
                print(f"  Final error fetching GoodInfo for {stock_id}: {e}")
                return None, None, None

    return None, None, None

def fetch_etf_weights(etf_id):
    """
    Fetches ETF constituents and weights from MoneyDJ.
    Returns a dictionary: { 'StockID': 'Weight%' }
    Example: { '2330': '47.5' }
    """
    # Basic0007B seems to be the "All Holdings" view
    url = f"https://www.moneydj.com/ETF/X/Basic/Basic0007B.xdjhtm?etfid={etf_id}.TW"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"Fetching ETF {etf_id} weights from MoneyDJ...")
    try:
        res = requests.get(url, headers=headers, timeout=20, verify=False)
        res.encoding = "utf-8"
        
        # Parse tables
        dfs = pd.read_html(StringIO(res.text))
        
        target_df = None
        for df in dfs:
            # Look for column headers
            cols = df.columns.astype(str)
            if "個股名稱" in cols and "投資比例(%)" in cols:
                target_df = df
                break
        
        if target_df is None:
            print(f"Warning: Constituent table not found for ETF {etf_id}")
            return {}
            
        weights = {}
        for _, row in target_df.iterrows():
            name_col = str(row["個股名稱"])
            weight_col = row["投資比例(%)"]
            
            # Parse Stock ID from "Name(ID.TW)"
            # Example: "台積電(2330.TW)"
            match = re.search(r'\((\d+)\.TW\)', name_col)
            if match:
                stock_id = match.group(1)
                # Convert weight to string, handle NaN
                if pd.isna(weight_col):
                    w_str = ""
                else:
                    w_str = str(weight_col).strip()
                
                weights[stock_id] = w_str
        
        print(f"  -> Retrieved {len(weights)} constituents for ETF {etf_id}")
        return weights

    except Exception as e:
        print(f"Error fetching ETF {etf_id}: {e}")
        return {}

def fetch_taifex_weights():
    """
    Fetches TAIEX constituent weights from TAIFEX.
    Returns: dict { 'StockID': 'Weight' }
    """
    url = "https://www.taifex.com.tw/cht/9/futuresQADetail"
    try:
        print("Fetching TAIFEX weights...")
        res = requests.get(url, headers=HEADERS, timeout=20)
        res.encoding = "utf-8" 
        
        # Use pandas to parse the table
        dfs = pd.read_html(StringIO(res.text))
        if not dfs:
            print("No tables found on TAIFEX page.")
            return {}
        
        df = dfs[0]
        
        # The table is double-columned: 
        # Left: [排行, 證券名稱, 證券名稱.1, 市值佔 大盤比重]
        # Right: [排行.1, 證券名稱.2, 證券名稱.3, 市值佔 大盤比重.1]
        
        # Part 1 (Left)
        p1 = df.iloc[:, [1, 3]].copy() # 證券名稱 (ID), 市值佔 大盤比重
        p1.columns = ['ID', 'Weight']
        
        # Part 2 (Right)
        p2 = df.iloc[:, [5, 7]].copy() # 證券名稱.2 (ID), 市值佔 大盤比重.1
        p2.columns = ['ID', 'Weight']
        
        full = pd.concat([p1, p2], ignore_index=True)
        full = full.dropna(subset=['ID'])
        
        # Clean ID (ensure string)
        full['ID'] = full['ID'].astype(str).str.strip()
        
        # Create Map
        weights = full.set_index('ID')['Weight'].to_dict()
        print(f"  -> Retrieved {len(weights)} constituents from TAIFEX")
        return weights
        
    except Exception as e:
        print(f"Error fetching TAIFEX weights: {e}")
        return {}

def fetch_isin_table(mode: int, market_label: str) -> pd.DataFrame:
    """
    mode = 2 → TWSE（上市）
    mode = 4 → TPEX（上櫃/興櫃）
    market_label = 'TWSE' 或 'TPEX'
    """
    url = BASE_URL.format(mode=mode)
    res = requests.get(url, headers=HEADERS, timeout=20, verify=False)
    res.encoding = "big5"

    df = pd.read_html(StringIO(res.text))[0]

    df.columns = df.iloc[0]
    df = df.iloc[1:].copy()

    df = df.rename(
        columns={
            "有價證券代號及名稱": "代號名稱",
            "上市日": "上市日",
            "市場別": "市場別",
            "產業別": "產業別",
        }
    )

    # 保留代號開頭為數字者
    df = df[df["代號名稱"].astype(str).str.match(r"^\d+")].copy()

    # 拆代號與名稱
    df["代號"] = df["代號名稱"].str.extract(r"^(\d+)")
    df["名稱_官方"] = df["代號名稱"].str.replace(r"^\d+", "", regex=True).str.strip()

    return df[["代號", "名稱_官方", "市場別", "產業別", "上市日"]]


def main():
    # 1) 讀 base CSV
    base = pd.read_csv(INPUT_CSV, dtype={"代號": str})
    base["代號"] = base["代號"].astype(str).str.strip()

    # 2) 抓 TWSE + TPEX 官方資料
    print("下載 TWSE（上市）資料...")
    twse_raw = fetch_isin_table(2, "TWSE")

    print("下載 TPEX（上櫃）資料...")
    tpex_raw = fetch_isin_table(4, "TPEX")

    print("下載 Emerging（興櫃）資料...")
    emg_raw = fetch_isin_table(5, "Emerging")

    print("下載 Public（公開發行）資料...")
    
    url_pub = BASE_URL.format(mode=1)
    res_pub = requests.get(url_pub, headers=HEADERS, timeout=20, verify=False)
    res_pub.encoding = "big5"
    pub_df = pd.read_html(StringIO(res_pub.text))[0]
    pub_df.columns = pub_df.iloc[0]
    pub_df = pub_df.iloc[1:].copy()
    
    # Mode 1 Columns: 有價證券代號及名稱, 國際證券辨識號碼..., 公開發行日, 產業別, ...
    pub_df = pub_df.rename(
        columns={
            "有價證券代號及名稱": "代號名稱",
            "產業別": "產業別_PUB",
        }
    )
    # Filter stocks
    pub_df = pub_df[pub_df["代號名稱"].astype(str).str.match(r"^\d+")].copy()
    pub_df["代號"] = pub_df["代號名稱"].str.extract(r"^(\d+)")
    pub_df["市場別_PUB"] = "公開發行" # Manually assign
    
    pub = pub_df[["代號", "市場別_PUB", "產業別_PUB"]]

    # === 產生 TWSE 欄位 ===
    twse = twse_raw.rename(
        columns={
            "市場別": "市場別_TWSE",
            "產業別": "產業別_TWSE",
        }
    )[
        [
            "代號",
            "市場別_TWSE",
            "產業別_TWSE",
        ]
    ]

    # === 產生 TPEX 欄位 ===
    tpex = tpex_raw.rename(
        columns={
            "市場別": "市場別_TPEX",
            "產業別": "產業別_TPEX",
        }
    )[
        [
            "代號",
            "市場別_TPEX",
            "產業別_TPEX",
        ]
    ]

    # === 產生 Emerging 欄位 ===
    emg = emg_raw.rename(
        columns={
            "市場別": "市場別_EMG",
            "產業別": "產業別_EMG",
        }
    )[
        [
            "代號",
            "市場別_EMG",
            "產業別_EMG",
        ]
    ]

    # 3) 抓取 ETF 成分股權重 (0050, 0056, 00878, 00919)
    print("下載 ETF 0050 成分股權重...")
    weights_0050 = fetch_etf_weights("0050")

    print("下載 ETF 0056 成分股權重...")
    weights_0056 = fetch_etf_weights("0056")

    print("下載 ETF 00878 成分股權重...")
    weights_00878 = fetch_etf_weights("00878")

    print("下載 ETF 00919 成分股權重...")
    weights_00919 = fetch_etf_weights("00919")

    print("下載 TAIFEX 大盤權重...")
    weights_taifex = fetch_taifex_weights()

    # 4) 合併
    merged = base.merge(twse, on="代號", how="left")
    merged = merged.merge(tpex, on="代號", how="left")
    merged = merged.merge(emg, on="代號", how="left")
    merged = merged.merge(pub, on="代號", how="left")

    # === 合併欄位 ===
    # 優先順序: TWSE > TPEX > Emerging > Public
    merged["市場別"] = (
        merged["市場別_TWSE"]
        .fillna(merged["市場別_TPEX"])
        .fillna(merged["市場別_EMG"])
        .fillna(merged["市場別_PUB"])
    )
    merged["產業別"] = (
        merged["產業別_TWSE"]
        .fillna(merged["產業別_TPEX"])
        .fillna(merged["產業別_EMG"])
        .fillna(merged["產業別_PUB"])
    )
    merged["市值"] = None

    # === Mapping ETF Weights ===
    merged["ETF_0050_權重"] = merged["代號"].map(weights_0050)
    merged["ETF_0056_權重"] = merged["代號"].map(weights_0056)
    merged["ETF_00878_權重"] = merged["代號"].map(weights_00878)
    merged["ETF_00919_權重"] = merged["代號"].map(weights_00919)
    merged["市值佔大盤比重"] = merged["代號"].map(weights_taifex)

    # Initialize empty columns
    merged["主要業務"] = None
    merged["相關概念"] = None
    merged["相關集團"] = None
    merged["市值"] = None
    
    # === Fetch GoodInfo Data (Selenium) ===
    driver = get_selenium_driver()
    if driver:
        # 1. Fetch Group Map (Bulk)
        print("Step 1: Fetching Group Map...")
        group_map = get_goodinfo_group_map(driver)
        
        # 2. Fetch Individual Stock Details
        print("Step 2: Fetching Stock Details...")
        total = len(merged)
        consecutive_failures = 0
        
        for idx, row in merged.iterrows():
            if consecutive_failures >= 5:
                print("Too many consecutive failures (IP blocked?). Stopping GoodInfo scrape.")
                break

            stock_id = row["代號"]
            print(f"[{idx+1}/{total}] Fetching GoodInfo for {stock_id} {row['名稱']}...")
            
            # Fetch Business & Concepts
            mb, cc, mv = fetch_goodinfo_data(driver, stock_id)
            
            if mb is None and cc is None and mv is None:
                consecutive_failures += 1
            else:
                consecutive_failures = 0
            
            # Get Group from Map
            gp = group_map.get(str(stock_id))
            
            # Update DataFrame directly
            merged.at[idx, "主要業務"] = mb
            merged.at[idx, "相關概念"] = cc
            merged.at[idx, "相關集團"] = gp
            merged.at[idx, "市值"] = mv

            # Delay to be polite/avoid being blocked (longer for CI environments)
            time.sleep(3)
        
        driver.quit()
    else:
        print("Skipping GoodInfo fetch (Selenium not available).")

    # === Fetch Gemini Concepts ===
    # Prepare list [(id, name)]
    stock_list_for_gemini = list(zip(merged["代號"], merged["名稱"]))
    gemini_results = fetch_gemini_concepts(stock_list_for_gemini)
    
    if gemini_results:
        print(f"Merging {len(gemini_results)} Gemini concepts...")
        for sid, concepts in gemini_results.items():
            # Find the row
            mask = merged["代號"] == sid
            if mask.any():
                idx = merged[mask].index[0]
                existing = merged.at[idx, "相關概念"]
                
                # Append or Set
                if pd.isna(existing) or existing is None or str(existing).strip() == "":
                    merged.at[idx, "相關概念"] = concepts
                else:
                    # Avoid duplicates if possible, but simple append for now
                    merged.at[idx, "相關概念"] = f"{existing};{concepts}"

    merged = add_concept_flag_columns(merged)

    # 5) 欄位順序
    col_order = [
        "代號",
        "名稱",
        "市場別",
        "產業別",          # This serves as '相關產業'
        "市值",
        "市值佔大盤比重",
        "ETF_0050_權重",
        "ETF_0056_權重",
        "ETF_00878_權重",
        "ETF_00919_權重",
        "主要業務",
        *CONCEPT_COLUMNS,
        "相關集團",
    ]

    for c in merged.columns:
        if c not in col_order and c not in [
            "市場別_TWSE", "產業別_TWSE", 
            "市場別_TPEX", "產業別_TPEX", 
            "市場別_EMG", "產業別_EMG",
            "市場別_PUB", "產業別_PUB",
            "上市日_TWSE"
        ]:
            # 排除已合併的原始欄位，保留其他可能的額外欄位
            col_order.append(c)

    merged = merged[col_order]

    # 6) 存檔
    merged.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print("\n=== 已完成 ===")
    print(f"輸出：{OUTPUT_CSV}")

    print("\n=== 最終欄位 ===")
    for col in merged.columns:
        print(col)

    print("\n=== Sample Row ===")
    if not merged.empty:
        print(merged.iloc[0])


if __name__ == "__main__":
    main()
