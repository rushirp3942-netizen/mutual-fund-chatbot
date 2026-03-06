"""
Groww Mutual Fund Scraper using Playwright
Extracts fund data from Groww mutual fund pages
"""

import asyncio
import re
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
from urllib.parse import urljoin
import json

from playwright.async_api import async_playwright, Page


@dataclass
class MutualFundData:
    """Data class for mutual fund information"""
    fund_name: str
    expense_ratio: Optional[str]
    exit_load: Optional[str]
    minimum_sip: Optional[str]
    lock_in_period: str
    risk_level: Optional[str]
    benchmark: Optional[str]
    statement_download_info: str
    source_url: str
    amc: Optional[str] = None
    category: Optional[str] = None
    fund_size: Optional[str] = None
    nav: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class GrowwFundScraper:
    """Scraper for extracting mutual fund data from Groww"""
    
    def __init__(self):
        self.base_url = "https://groww.in"
        self.statement_download_text = (
            "Log in to Groww → Profile → Reports → Select Mutual Fund report → "
            "Choose date range → Download statement."
        )
    
    async def extract_fund_data(self, fund_url: str) -> MutualFundData:
        """
        Extract comprehensive fund data using Playwright
        
        Args:
            fund_url: URL of the Groww mutual fund page
            
        Returns:
            MutualFundData object with extracted information
        """
        async with async_playwright() as p:
            # Launch browser with specific settings for Groww
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            # Set default timeout
            context.set_default_timeout(30000)
            
            page = await context.new_page()
            
            try:
                print(f"  Navigating to: {fund_url}")
                
                # Navigate to fund page with extended timeout
                await page.goto(fund_url, wait_until="networkidle", timeout=60000)
                await page.wait_for_load_state("domcontentloaded")
                
                # Wait for main content
                await page.wait_for_selector("h1", timeout=10000)
                
                # Additional wait for dynamic content
                await page.wait_for_timeout(2000)
                
                print(f"  Extracting fields...")
                
                # Extract all fund data
                fund_data = await self._extract_all_fields(page, fund_url)
                
                print(f"  ✓ Extracted: {fund_data.fund_name}")
                
                return fund_data
                
            except Exception as e:
                print(f"  ✗ Error extracting {fund_url}: {str(e)}")
                # Return partial data with error info
                return MutualFundData(
                    fund_name="Extraction Failed",
                    expense_ratio=None,
                    exit_load=None,
                    minimum_sip=None,
                    lock_in_period="Unknown",
                    risk_level=None,
                    benchmark=None,
                    statement_download_info=self.statement_download_text,
                    source_url=fund_url
                )
            finally:
                await browser.close()
    
    async def _extract_all_fields(self, page: Page, fund_url: str) -> MutualFundData:
        """Extract all fund fields with multiple fallback strategies"""
        
        # Extract basic fields
        fund_name = await self._extract_fund_name(page)
        expense_ratio = await self._extract_expense_ratio(page)
        exit_load = await self._extract_exit_load(page)
        minimum_sip = await self._extract_minimum_sip(page)
        
        # Extract category and determine lock-in
        category = await self._extract_category(page)
        lock_in_period = self._determine_lock_in(category)
        
        # Extract AMC
        amc = await self._extract_amc(page)
        
        # Extract fund size and NAV
        fund_size = await self._extract_fund_size(page)
        nav = await self._extract_nav(page)
        
        # Extract Riskometer with multiple strategies
        risk_level = await self._extract_riskometer(page)
        
        # Extract Benchmark with multiple strategies
        benchmark = await self._extract_benchmark(page)
        
        return MutualFundData(
            fund_name=fund_name,
            expense_ratio=expense_ratio,
            exit_load=exit_load,
            minimum_sip=minimum_sip,
            lock_in_period=lock_in_period,
            risk_level=risk_level,
            benchmark=benchmark,
            statement_download_info=self.statement_download_text,
            source_url=fund_url,
            amc=amc,
            category=category,
            fund_size=fund_size,
            nav=nav
        )
    
    async def _extract_fund_name(self, page: Page) -> str:
        """Extract fund name from page header"""
        selectors = [
            "h1",
            "[data-testid='fund-name']",
            ".fund-name",
            "h1.fund-header",
            "[class*='fundName']",
            "[class*='FundName']"
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text.strip()) > 5:
                        return text.strip()
            except:
                continue
        
        # Fallback: extract from title
        try:
            title = await page.title()
            # Remove "- Groww" suffix
            if "-" in title:
                return title.split("-")[0].strip()
            return title.strip()
        except:
            pass
        
        return "Not available"
    
    async def _extract_amc(self, page: Page) -> Optional[str]:
        """Extract AMC (Asset Management Company) name"""
        try:
            # Look for AMC in fund name or specific elements
            selectors = [
                "[data-testid='amc-name']",
                ".amc-name",
                "[class*='amc']",
                "[class*='AMC']"
            ]
            
            for selector in selectors:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text:
                        return text.strip()
            
            # Extract from fund name (first word usually)
            fund_name = await self._extract_fund_name(page)
            if " " in fund_name:
                # Common AMC names
                amc_keywords = ["HDFC", "SBI", "ICICI", "Axis", "Bandhan", 
                               "Nippon", "Tata", "Parag Parikh", "WhiteOak"]
                for amc in amc_keywords:
                    if amc.lower() in fund_name.lower():
                        return f"{amc} Mutual Fund"
                        
        except:
            pass
        
        return None
    
    async def _extract_expense_ratio(self, page: Page) -> Optional[str]:
        """Extract expense ratio from multiple locations"""
        try:
            # Get page content and search for expense ratio
            content = await page.content()
            
            # Pattern: Expense ratio followed by percentage
            patterns = [
                r'Expense ratio[\s:]+(\d+\.?\d*)%',
                r'Expense ratio[\s\w]*</[^>]+>[\s]*([\d.]+)%',
                r'>(\d+\.?\d*)%<[^>]*>[^<]*Expense'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return f"{match.group(1)}%"
            
            # Try selectors
            selectors = [
                "text=Expense ratio",
                "[data-testid='expense-ratio']",
                ".expense-ratio .value",
                "div:has-text('Expense ratio') + div",
                "div:has-text('Expense ratio') ~ div"
            ]
            
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        if text and "%" in text:
                            # Extract just the percentage
                            match = re.search(r'(\d+\.?\d*)%', text)
                            if match:
                                return f"{match.group(1)}%"
                except:
                    continue
                    
        except Exception as e:
            print(f"    Warning: Could not extract expense ratio: {e}")
        
        return None
    
    async def _extract_exit_load(self, page: Page) -> Optional[str]:
        """Extract exit load from Exit Load section"""
        try:
            # Look for exit load in page content
            content = await page.content()
            
            # Common exit load patterns
            patterns = [
                r'Exit load of (\d+%)[^<]*if redeemed within (\d+)[^<]*year',
                r'Exit load[\s:]+(\d+%)[^<]*within (\d+)',
                r'>(Exit load of \d+%[^<]+)<',
                r'Exit load[\s\w]+</[^>]+>[\s]*([^<]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(0).replace(">", "").replace("<", "").strip()
            
            # Try to find and click Exit Load section
            exit_load_elements = await page.query_selector_all("text=Exit load")
            for element in exit_load_elements:
                try:
                    await element.click()
                    await page.wait_for_timeout(500)
                    
                    # Get updated content
                    content = await page.content()
                    if "Exit load of" in content:
                        match = re.search(r'Exit load of \d+%[^<]+', content)
                        if match:
                            return match.group(0).strip()
                except:
                    continue
                    
        except Exception as e:
            print(f"    Warning: Could not extract exit load: {e}")
        
        return None
    
    async def _extract_minimum_sip(self, page: Page) -> Optional[str]:
        """Extract minimum SIP amount"""
        try:
            content = await page.content()
            
            # Look for Min. for SIP pattern
            patterns = [
                r'Min\. for SIP[\s:₹]*([\d,]+)',
                r'Minimum SIP[\s:₹]*([\d,]+)',
                r'>Min\. for SIP<[^>]*>[\s₹]*([\d,]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    amount = match.group(1).replace(",", "")
                    return f"₹{amount}"
            
            # Try selectors
            selectors = [
                "text=Min. for SIP",
                "[data-testid='min-sip']",
                "div:has-text('Min. for SIP') + div"
            ]
            
            for selector in selectors:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if "₹" in text or any(c.isdigit() for c in text):
                        # Extract amount
                        match = re.search(r'₹?([\d,]+)', text)
                        if match:
                            return f"₹{match.group(1)}"
                            
        except Exception as e:
            print(f"    Warning: Could not extract minimum SIP: {e}")
        
        return None
    
    async def _extract_fund_size(self, page: Page) -> Optional[str]:
        """Extract fund size/AUM"""
        try:
            content = await page.content()
            
            # Look for Fund size pattern
            patterns = [
                r'Fund size[\s:₹]*([\d,]+\.?\d*)\s*Cr',
                r'AUM[\s:₹]*([\d,]+\.?\d*)\s*Cr'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return f"₹{match.group(1)} Cr"
                    
        except:
            pass
        
        return None
    
    async def _extract_nav(self, page: Page) -> Optional[str]:
        """Extract current NAV"""
        try:
            # Try to get NAV from page content using multiple selectors
            nav_selectors = [
                '[data-testid="nav-value"]',
                '.nav-value',
                '[class*="nav"]',
                'div:has-text("NAV") + div',
                'div:has-text("₹"):has-text("NAV")'
            ]
            
            for selector in nav_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        # Extract number with ₹ symbol
                        match = re.search(r'₹?\s*([\d,]+\.?\d*)', text)
                        if match:
                            return f"₹{match.group(1)}"
                except:
                    continue
            
            # Fallback: Search in page content
            content = await page.content()
            
            # Look for NAV pattern with more comprehensive patterns
            patterns = [
                r'NAV[\s:]+[₹\s]*([\d,]+\.?\d*)',
                r'[₹\s]*([\d,]+\.?\d*)[\s]*<[^>]*>[^<]*NAV',
                r'class="[^"]*nav[^"]*"[^>]*>[₹\s]*([\d,]+\.?\d*)',
                r'>([\d,]+\.?\d*)<[^>]*>\s*<[^>]*>\s*NAV',
                r'NAV\s*</[^>]*>\s*<[^>]*>[₹\s]*([\d,]+\.?\d*)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    nav_value = match.group(1)
                    # Ensure it's a reasonable NAV value (not too small)
                    try:
                        nav_num = float(nav_value.replace(',', ''))
                        if nav_num > 1:  # NAV should be greater than 1
                            return f"₹{nav_value}"
                    except:
                        continue
                    
        except Exception as e:
            print(f"    NAV extraction error: {e}")
        
        return None
    
    async def _extract_category(self, page: Page) -> Optional[str]:
        """Extract fund category for lock-in determination"""
        try:
            content = await page.content()
            
            # Common category patterns
            categories = [
                "Equity Mid Cap",
                "Equity Large Cap", 
                "Equity Small Cap",
                "ELSS",
                "Tax Saver",
                "Debt",
                "Hybrid",
                "Index Fund"
            ]
            
            for category in categories:
                if category in content:
                    return category
            
            # Look for category in returns table
            if "Category average" in content:
                match = re.search(r'Category average \(([^)]+)\)', content)
                if match:
                    return match.group(1)
                    
        except:
            pass
        
        return None
    
    def _determine_lock_in(self, category: Optional[str]) -> str:
        """Determine lock-in period based on category"""
        if category and ("ELSS" in category or "Tax Saver" in category):
            return "3 years lock-in period"
        return "No lock-in period"
    
    async def _extract_riskometer(self, page: Page) -> Optional[str]:
        """
        Extract Riskometer level with multiple strategies
        Checks: Main section, Fund details, Risk section, visual indicators
        """
        
        # Strategy 1: Look for risk text in page content
        try:
            content = await page.content()
            
            # Standard risk levels
            risk_levels = ["Very High", "High", "Moderately High", "Moderate", 
                          "Moderately Low", "Low", "Very Low"]
            
            for level in risk_levels:
                # Look for risk level in various contexts
                patterns = [
                    f'"{level}"[^<]*Risk',
                    f'Risk[^<]*"{level}"',
                    f'>{level} Risk<',
                    f'>{level}<[^>]*>[^<]*risk',
                    f'risk[^>]*>{level}<'
                ]
                
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        return level
                        
        except:
            pass
        
        # Strategy 2: Look for specific risk selectors
        risk_selectors = [
            "[data-testid='riskometer']",
            "[data-testid='risk-level']",
            ".riskometer",
            ".risk-level",
            "[data-risk-level]",
            ".fund-risk",
            "[class*='riskLevel']",
            "[class*='RiskLevel']"
        ]
        
        for selector in risk_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text:
                        normalized = self._normalize_risk_level(text)
                        if normalized != "Not available":
                            return normalized
                    
                    # Check data attributes
                    risk_attr = await element.get_attribute("data-risk-level")
                    if risk_attr:
                        return self._normalize_risk_level(risk_attr)
                        
                    # Check aria-label
                    aria_label = await element.get_attribute("aria-label")
                    if aria_label and "risk" in aria_label.lower():
                        return self._normalize_risk_level(aria_label)
            except:
                continue
        
        # Strategy 3: Scroll and check for risk section
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
            await page.wait_for_timeout(1000)
            
            # Look again after scroll
            content = await page.content()
            
            for level in ["Very High", "High", "Moderate", "Low", "Very Low"]:
                if f'"{level}"' in content or f">{level}<" in content:
                    # Verify it's a risk indicator
                    surrounding = content[max(0, content.find(level) - 100):
                                         min(len(content), content.find(level) + 100)]
                    if "risk" in surrounding.lower():
                        return level
                        
        except:
            pass
        
        return "Not available"
    
    async def _extract_benchmark(self, page: Page) -> Optional[str]:
        """
        Extract Benchmark index with multiple strategies
        Checks: Returns section, Fund details, Performance comparison
        """
        
        # Strategy 1: Look for benchmark in page content
        try:
            content = await page.content()
            
            # Common benchmark patterns
            benchmark_patterns = [
                r'NIFTY(?:\s+)?Midcap(?:\s+)?\d+(?:\s+)?Total(?:\s+)?Return(?:\s+)?Index',
                r'NIFTY(?:\s+)?\d+(?:\s+)?Total(?:\s+)?Return(?:\s+)?Index',
                r'NIFTY(?:\s+)?Midcap(?:\s+)?\d+(?:\s+)?Index',
                r'NIFTY(?:\s+)?Large(?:\s+)?Midcap(?:\s+)?\d+(?:\s+)?Index',
                r'NIFTY(?:\s+)?Smallcap(?:\s+)?\d+(?:\s+)?Index',
                r'S&P BSE(?:\s+)?\w+(?:\s+)?Index',
                r'CRISIL(?:\s+)?\w+(?:\s+)?Index',
                r'Benchmark[\s:]+([^<]+Index)',
            ]
            
            for pattern in benchmark_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(0).replace("Benchmark:", "").strip()
            
            # Look for "vs" or "benchmark" comparisons
            if "vs" in content or "benchmark" in content.lower():
                # Often shown as "Fund vs Benchmark"
                vs_patterns = [
                    r'vs\s+([A-Z][A-Za-z\s]+Index)',
                    r'benchmark[\s:]+([A-Z][A-Za-z\s]+Index)',
                    r'>(NIFTY[A-Za-z\s]+Index)<',
                ]
                
                for pattern in vs_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
                        
        except:
            pass
        
        # Strategy 2: Look for benchmark selectors
        benchmark_selectors = [
            "[data-testid='benchmark']",
            "[data-testid='benchmark-index']",
            ".benchmark-index",
            ".fund-benchmark",
            "[class*='benchmark']",
            "[class*='Benchmark']"
        ]
        
        for selector in benchmark_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and "index" in text.lower():
                        return text.strip()
            except:
                continue
        
        # Strategy 3: Scroll and check for benchmark in performance section
        try:
            # Scroll to performance/returns section
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.4)")
            await page.wait_for_timeout(1000)
            
            # Look for tables with benchmark data
            tables = await page.query_selector_all("table")
            for table in tables:
                headers = await table.query_selector_all("th, td")
                for header in headers:
                    text = await header.inner_text()
                    if text and ("benchmark" in text.lower() or "nifty" in text.lower()):
                        if "Index" in text:
                            return text.strip()
                        
                        # Check adjacent cells
                        cells = await table.query_selector_all("td")
                        for cell in cells:
                            cell_text = await cell.inner_text()
                            if "NIFTY" in cell_text.upper() and "Index" in cell_text:
                                return cell_text.strip()
        except:
            pass
        
        return "Not available"
    
    def _normalize_risk_level(self, text: str) -> str:
        """Normalize risk level text to standard values"""
        if not text:
            return "Not available"
            
        text = text.strip().lower()
        
        if "very high" in text:
            return "Very High"
        elif "moderately high" in text:
            return "Moderately High"
        elif "high" in text:
            return "High"
        elif "moderately low" in text:
            return "Moderately Low"
        elif "moderate" in text:
            return "Moderate"
        elif "very low" in text:
            return "Very Low"
        elif "low" in text:
            return "Low"
        
        return "Not available"


async def extract_multiple_funds(fund_urls: List[str], output_file: str = None):
    """
    Extract data from multiple fund URLs
    
    Args:
        fund_urls: List of fund URLs to extract
        output_file: Optional file path to save results
        
    Returns:
        List of MutualFundData objects
    """
    scraper = GrowwFundScraper()
    results = []
    
    print(f"\nStarting extraction of {len(fund_urls)} funds...\n")
    
    for i, url in enumerate(fund_urls, 1):
        print(f"[{i}/{len(fund_urls)}] Processing...")
        try:
            data = await scraper.extract_fund_data(url)
            results.append(data)
        except Exception as e:
            print(f"  ✗ Failed: {str(e)}")
            # Add failed entry
            results.append(MutualFundData(
                fund_name="Extraction Failed",
                expense_ratio=None,
                exit_load=None,
                minimum_sip=None,
                lock_in_period="Unknown",
                risk_level=None,
                benchmark=None,
                statement_download_info=scraper.statement_download_text,
                source_url=url
            ))
        
        # Small delay between requests
        if i < len(fund_urls):
            await asyncio.sleep(2)
    
    # Save results if output file specified
    if output_file:
        output_data = [r.to_dict() for r in results]
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Results saved to: {output_file}")
    
    return results


# Seed URLs from architecture
SEED_URLS = [
    "https://groww.in/mutual-funds/bandhan-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-long-term-value-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/nippon-india-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/tata-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/axis-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/sbi-small-midcap-fund-direct-growth"
]


if __name__ == "__main__":
    # Run extraction on all seed URLs
    asyncio.run(extract_multiple_funds(
        fund_urls=SEED_URLS,
        output_file="data/processed/extracted_funds.json"
    ))
