#!/usr/bin/env python3
"""
EXPANDED Walk-in & Job Postings Scraper for GitHub Actions
Scrapes BOTH:
1. Walk-in interviews (time-sensitive)
2. Regular job postings (standard applications)

From: Naukri, Indeed, Times Jobs, Stack Overflow
Separates into 2 categories for easy tracking
Sends Telegram alerts for both
"""

import os
import json
import requests
import csv
from bs4 import BeautifulSoup
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TARGET_KEYWORDS = ["DevOps", "SRE", "Cloud Engineer", "Infrastructure", "AWS", "Kubernetes", "Azure", "CI/CD"]
LOCATION = "Hyderabad"
MIN_EXPERIENCE = 3

class ExpandedJobScraper:
    def __init__(self):
        self.walkin_jobs = []
        self.regular_jobs = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    def is_walkin(self, title, location_text):
        """Check if job is a walk-in interview"""
        walkin_keywords = ["walk-in", "walk in", "without interview", "same day", "urgent"]
        title_lower = title.lower()
        location_lower = location_text.lower() if location_text else ""
        
        return any(kw in title_lower or kw in location_lower for kw in walkin_keywords)
    
    def scrape_naukri(self):
        """Scrape Naukri for ALL DevOps jobs"""
        try:
            logger.info("🔍 Scraping Naukri (All jobs)...")
            url = "https://www.naukri.com/search"
            params = {
                'k': 'DevOps',
                'l': LOCATION,
                'e': f'{MIN_EXPERIENCE}-99'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_cards = soup.find_all('article', class_='jobTuple')
            
            for card in job_cards[:30]:  # Increased limit
                try:
                    title_elem = card.find('a', class_='jobTitle')
                    company_elem = card.find('a', class_='companyName')
                    
                    if not title_elem or not company_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    
                    # Check if any keyword matches
                    if not any(kw.lower() in title.lower() for kw in TARGET_KEYWORDS):
                        continue
                    
                    location_elem = card.find('span', class_='jobLocation')
                    location = location_elem.text.strip() if location_elem else LOCATION
                    
                    date_elem = card.find('span', class_='jobPostedDate')
                    posted_date = date_elem.text.strip() if date_elem else "Today"
                    
                    url_elem = card.find('a', class_='jobTitle')
                    job_url = url_elem['href'] if url_elem and url_elem.get('href') else "N/A"
                    
                    job_type = "Walk-in" if self.is_walkin(title, posted_date) else "Regular"
                    
                    job_data = {
                        'type': job_type,
                        'source': 'Naukri',
                        'company': company,
                        'role': title,
                        'location': location,
                        'posted_date': posted_date,
                        'url': job_url,
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    if job_type == "Walk-in":
                        self.walkin_jobs.append(job_data)
                    else:
                        self.regular_jobs.append(job_data)
                    
                    logger.info(f"✅ Found [{job_type}]: {company} - {title}")
                except Exception as e:
                    logger.debug(f"Error parsing card: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Naukri scraping failed: {e}")
    
    def scrape_indeed(self):
        """Scrape Indeed India for ALL jobs"""
        try:
            logger.info("🔍 Scraping Indeed (All jobs)...")
            url = "https://www.indeed.co.in/jobs"
            params = {
                'q': 'DevOps',
                'l': LOCATION,
                'jt': 'fulltime'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            for card in job_cards[:30]:
                try:
                    title_elem = card.find('h2', class_='jobTitle')
                    company_elem = card.find('span', class_='companyName')
                    
                    if not title_elem or not company_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    
                    if not any(kw.lower() in title.lower() for kw in TARGET_KEYWORDS):
                        continue
                    
                    link = card.find('a', class_='jcs-JobTitle')
                    url_path = link['href'] if link else ""
                    job_url = f"https://www.indeed.co.in{url_path}"
                    
                    job_type = "Walk-in" if self.is_walkin(title, "") else "Regular"
                    
                    job_data = {
                        'type': job_type,
                        'source': 'Indeed',
                        'company': company,
                        'role': title,
                        'location': LOCATION,
                        'posted_date': 'Recent',
                        'url': job_url,
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    if job_type == "Walk-in":
                        self.walkin_jobs.append(job_data)
                    else:
                        self.regular_jobs.append(job_data)
                    
                    logger.info(f"✅ Found [{job_type}]: {company} - {title}")
                except Exception as e:
                    logger.debug(f"Error parsing Indeed job: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Indeed scraping failed: {e}")
    
    def scrape_times_jobs(self):
        """Scrape Times Jobs Hyderabad"""
        try:
            logger.info("🔍 Scraping Times Jobs...")
            url = "https://www.timesjobs.com/candidate/job-search.html"
            params = {
                'searchType': 'personalizedSearch',
                'searchText': 'DevOps',
                'cboWorkExp99': 'Y',
                'limit': '0'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_listings = soup.find_all('li', class_='clearfix')
            
            for job in job_listings[:30]:
                try:
                    title_elem = job.find('a', class_='jobTitle')
                    company_elem = job.find('a', class_='companyName')
                    
                    if not title_elem or not company_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    
                    if not any(kw.lower() in title.lower() for kw in TARGET_KEYWORDS):
                        continue
                    
                    job_type = "Walk-in" if self.is_walkin(title, "") else "Regular"
                    
                    job_data = {
                        'type': job_type,
                        'source': 'TimesJobs',
                        'company': company,
                        'role': title,
                        'location': LOCATION,
                        'posted_date': 'Recent',
                        'url': title_elem['href'],
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    if job_type == "Walk-in":
                        self.walkin_jobs.append(job_data)
                    else:
                        self.regular_jobs.append(job_data)
                    
                    logger.info(f"✅ Found [{job_type}]: {company} - {title}")
                except Exception as e:
                    logger.debug(f"Error parsing Times Jobs: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Times Jobs scraping failed: {e}")
    
    def scrape_stackoverflow(self):
        """Scrape Stack Overflow for tech jobs"""
        try:
            logger.info("🔍 Scraping Stack Overflow Jobs...")
            url = "https://stackoverflow.com/jobs"
            params = {
                'q': 'DevOps',
                'l': LOCATION
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_items = soup.find_all('div', class_='s-job-card')
            
            for job in job_items[:20]:
                try:
                    title_elem = job.find('h2', class_='mb0')
                    company_elem = job.find('span', class_='fc-black-500')
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    company = company_elem.text.strip() if company_elem else "Unknown"
                    
                    if not any(kw.lower() in title.lower() for kw in TARGET_KEYWORDS):
                        continue
                    
                    link = job.find('a')
                    job_url = f"https://stackoverflow.com{link['href']}" if link else "N/A"
                    
                    job_data = {
                        'type': 'Regular',
                        'source': 'StackOverflow',
                        'company': company,
                        'role': title,
                        'location': LOCATION,
                        'posted_date': 'Recent',
                        'url': job_url,
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    self.regular_jobs.append(job_data)
                    logger.info(f"✅ Found [Regular]: {company} - {title}")
                except Exception as e:
                    logger.debug(f"Error parsing Stack Overflow job: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Stack Overflow scraping failed: {e}")
    
    def remove_duplicates(self):
        """Remove duplicate entries"""
        def unique_jobs(jobs):
            unique = {}
            for job in jobs:
                key = f"{job['company'].lower()}_{job['role'].lower()}"
                if key not in unique:
                    unique[key] = job
            return list(unique.values())
        
        self.walkin_jobs = unique_jobs(self.walkin_jobs)
        self.regular_jobs = unique_jobs(self.regular_jobs)
        
        logger.info(f"📊 Found {len(self.walkin_jobs)} unique walk-ins, {len(self.regular_jobs)} unique regular jobs")
    
    def save_to_csv(self):
        """Save jobs to CSV files"""
        try:
            # Save walk-ins
            if self.walkin_jobs:
                with open('walkins.csv', 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['type', 'date', 'company', 'role', 'location', 'source', 'url'])
                    writer.writeheader()
                    for job in self.walkin_jobs:
                        writer.writerow({
                            'type': job['type'],
                            'date': job['scraped_at'],
                            'company': job['company'],
                            'role': job['role'],
                            'location': job['location'],
                            'source': job['source'],
                            'url': job['url']
                        })
                logger.info(f"✅ Saved {len(self.walkin_jobs)} walk-ins to walkins.csv")
            
            # Save regular jobs
            if self.regular_jobs:
                with open('regular_jobs.csv', 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['type', 'date', 'company', 'role', 'location', 'source', 'url'])
                    writer.writeheader()
                    for job in self.regular_jobs:
                        writer.writerow({
                            'type': job['type'],
                            'date': job['scraped_at'],
                            'company': job['company'],
                            'role': job['role'],
                            'location': job['location'],
                            'source': job['source'],
                            'url': job['url']
                        })
                logger.info(f"✅ Saved {len(self.regular_jobs)} regular jobs to regular_jobs.csv")
        
        except Exception as e:
            logger.error(f"❌ Failed to save to CSV: {e}")
    
    def send_telegram_alerts(self):
        """Send Telegram alerts for new jobs"""
        if not self.telegram_token or not self.telegram_chat_id:
            logger.warning("Telegram not configured, skipping alerts")
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            # Alert for walk-ins (URGENT)
            if self.walkin_jobs:
                message = f"""🚨 *URGENT: NEW WALK-IN INTERVIEWS* 🚨

Found {len(self.walkin_jobs)} new walk-in opportunities!

"""
                for job in self.walkin_jobs[:5]:
                    message += f"""🏢 {job['company']}
📌 {job['role']}
📍 {job['location']}
🔗 {job['url']}

"""
                
                if len(self.walkin_jobs) > 5:
                    message += f"\n... and {len(self.walkin_jobs) - 5} more! Check walkins.csv"
                
                payload = {
                    'chat_id': self.telegram_chat_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                
                requests.post(url, json=payload, timeout=10)
                logger.info(f"✅ Walk-in alerts sent for {len(self.walkin_jobs)} opportunities")
            
            # Alert for regular jobs
            if self.regular_jobs:
                message = f"""📋 *NEW REGULAR JOB POSTINGS*

Found {len(self.regular_jobs)} new job opportunities!

"""
                for job in self.regular_jobs[:5]:
                    message += f"""🏢 {job['company']}
📌 {job['role']}
📍 {job['location']}
🔗 {job['url']}

"""
                
                if len(self.regular_jobs) > 5:
                    message += f"\n... and {len(self.regular_jobs) - 5} more! Check regular_jobs.csv"
                
                payload = {
                    'chat_id': self.telegram_chat_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                
                requests.post(url, json=payload, timeout=10)
                logger.info(f"✅ Regular job alerts sent for {len(self.regular_jobs)} opportunities")
        
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram alerts: {e}")
    
    def run(self):
        """Execute all scrapers"""
        logger.info("\n🚀 Starting EXPANDED Job Scraper...")
        logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n")
        
        self.scrape_naukri()
        self.scrape_indeed()
        self.scrape_times_jobs()
        self.scrape_stackoverflow()
        
        self.remove_duplicates()
        self.save_to_csv()
        self.send_telegram_alerts()
        
        logger.info(f"\n✅ Scraping complete!")
        logger.info(f"   Walk-in jobs: {len(self.walkin_jobs)}")
        logger.info(f"   Regular jobs: {len(self.regular_jobs)}")
        logger.info(f"   Total: {len(self.walkin_jobs) + len(self.regular_jobs)} jobs found")


if __name__ == "__main__":
    scraper = ExpandedJobScraper()
    scraper.run()
    
    print("\n" + "="*60)
    print("JOB SCRAPING SUMMARY")
    print("="*60)
    print(f"\n🚨 WALK-IN INTERVIEWS: {len(scraper.walkin_jobs)}")
    for job in scraper.walkin_jobs[:5]:
        print(f"  🏢 {job['company']} - {job['role']}")
    
    print(f"\n📋 REGULAR JOBS: {len(scraper.regular_jobs)}")
    for job in scraper.regular_jobs[:5]:
        print(f"  🏢 {job['company']} - {job['role']}")
