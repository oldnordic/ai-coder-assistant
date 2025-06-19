"""
Security Intelligence Service

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

"""
Security Intelligence Service - Track security breaches, CVEs, and patches.
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
import re

import httpx
from bs4 import BeautifulSoup
import feedparser

logger = logging.getLogger(__name__)


@dataclass
class SecurityVulnerability:
    """Security vulnerability information."""
    id: str  # CVE ID or unique identifier
    title: str
    description: str
    severity: str  # Critical, High, Medium, Low
    cvss_score: Optional[float] = None
    affected_products: List[str] = field(default_factory=list)
    affected_versions: List[str] = field(default_factory=list)
    published_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    references: List[str] = field(default_factory=list)
    patches: List[str] = field(default_factory=list)
    source: str = ""  # Source of the vulnerability
    tags: List[str] = field(default_factory=list)
    is_patched: bool = False
    patch_available: bool = False


@dataclass
class SecurityBreach:
    """Security breach information."""
    id: str
    title: str
    description: str
    company: str
    breach_date: Optional[datetime] = None
    discovered_date: Optional[datetime] = None
    affected_users: Optional[int] = None
    data_types: List[str] = field(default_factory=list)
    attack_vector: str = ""
    severity: str = "Unknown"
    source: str = ""
    references: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)


@dataclass
class SecurityPatch:
    """Security patch information."""
    id: str
    title: str
    description: str
    affected_products: List[str] = field(default_factory=list)
    patch_version: str = ""
    release_date: Optional[datetime] = None
    severity: str = "Unknown"
    source: str = ""
    download_url: str = ""
    installation_instructions: str = ""
    rollback_instructions: str = ""
    tested: bool = False
    applied: bool = False


@dataclass
class SecurityFeed:
    """Security feed configuration."""
    name: str
    url: str
    feed_type: str  # "rss", "atom", "api"
    enabled: bool = True
    last_fetch: Optional[datetime] = None
    fetch_interval: int = 3600  # seconds
    tags: List[str] = field(default_factory=list)


class SecurityIntelligenceService:
    """Main security intelligence service."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "security_intelligence_config.json"
        self.vulnerabilities: Dict[str, SecurityVulnerability] = {}
        self.breaches: Dict[str, SecurityBreach] = {}
        self.patches: Dict[str, SecurityPatch] = {}
        self.feeds: Dict[str, SecurityFeed] = {}
        self.training_data: List[Dict[str, Any]] = []
        
        self.load_config()
        self.load_data()
    
    def load_config(self):
        """Load configuration from file."""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                # Load feeds
                for feed_data in data.get("feeds", []):
                    feed = SecurityFeed(**feed_data)
                    self.feeds[feed.name] = feed
                    
        except Exception as e:
            logger.error(f"Error loading security intelligence config: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration with popular security feeds."""
        default_feeds = [
            SecurityFeed(
                name="NVD CVE Feed",
                url="https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss-analyzed.xml",
                feed_type="rss",
                tags=["cve", "vulnerability"]
            ),
            SecurityFeed(
                name="SecurityWeek",
                url="https://www.securityweek.com/feed/",
                feed_type="rss",
                tags=["breach", "security-news"]
            ),
            SecurityFeed(
                name="The Hacker News",
                url="https://feeds.feedburner.com/TheHackersNews",
                feed_type="rss",
                tags=["breach", "security-news"]
            ),
            SecurityFeed(
                name="CISA Alerts",
                url="https://www.cisa.gov/news-events/cybersecurity-advisories/feed",
                feed_type="rss",
                tags=["advisory", "government"]
            )
        ]
        
        for feed in default_feeds:
            self.feeds[feed.name] = feed
        
        self.save_config()
    
    def save_config(self):
        """Save configuration to file."""
        try:
            config_data = {
                "feeds": [feed.__dict__ for feed in self.feeds.values()]
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving security intelligence config: {e}")
    
    def load_data(self):
        """Load cached security data."""
        data_files = {
            "vulnerabilities": "security_vulnerabilities.json",
            "breaches": "security_breaches.json",
            "patches": "security_patches.json",
            "training_data": "security_training_data.json"
        }
        
        for data_type, filename in data_files.items():
            try:
                file_path = Path(filename)
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    if data_type == "vulnerabilities":
                        for vuln_data in data:
                            vuln = SecurityVulnerability(**vuln_data)
                            self.vulnerabilities[vuln.id] = vuln
                    elif data_type == "breaches":
                        for breach_data in data:
                            breach = SecurityBreach(**breach_data)
                            self.breaches[breach.id] = breach
                    elif data_type == "patches":
                        for patch_data in data:
                            patch = SecurityPatch(**patch_data)
                            self.patches[patch.id] = patch
                    elif data_type == "training_data":
                        self.training_data = data
                        
            except Exception as e:
                logger.error(f"Error loading {data_type}: {e}")
    
    def save_data(self):
        """Save security data to files."""
        try:
            # Save vulnerabilities
            with open("security_vulnerabilities.json", 'w') as f:
                json.dump([vuln.__dict__ for vuln in self.vulnerabilities.values()], f, indent=2, default=str)
            
            # Save breaches
            with open("security_breaches.json", 'w') as f:
                json.dump([breach.__dict__ for breach in self.breaches.values()], f, indent=2, default=str)
            
            # Save patches
            with open("security_patches.json", 'w') as f:
                json.dump([patch.__dict__ for patch in self.patches.values()], f, indent=2, default=str)
            
            # Save training data
            with open("security_training_data.json", 'w') as f:
                json.dump(self.training_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving security data: {e}")
    
    async def fetch_security_feeds(self):
        """Fetch security data from configured feeds."""
        async with httpx.AsyncClient() as client:
            for feed_name, feed in self.feeds.items():
                if not feed.enabled:
                    continue
                
                try:
                    if feed.feed_type == "rss":
                        await self._fetch_rss_feed(client, feed)
                    elif feed.feed_type == "api":
                        await self._fetch_api_feed(client, feed)
                    
                    feed.last_fetch = datetime.now()
                    
                except Exception as e:
                    logger.error(f"Error fetching feed {feed_name}: {e}")
        
        self.save_config()
        self.save_data()
    
    async def _fetch_rss_feed(self, client: httpx.AsyncClient, feed: SecurityFeed):
        """Fetch data from RSS feed."""
        try:
            response = await client.get(feed.url)
            response.raise_for_status()
            
            # Parse RSS feed
            parsed_feed = feedparser.parse(response.text)
            
            for entry in parsed_feed.entries:
                if "cve" in feed.tags:
                    await self._process_cve_entry(entry, feed)
                elif "breach" in feed.tags:
                    await self._process_breach_entry(entry, feed)
                elif "advisory" in feed.tags:
                    await self._process_advisory_entry(entry, feed)
                    
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed.name}: {e}")
    
    async def _fetch_api_feed(self, client: httpx.AsyncClient, feed: SecurityFeed):
        """Fetch data from API feed."""
        try:
            response = await client.get(feed.url)
            response.raise_for_status()
            
            data = response.json()
            
            # Process API data based on feed type
            if "cve" in feed.tags:
                await self._process_cve_api_data(data, feed)
            elif "breach" in feed.tags:
                await self._process_breach_api_data(data, feed)
                
        except Exception as e:
            logger.error(f"Error fetching API feed {feed.name}: {e}")
    
    async def _process_cve_entry(self, entry, feed: SecurityFeed):
        """Process CVE entry from RSS feed."""
        try:
            # Extract CVE ID
            cve_id = self._extract_cve_id(entry.title or entry.description)
            if not cve_id:
                return
            
            # Check if already exists
            if cve_id in self.vulnerabilities:
                return
            
            # Create vulnerability object
            vuln = SecurityVulnerability(
                id=cve_id,
                title=entry.title or "Unknown",
                description=entry.description or "",
                severity=self._extract_severity(entry.title or entry.description),
                published_date=datetime.now(),
                source=feed.name,
                tags=feed.tags.copy()
            )
            
            self.vulnerabilities[cve_id] = vuln
            
            # Add to training data
            self._add_to_training_data(vuln)
            
        except Exception as e:
            logger.error(f"Error processing CVE entry: {e}")
    
    async def _process_breach_entry(self, entry, feed: SecurityFeed):
        """Process breach entry from RSS feed."""
        try:
            breach_id = f"breach_{len(self.breaches) + 1}"
            
            # Create breach object
            breach = SecurityBreach(
                id=breach_id,
                title=entry.title or "Unknown",
                description=entry.description or "",
                company=self._extract_company(entry.title or entry.description),
                breach_date=datetime.now(),
                source=feed.name,
                tags=feed.tags.copy()
            )
            
            self.breaches[breach_id] = breach
            
            # Add to training data
            self._add_to_training_data(breach)
            
        except Exception as e:
            logger.error(f"Error processing breach entry: {e}")
    
    async def _process_advisory_entry(self, entry, feed: SecurityFeed):
        """Process advisory entry from RSS feed."""
        try:
            advisory_id = f"advisory_{len(self.patches) + 1}"
            
            # Create patch object
            patch = SecurityPatch(
                id=advisory_id,
                title=entry.title or "Unknown",
                description=entry.description or "",
                release_date=datetime.now(),
                source=feed.name,
                tags=feed.tags.copy()
            )
            
            self.patches[advisory_id] = patch
            
            # Add to training data
            self._add_to_training_data(patch)
            
        except Exception as e:
            logger.error(f"Error processing advisory entry: {e}")
    
    def _extract_cve_id(self, text: str) -> Optional[str]:
        """Extract CVE ID from text."""
        cve_pattern = r'CVE-\d{4}-\d{4,7}'
        match = re.search(cve_pattern, text, re.IGNORECASE)
        return match.group() if match else None
    
    def _extract_severity(self, text: str) -> str:
        """Extract severity from text."""
        text_lower = text.lower()
        if any(word in text_lower for word in ["critical", "severe"]):
            return "Critical"
        elif "high" in text_lower:
            return "High"
        elif "medium" in text_lower:
            return "Medium"
        elif "low" in text_lower:
            return "Low"
        return "Unknown"
    
    def _extract_company(self, text: str) -> str:
        """Extract company name from text."""
        # Simple extraction - could be enhanced with NLP
        words = text.split()
        if len(words) > 0:
            return words[0]
        return "Unknown"
    
    def _add_to_training_data(self, item):
        """Add security item to training data."""
        training_item = {
            "type": type(item).__name__,
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "severity": getattr(item, 'severity', 'Unknown'),
            "source": item.source,
            "tags": item.tags,
            "timestamp": datetime.now().isoformat()
        }
        
        self.training_data.append(training_item)
    
    def get_vulnerabilities(self, severity: Optional[str] = None, limit: int = 100) -> List[SecurityVulnerability]:
        """Get vulnerabilities with optional filtering."""
        vulns = list(self.vulnerabilities.values())
        
        if severity:
            vulns = [v for v in vulns if v.severity.lower() == severity.lower()]
        
        # Sort by published date (newest first)
        vulns.sort(key=lambda x: x.published_date or datetime.min, reverse=True)
        
        return vulns[:limit]
    
    def get_breaches(self, limit: int = 100) -> List[SecurityBreach]:
        """Get security breaches."""
        breaches = list(self.breaches.values())
        breaches.sort(key=lambda x: x.breach_date or datetime.min, reverse=True)
        return breaches[:limit]
    
    def get_patches(self, limit: int = 100) -> List[SecurityPatch]:
        """Get security patches."""
        patches = list(self.patches.values())
        patches.sort(key=lambda x: x.release_date or datetime.min, reverse=True)
        return patches[:limit]
    
    def get_training_data(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get training data for AI models."""
        return self.training_data[-limit:]
    
    def search_vulnerabilities(self, query: str) -> List[SecurityVulnerability]:
        """Search vulnerabilities by query."""
        query_lower = query.lower()
        results = []
        
        for vuln in self.vulnerabilities.values():
            if (query_lower in vuln.title.lower() or 
                query_lower in vuln.description.lower() or
                query_lower in vuln.id.lower()):
                results.append(vuln)
        
        return results
    
    def add_feed(self, feed: SecurityFeed):
        """Add a new security feed."""
        self.feeds[feed.name] = feed
        self.save_config()
    
    def remove_feed(self, feed_name: str):
        """Remove a security feed."""
        if feed_name in self.feeds:
            del self.feeds[feed_name]
            self.save_config()
    
    def get_feeds(self) -> List[SecurityFeed]:
        """Get all configured feeds."""
        return list(self.feeds.values())
    
    def mark_patch_applied(self, patch_id: str):
        """Mark a patch as applied."""
        if patch_id in self.patches:
            self.patches[patch_id].applied = True
            self.save_data()
    
    def mark_vulnerability_patched(self, vuln_id: str):
        """Mark a vulnerability as patched."""
        if vuln_id in self.vulnerabilities:
            self.vulnerabilities[vuln_id].is_patched = True
            self.save_data()


# Global instance
security_intelligence_service = SecurityIntelligenceService() 