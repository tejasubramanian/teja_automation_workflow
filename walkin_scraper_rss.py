#!/usr/bin/env python3
"""
RSS-based Job Scraper for GitHub Actions
Uses official RSS feeds from job boards (no blocking issues!)
Scrapes BOTH walk-in interviews AND regular job postings
From: Naukri, Indeed, Stack Overflow
Saves to CSV and sends Telegram alerts
"""

import os
import csv
import requests
import feedparser
from datetime import datetime
import logging
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TARGET_KEYWORDS = ["DevOps", "SRE", "Cloud Engineer", "Infrastructure", "AWS", "Kubernetes", "Azure", "CI/CD"]
LOCATION = "Hyderabad"

# RSS Feed URLs (official, allowed by job boards)
RSS_FEEDS = {
    'Naukri': 'https://www.naukri.com/rss/jobs-devops-hyderabad',
    'Indeed': 'https://www.indeed.com/rss?q=DevOps&l=Hyderabad&jt=permanent',
    'StackOverflow': 'https://stackoverflow.com/jobs/feed?q=DevOps&l=Hyderabad'
}

class RSSJobScraper:
    def __init__(self):
        self.walkin_jobs = []
        self.regular_jobs = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    def is_walkin(self, title, description):
        """Check if job is a walk-in interview"""
        walkin_keywords = ["walk-in", "walk in", "without interview", "same day", "urgent", "immediate"]
        combined_text = f"{title} {description}".lower()
        return any(kw in combined_text for kw in walkin_keywords)
    
    def is_relevant(self, title, description):
        """Check if job matches target keywords"""
        combined_text = f"{title} {description}".lower()
        return any(kw.lower() in combined_text for kw in TARGET_KEYWORDS)
    
    def scrape_naukri_rss(self):
        """Scrape Naukri via RSS feed"""
        try:
            logger.info("🔍 Scraping Naukri RSS...")
            
            feed = feedparser.parse(RSS_FEEDS['Naukri'])
            
            if feed.bozo:
                logger.warning(f"⚠️ Naukri RSS parsing warning: {feed.bozo_exception}")
            
            for entry in feed.entries[:50]:
                try:
                    title = entry.get('title', 'Unknown')
                    description = entry.get('description', '')
                    link = entry.get('link', '')
                    published = entry.get('published', datetime.now().isoformat())
                    
                    # Clean up description (remove HTML tags)
                    description = description.replace('<br/>', ' ').replace('<br>', ' ')
                    
                    if not self.is_relevant(title, description):
                        continue
                    
                    # Extract company from description or title
                    company = "Naukri Job"
                    if 'Naukri' in title:
                        company = title.split('-')[0].strip() if '-' in title else company
                    
                    job_type = "Walk-in" if self.is_walkin(title, description) else "Regular"
                    
                    job_data = {
                        'type': job_type,
                        'source': 'Naukri',
                        'company': company,
                        'role': title,
                        'location': LOCATION,
                        'posted_date': published[:10],  # Date only
                        'url': link,
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    if job_type == "Walk-in":
                        self.walkin_jobs.append(job_data)
                    else:
                        self.regular_jobs.append(job_data)
                    
                    logger.info(f"✅ Found [{job_type}]: {company} - {title[:50]}")
                
                except Exception as e:
                    logger.debug(f"Error parsing Naukri entry: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ Naukri RSS scraping failed: {e}")
    
    def scrape_indeed_rss(self):
        """Scrape Indeed via RSS feed"""
        try:
            logger.info("🔍 Scraping Indeed RSS...")
            
            feed = feedparser.parse(RSS_FEEDS['Indeed'])
            
            if feed.bozo:
                logger.warning(f"⚠️ Indeed RSS parsing warning: {feed.bozo_exception}")
            
            for entry in feed.entries[:50]:
                try:
                    title = entry.get('title', 'Unknown')
                    description = entry.get('description', '')
                    link = entry.get('link', '')
                    published = entry.get('published', datetime.now().isoformat())
                    
                    # Clean up description
                    description = description.replace('<br/>', ' ').replace('<br>', ' ')
                    
                    if not self.is_relevant(title, description):
                        continue
                    
                    # Extract company
                    company = "Indeed Job"
                    if 'company:' in description.lower():
                        company_part = description.lower().split('company:')[1].split('<')[0].strip()
                        company = company_part if company_part else company
                    
                    job_type = "Walk-in" if self.is_walkin(title, description) else "Regular"
                    
                    job_data = {
                        'type': job_type,
                        'source': 'Indeed',
                        'company': company,
                        'role': title,
                        'location': LOCATION,
                        'posted_date': published[:10],
                        'url': link,
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    if job_type == "Walk-in":
                        self.walkin_jobs.append(job_data)
                    else:
                        self.regular_jobs.append(job_data)
                    
                    logger.info(f"✅ Found [{job_type}]: {company} - {title[:50]}")
                
                except Exception as e:
                    logger.debug(f"Error parsing Indeed entry: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ Indeed RSS scraping failed: {e}")
    
    def scrape_stackoverflow_rss(self):
        """Scrape Stack Overflow via RSS feed"""
        try:
            logger.info("🔍 Scraping Stack Overflow RSS...")
            
            feed = feedparser.parse(RSS_FEEDS['StackOverflow'])
            
            if feed.bozo:
                logger.warning(f"⚠️ Stack Overflow RSS parsing warning: {feed.bozo_exception}")
            
            for entry in feed.entries[:50]:
                try:
                    title = entry.get('title', 'Unknown')
                    description = entry.get('description', '')
                    link = entry.get('link', '')
                    published = entry.get('published', datetime.now().isoformat())
                    
                    # Clean up description
                    description = description.replace('<br/>', ' ').replace('<br>', ' ')
                    
                    if not self.is_relevant(title, description):
                        continue
                    
                    # Extract company
                    company = "StackOverflow Job"
                    if 'company' in description.lower():
                        parts = description.lower().split('company')[1]
                        company_part = parts.split('<')[0].strip().replace(':', '').strip()
                        company = company_part if company_part else company
                    
                    job_type = "Regular"  # Stack Overflow rarely has walk-ins
                    
                    job_data = {
                        'type': job_type,
                        'source': 'StackOverflow',
                        'company': company,
                        'role': title,
                        'location': LOCATION,
                        'posted_date': published[:10],
                        'url': link,
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    self.regular_jobs.append(job_data)
                    
                    logger.info(f"✅ Found [Regular]: {company} - {title[:50]}")
                
                except Exception as e:
                    logger.debug(f"Error parsing Stack Overflow entry: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ Stack Overflow RSS scraping failed: {e}")
    
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
                            'date': job['posted_date'],
                            'company': job['company'],
                            'role': job['role'],
                            'location': job['location'],
                            'source': job['source'],
                            'url': job['url']
                        })
                logger.info(f"✅ Saved {len(self.walkin_jobs)} walk-ins to walkins.csv")
            else:
                # Create empty CSV if no walk-ins
                with open('walkins.csv', 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['type', 'date', 'company', 'role', 'location', 'source', 'url'])
                logger.info("✅ Created empty walkins.csv")
            
            # Save regular jobs
            if self.regular_jobs:
                with open('regular_jobs.csv', 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['type', 'date', 'company', 'role', 'location', 'source', 'url'])
                    writer.writeheader()
                    for job in self.regular_jobs:
                        writer.writerow({
                            'type': job['type'],
                            'date': job['posted_date'],
                            'company': job['company'],
                            'role': job['role'],
                            'location': job['location'],
                            'source': job['source'],
                            'url': job['url']
                        })
                logger.info(f"✅ Saved {len(self.regular_jobs)} regular jobs to regular_jobs.csv")
            else:
                # Create empty CSV if no regular jobs
                with open('regular_jobs.csv', 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['type', 'date', 'company', 'role', 'location', 'source', 'url'])
                logger.info("✅ Created empty regular_jobs.csv")
        
        except Exception as e:
            logger.error(f"❌ Failed to save to CSV: {e}")
    
    def send_telegram_alerts(self):
        """Send Telegram alerts for new jobs"""
        if not self.telegram_token or not self.telegram_chat_id:
            logger.warning("Telegram not configured, skipping alerts")
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            total_jobs = len(self.walkin_jobs) + len(self.regular_jobs)
            
            if total_jobs == 0:
                message = "📋 Job Scraper Ran\n\nNo new jobs found today. Try again tomorrow!"
                payload = {
                    'chat_id': self.telegram_chat_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                requests.post(url, json=payload, timeout=10)
                logger.info("✅ No jobs alert sent")
                return
            
            # Alert for walk-ins (URGENT)
            if self.walkin_jobs:
                message = f"🚨 *URGENT: NEW WALK-IN INTERVIEWS* 🚨\n\nFound {len(self.walkin_jobs)} new walk-in opportunities!\n\n"
                for job in self.walkin_jobs[:5]:
                    message += f"🏢 {job['company']}\n📌 {job['role']}\n🔗 {job['url']}\n\n"
                
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
                message = f"📋 *NEW REGULAR JOB POSTINGS*\n\nFound {len(self.regular_jobs)} new job opportunities!\n\n"
                for job in self.regular_jobs[:5]:
                    message += f"🏢 {job['company']}\n📌 {job['role']}\n🔗 {job['url']}\n\n"
                
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
        """Execute all RSS scrapers"""
        logger.info("\n🚀 Starting RSS-based Job Scraper...")
        logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n")
        
        self.scrape_naukri_rss()
        self.scrape_indeed_rss()
        self.scrape_stackoverflow_rss()
        
        self.remove_duplicates()
        self.save_to_csv()
        self.send_telegram_alerts()
        
        logger.info(f"\n✅ Scraping complete!")
        logger.info(f"   Walk-in jobs: {len(self.walkin_jobs)}")
        logger.info(f"   Regular jobs: {len(self.regular_jobs)}")
        logger.info(f"   Total: {len(self.walkin_jobs) + len(self.regular_jobs)} jobs found")


if __name__ == "__main__":
    scraper = RSSJobScraper()
    scraper.run()
    
    print("\n" + "="*60)
    print("JOB SCRAPING SUMMARY (RSS-based)")
    print("="*60)
    print(f"\n🚨 WALK-IN INTERVIEWS: {len(scraper.walkin_jobs)}")
    for job in scraper.walkin_jobs[:5]:
        print(f"  🏢 {job['company']} - {job['role']}")
    
    print(f"\n📋 REGULAR JOBS: {len(scraper.regular_jobs)}")
    for job in scraper.regular_jobs[:5]:
        print(f"  🏢 {job['company']} - {job['role']}")
