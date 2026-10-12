#!/usr/bin/env python3
"""
Walk-in Interview Scraper for GitHub Actions
Scrapes walk-ins from Naukri, LinkedIn, Indeed
Writes directly to Google Sheets
Sends Telegram alerts
No file storage needed - everything via APIs
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TARGET_KEYWORDS = ["DevOps", "SRE", "Cloud Engineer", "Infrastructure", "AWS", "Kubernetes", "Azure"]
LOCATION = "Hyderabad"
MIN_EXPERIENCE = 3

class WalkinScraper:
    def __init__(self):
        self.walkins = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.google_sheet_id = os.getenv('GOOGLE_SHEET_ID')
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Initialize Google Sheets API
        self.sheets_service = self._init_google_sheets()
    
    def _init_google_sheets(self):
        """Initialize Google Sheets API using service account"""
        try:
            creds_json = os.getenv('GOOGLE_CREDENTIALS')
            if not creds_json:
                logger.warning("GOOGLE_CREDENTIALS not set")
                return None
            
            creds_dict = json.loads(creds_json)
            creds = Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            service = build('sheets', 'v4', credentials=creds)
            return service
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            return None
    
    def scrape_naukri(self):
        """Scrape Naukri walk-in interviews"""
        try:
            logger.info("🔍 Scraping Naukri...")
            url = "https://www.naukri.com/walk-in-interview-jobs"
            params = {
                'locations': LOCATION,
                'exp': f'{MIN_EXPERIENCE}-99'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_cards = soup.find_all('article', class_='jobTuple')
            
            for card in job_cards[:15]:
                try:
                    title_elem = card.find('a', class_='jobTitle')
                    company_elem = card.find('a', class_='companyName')
                    
                    if not title_elem or not company_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    
                    if any(keyword.lower() in title.lower() for keyword in TARGET_KEYWORDS):
                        location_elem = card.find('span', class_='jobLocation')
                        location = location_elem.text.strip() if location_elem else LOCATION
                        
                        date_elem = card.find('span', class_='jobPostedDate')
                        posted_date = date_elem.text.strip() if date_elem else "Today"
                        
                        url_elem = card.find('a', class_='jobTitle')
                        job_url = url_elem['href'] if url_elem and url_elem.get('href') else "N/A"
                        
                        walkin_data = {
                            'source': 'Naukri',
                            'company': company,
                            'role': title,
                            'location': location,
                            'posted_date': posted_date,
                            'url': job_url,
                            'scraped_at': datetime.now().isoformat()
                        }
                        self.walkins.append(walkin_data)
                        logger.info(f"✅ Found: {company} - {title}")
                except Exception as e:
                    logger.debug(f"Error parsing card: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Naukri scraping failed: {e}")
    
    def scrape_linkedin(self):
        """Scrape LinkedIn walk-in opportunities"""
        try:
            logger.info("🔍 Scraping LinkedIn...")
            search_query = "walk-in interview DevOps Hyderabad"
            url = "https://www.linkedin.com/jobs/search"
            params = {
                'keywords': search_query,
                'location': 'Hyderabad',
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_listings = soup.find_all('div', class_='base-card')
            
            for job in job_listings[:10]:
                try:
                    title_elem = job.find('h3', class_='base-search-card__title')
                    company_elem = job.find('a', class_='hidden-nested-link')
                    
                    if not title_elem or not company_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    
                    if any(keyword.lower() in title.lower() for keyword in TARGET_KEYWORDS):
                        url_elem = job.find('a', class_='base-card__full-link')
                        job_url = url_elem['href'] if url_elem else "N/A"
                        
                        walkin_data = {
                            'source': 'LinkedIn',
                            'company': company,
                            'role': title,
                            'location': LOCATION,
                            'posted_date': 'Recent',
                            'url': job_url,
                            'scraped_at': datetime.now().isoformat()
                        }
                        self.walkins.append(walkin_data)
                        logger.info(f"✅ Found: {company} - {title}")
                except Exception as e:
                    logger.debug(f"Error parsing LinkedIn job: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ LinkedIn scraping failed: {e}")
    
    def scrape_indeed(self):
        """Scrape Indeed India for walk-in opportunities"""
        try:
            logger.info("🔍 Scraping Indeed...")
            url = "https://www.indeed.co.in/jobs"
            params = {
                'q': 'DevOps "walk-in interview"',
                'l': LOCATION,
                'jt': 'fulltime'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            for card in job_cards[:12]:
                try:
                    title_elem = card.find('h2', class_='jobTitle')
                    company_elem = card.find('span', class_='companyName')
                    
                    if not title_elem or not company_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    
                    if any(keyword.lower() in title.lower() for keyword in TARGET_KEYWORDS):
                        link = card.find('a', class_='jcs-JobTitle')
                        url_path = link['href'] if link else ""
                        full_url = f"https://www.indeed.co.in{url_path}"
                        
                        walkin_data = {
                            'source': 'Indeed',
                            'company': company,
                            'role': title,
                            'location': LOCATION,
                            'posted_date': 'Recent',
                            'url': full_url,
                            'scraped_at': datetime.now().isoformat()
                        }
                        self.walkins.append(walkin_data)
                        logger.info(f"✅ Found: {company} - {title}")
                except Exception as e:
                    logger.debug(f"Error parsing Indeed job: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Indeed scraping failed: {e}")
    
    def remove_duplicates(self):
        """Remove duplicate entries by company + role"""
        unique = {}
        for walkin in self.walkins:
            key = f"{walkin['company'].lower()}_{walkin['role'].lower()}"
            if key not in unique:
                unique[key] = walkin
        self.walkins = list(unique.values())
        logger.info(f"📊 Found {len(self.walkins)} unique walk-ins")
    
    def update_google_sheets(self):
        """Add walk-ins to Google Sheets"""
        if not self.sheets_service or not self.google_sheet_id:
            logger.warning("Google Sheets not configured, skipping update")
            return
        
        try:
            # Prepare data for Google Sheets
            values = []
            for walkin in self.walkins:
                row = [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Date Scraped
                    walkin['company'],
                    walkin['role'],
                    walkin['location'],
                    walkin['url'],
                    walkin['source'],
                    "N",  # Applied (Y/N)
                    "",   # Interview Date
                    "Pending",  # Status
                    ""    # Notes
                ]
                values.append(row)
            
            if not values:
                logger.info("No new walk-ins to add")
                return
            
            # Add to Google Sheets
            body = {'values': values}
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.google_sheet_id,
                range='Walk-ins!A:J',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.info(f"✅ Added {len(values)} rows to Google Sheets")
        except Exception as e:
            logger.error(f"❌ Failed to update Google Sheets: {e}")
    
    def send_telegram_alerts(self):
        """Send Telegram alerts for new walk-ins"""
        if not self.telegram_token or not self.telegram_chat_id:
            logger.warning("Telegram not configured, skipping alerts")
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            for walkin in self.walkins[:5]:  # Send top 5
                message = f"""🔔 *NEW WALK-IN ALERT*

🏢 *Company:* {walkin['company']}
📌 *Role:* {walkin['role']}
📍 *Location:* {walkin['location']}
📅 *Posted:* {walkin['posted_date']}

🔗 *Apply:* {walkin['url']}
📰 *Source:* {walkin['source']}"""
                
                payload = {
                    'chat_id': self.telegram_chat_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"✅ Telegram alert sent for: {walkin['company']}")
                else:
                    logger.error(f"❌ Telegram alert failed: {response.text}")
        
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram alerts: {e}")
    
    def run(self):
        """Execute all scrapers"""
        logger.info("\n🚀 Starting Walk-in Interview Scraper...")
        logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n")
        
        self.scrape_naukri()
        self.scrape_linkedin()
        self.scrape_indeed()
        
        self.remove_duplicates()
        self.update_google_sheets()
        self.send_telegram_alerts()
        
        logger.info(f"\n✅ Scraping complete! Total: {len(self.walkins)} walk-ins found")
        
        # Also save to walkins.json for reference
        with open('walkins.json', 'w', encoding='utf-8') as f:
            json.dump(self.walkins, f, indent=2, ensure_ascii=False)
        
        return self.walkins


if __name__ == "__main__":
    scraper = WalkinScraper()
    walkins = scraper.run()
    
    print("\n" + "="*60)
    print("WALK-IN OPPORTUNITIES SUMMARY")
    print("="*60)
    for walkin in walkins[:5]:
        print(f"\n🏢 {walkin['company']}")
        print(f"   Role: {walkin['role']}")
        print(f"   Location: {walkin['location']}")
        print(f"   Source: {walkin['source']}")
        print(f"   Apply: {walkin['url']}")
