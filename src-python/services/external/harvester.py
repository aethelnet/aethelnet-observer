"""
Universal Content Harvester

Fetches and cleans content from ANY public web source:
- Wikipedia / Wikis (MediaWiki, Fandom, etc.)
- Public Obsidian vaults (publish.obsidian.md)
- Anki shared decks
- Finance data pages
- Any public knowledge base

Key feature: Smart link filtering to remove CTAs, socials, and noise.

Usage:
    from services.external.harvester import ContentHarvester
    
    harvester = ContentHarvester()
    content = await harvester.fetch_and_clean("https://publish.obsidian.md/...")
"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
import re


@dataclass
class HarvestedContent:
    """Cleaned content from any web source."""
    url: str
    title: str
    content: str  # Cleaned text content
    content_type: str  # wiki, obsidian, anki, finance, generic
    internal_links: List[str]  # Links within same domain (useful)
    external_links: List[str]  # Links to other domains (filtered)
    images: List[str]
    code_blocks: List[str]
    headings: List[str]
    fetched_at: datetime
    word_count: int
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['fetched_at'] = self.fetched_at.isoformat()
        return d


class ContentHarvester:
    """
    Universal content harvester with smart link filtering.
    
    Removes:
    - Social media CTAs (twitter, facebook, etc.)
    - Donation/Patreon links
    - Newsletter signups
    - Comment sections
    - Navigation/footer links
    - Ads and tracking
    """
    
    # Domains to filter out from links (noise)
    BLOCKED_DOMAINS = {
        # Social
        'twitter.com', 'x.com', 'facebook.com', 'instagram.com',
        'linkedin.com', 'tiktok.com', 'youtube.com', 'reddit.com',
        'discord.com', 'discord.gg', 'telegram.me', 't.me',
        # Donation/Commerce
        'patreon.com', 'ko-fi.com', 'buymeacoffee.com', 'gumroad.com',
        'paypal.com', 'stripe.com', 'shopify.com', 'etsy.com',
        # Email/Newsletter
        'mailchimp.com', 'convertkit.com', 'substack.com',
        # Tracking
        'bit.ly', 'goo.gl', 'tinyurl.com', 't.co',
        # Ads
        'doubleclick.net', 'googlesyndication.com', 'adsense.com',
    }
    
    # URL patterns to filter (CTAs, tracking, etc.)
    BLOCKED_PATTERNS = [
        r'/share[?/]', r'/tweet[?/]', r'/pin[?/]',  # Social share
        r'/subscribe', r'/newsletter', r'/signup',   # CTAs
        r'/donate', r'/support', r'/sponsor',        # Donation CTAs
        r'/login', r'/register', r'/auth',           # Auth
        r'/cart', r'/checkout', r'/buy',             # Commerce
        r'\?utm_', r'\?ref=', r'\?source=',          # Tracking
        r'/comment', r'/reply', r'#comments',        # Comments
        r'/feed', r'/rss', r'/atom',                 # Feeds
        r'/tag/', r'/category/', r'/archive/',       # Navigation
    ]
    
    # CSS selectors to remove (noise elements)
    NOISE_SELECTORS = [
        '.sidebar', '.footer', '.header', '.nav', '.navigation',
        '.ads', '.ad', '.advertisement', '.sponsor',
        '.comments', '.comment-section', '.disqus',
        '.share', '.share-buttons', '.social',
        '.newsletter', '.subscribe', '.signup',
        '.cookie', '.cookie-banner', '.gdpr',
        '.popup', '.modal', '.overlay',
    ]
    
    def __init__(self, max_links: int = 20, cache_ttl_hours: int = 24):
        self.max_links = max_links
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, HarvestedContent] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(hours=cache_ttl_hours)
        self._blocked_patterns = [re.compile(p, re.IGNORECASE) for p in self.BLOCKED_PATTERNS]
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; AuraticHarvester/1.0; +https://github.com/ProphitEngine)'
            }
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    # ==========================================
    # MAIN FETCH METHOD
    # ==========================================
    
    async def fetch_and_clean(self, url: str) -> Optional[HarvestedContent]:
        """
        Fetch any URL and return cleaned content.
        
        Automatically detects content type and applies appropriate parsing.
        """
        # Check cache
        if url in self._cache:
            if datetime.now() - self._cache_time[url] < self._cache_ttl:
                return self._cache[url]
        
        session = await self._get_session()
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    return None
                
                html = await resp.text()
                content_type = self._detect_content_type(url, html)
                
                # Parse and clean
                content = self._parse_html(html, url, content_type)
                
                # Cache
                self._cache[url] = content
                self._cache_time[url] = datetime.now()
                
                return content
                
        except Exception as e:
            print(f"Harvest error for {url}: {e}")
            return None
    
    def _detect_content_type(self, url: str, html: str) -> str:
        """Detect what type of content this is."""
        domain = urlparse(url).netloc.lower()
        
        # Obsidian Publish
        if 'obsidian.md' in domain or 'obsidian-publish' in html:
            return 'obsidian'
        
        # MediaWiki (Wikipedia, Fandom, etc.)
        if 'mediawiki' in html.lower() or 'wikipedia' in domain or 'fandom.com' in domain:
            return 'wiki'
        
        # Anki
        if 'ankiweb.net' in domain or 'anki' in html.lower():
            return 'anki'
        
        # Finance (TradingView, Yahoo Finance, etc.)
        finance_indicators = ['tradingview', 'yahoo', 'investing.com', 'coinmarketcap', 'coingecko']
        if any(ind in domain for ind in finance_indicators):
            return 'finance'
        
        # Notion
        if 'notion.so' in domain or 'notion.site' in domain:
            return 'notion'
        
        # GitBook
        if 'gitbook.io' in domain or 'gitbook' in html.lower():
            return 'gitbook'
        
        return 'generic'
    
    def _parse_html(self, html: str, base_url: str, content_type: str) -> HarvestedContent:
        """Parse HTML and extract clean content."""
        from html.parser import HTMLParser
        import html as html_module
        
        # Simple but effective HTML parsing
        # Remove script/style tags
        html = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
        html = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', html, flags=re.IGNORECASE)
        html = re.sub(r'<noscript[^>]*>[\s\S]*?</noscript>', '', html, flags=re.IGNORECASE)
        
        # Extract title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        title = html_module.unescape(title_match.group(1).strip()) if title_match else ""
        
        # Extract headings
        headings = []
        for match in re.finditer(r'<h[1-6][^>]*>([^<]+)</h[1-6]>', html, re.IGNORECASE):
            heading = html_module.unescape(match.group(1).strip())
            if heading and len(heading) < 200:
                headings.append(heading)
        
        # Extract code blocks
        code_blocks = []
        for match in re.finditer(r'<pre[^>]*><code[^>]*>([\s\S]*?)</code></pre>', html, re.IGNORECASE):
            code = html_module.unescape(match.group(1).strip())
            if code:
                code_blocks.append(code[:1000])  # Limit size
        
        # Extract links and filter
        internal_links = []
        external_links = []
        base_domain = urlparse(base_url).netloc
        
        for match in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\']', html, re.IGNORECASE):
            href = match.group(1)
            full_url = urljoin(base_url, href)
            
            if self._is_useful_link(full_url, base_domain):
                parsed = urlparse(full_url)
                if parsed.netloc == base_domain:
                    internal_links.append(full_url)
                else:
                    external_links.append(full_url)
        
        # Dedupe and limit
        internal_links = list(dict.fromkeys(internal_links))[:self.max_links]
        external_links = list(dict.fromkeys(external_links))[:10]
        
        # Extract images (only from same domain to avoid tracking pixels)
        images = []
        for match in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE):
            src = match.group(1)
            full_url = urljoin(base_url, src)
            parsed = urlparse(full_url)
            if parsed.netloc == base_domain or not parsed.netloc:
                images.append(full_url)
        images = images[:10]
        
        # Extract text content (strip HTML tags)
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text)
        text = html_module.unescape(text).strip()
        
        # Clean up noise phrases common in web content
        noise_phrases = [
            r'Cookie.*?accept', r'Sign up.*?newsletter', r'Subscribe.*?updates',
            r'Share on.*?Twitter', r'Follow us on', r'Join our.*?community',
            r'Click here to', r'Learn more about', r'Read more',
        ]
        for phrase in noise_phrases:
            text = re.sub(phrase, '', text, flags=re.IGNORECASE)
        
        return HarvestedContent(
            url=base_url,
            title=title,
            content=text[:50000],  # Limit to 50k chars
            content_type=content_type,
            internal_links=internal_links,
            external_links=external_links,
            images=images,
            code_blocks=code_blocks[:10],
            headings=headings[:20],
            fetched_at=datetime.now(),
            word_count=len(text.split())
        )
    
    def _is_useful_link(self, url: str, base_domain: str) -> bool:
        """Check if a link is useful (not noise)."""
        try:
            parsed = urlparse(url)
            
            # Skip non-http
            if parsed.scheme not in ('http', 'https', ''):
                return False
            
            # Skip blocked domains
            domain = parsed.netloc.lower()
            for blocked in self.BLOCKED_DOMAINS:
                if blocked in domain:
                    return False
            
            # Skip blocked URL patterns
            for pattern in self._blocked_patterns:
                if pattern.search(url):
                    return False
            
            # Skip empty or fragment-only
            if not parsed.path or parsed.path == '/':
                if parsed.fragment:
                    return True  # Same-page anchor is ok
                return False
            
            return True
            
        except Exception:
            return False
    
    # ==========================================
    # BATCH OPERATIONS
    # ==========================================
    
    async def harvest_multiple(self, urls: List[str]) -> List[HarvestedContent]:
        """Harvest multiple URLs concurrently."""
        tasks = [self.fetch_and_clean(url) for url in urls[:20]]  # Cap at 20
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
    
    async def crawl_site(
        self, 
        start_url: str, 
        max_pages: int = 10,
        same_domain_only: bool = True
    ) -> List[HarvestedContent]:
        """
        Crawl a site starting from a URL.
        
        Args:
            start_url: Starting page
            max_pages: Maximum pages to fetch
            same_domain_only: Only follow internal links
            
        Returns:
            List of harvested content
        """
        visited: Set[str] = set()
        to_visit = [start_url]
        results = []
        base_domain = urlparse(start_url).netloc
        
        while to_visit and len(results) < max_pages:
            url = to_visit.pop(0)
            
            if url in visited:
                continue
            visited.add(url)
            
            content = await self.fetch_and_clean(url)
            if content:
                results.append(content)
                
                # Add internal links to queue
                for link in content.internal_links:
                    if link not in visited and link not in to_visit:
                        if same_domain_only:
                            if urlparse(link).netloc == base_domain:
                                to_visit.append(link)
                        else:
                            to_visit.append(link)
        
        return results


# Singleton
_harvester: Optional[ContentHarvester] = None

def get_content_harvester() -> ContentHarvester:
    global _harvester
    if _harvester is None:
        _harvester = ContentHarvester()
    return _harvester
