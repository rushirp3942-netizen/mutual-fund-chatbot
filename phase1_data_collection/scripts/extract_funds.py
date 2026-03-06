#!/usr/bin/env python3
"""
Script to extract mutual fund data from Groww
Usage: python extract_funds.py
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_pipeline.scraper import GrowwFundScraper, extract_multiple_funds


# Seed URLs from architecture document + SBI ELSS Tax Saver Fund
SEED_URLS = [
    "https://groww.in/mutual-funds/bandhan-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-long-term-value-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/nippon-india-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/tata-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/axis-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/sbi-small-midcap-fund-direct-growth",
    "https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth"  # ELSS Fund with 3-year lock-in
]


async def main():
    """Main extraction function"""
    
    print("=" * 70)
    print("MUTUAL FUND DATA EXTRACTION - PHASE 1")
    print("=" * 70)
    print(f"Target: {len(SEED_URLS)} funds from Groww")
    print("=" * 70)
    
    # Run extraction
    results = await extract_multiple_funds(
        fund_urls=SEED_URLS,
        output_file="data/processed/extracted_funds.json"
    )
    
    # Print summary
    print("\n" + "=" * 70)
    print("EXTRACTION SUMMARY")
    print("=" * 70)
    
    successful = sum(1 for r in results if r.fund_name != "Extraction Failed")
    failed = len(results) - successful
    
    print(f"Total funds processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    # Print extracted data in required format
    print("\n" + "=" * 70)
    print("EXTRACTED DATA")
    print("=" * 70)
    
    for i, data in enumerate(results, 1):
        print(f"\n--- Fund {i}: {data.fund_name} ---")
        print(f"Fund Name: {data.fund_name}")
        print(f"Expense Ratio: {data.expense_ratio or 'Not available'}")
        print(f"Exit Load: {data.exit_load or 'Not available'}")
        print(f"Minimum SIP: {data.minimum_sip or 'Not available'}")
        print(f"Lock-in Period: {data.lock_in_period}")
        print(f"Riskometer / Risk Level: {data.risk_level or 'Not available'}")
        print(f"Benchmark: {data.benchmark or 'Not available'}")
        print(f"How to download statements: {data.statement_download_info}")
        print(f"Source Link: {data.source_url}")
        if data.amc:
            print(f"AMC: {data.amc}")
        if data.category:
            print(f"Category: {data.category}")
    
    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"Data saved to: data/processed/extracted_funds.json")


if __name__ == "__main__":
    asyncio.run(main())
