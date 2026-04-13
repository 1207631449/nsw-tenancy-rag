"""
Fair Trading NSW 爬虫
抓取租房相关法律指南
"""

import os
import sys
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

# 设置编码
sys.stdout.reconfigure(encoding='utf-8')
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import requests
from bs4 import BeautifulSoup


# 要爬取的页面
PAGES_TO_SCRAPE = [
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting",
        "title": "Renting Overview",
        "category": "overview"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/before-you-start",
        "title": "Before You Start",
        "category": "before_renting"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/looking-for-a-place-to-live",
        "title": "Looking for a Place to Live",
        "category": "finding"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/signing-a-tenancy-agreement",
        "title": "Signing a Tenancy Agreement",
        "category": "agreement"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/bond",
        "title": "Bond (押金)",
        "category": "bond"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/paying-rent",
        "title": "Paying Rent",
        "category": "rent"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/during-a-tenancy",
        "title": "During a Tenancy",
        "category": "during"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/during-a-tenancy/tenant-rights-and-responsibilities",
        "title": "Tenant Rights and Responsibilities",
        "category": "rights"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/during-a-tenancy/landlord-rights-and-responsibilities",
        "title": "Landlord Rights and Responsibilities",
        "category": "landlord_rights"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/during-a-tenancy/repairs-and-maintenance",
        "title": "Repairs and Maintenance",
        "category": "repairs"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/during-a-tenancy/rent-increases",
        "title": "Rent Increases",
        "category": "rent_increase"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/during-a-tenancy/access-and-inspections",
        "title": "Access and Inspections",
        "category": "access"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/ending-a-tenancy",
        "title": "Ending a Tenancy",
        "category": "ending"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/ending-a-tenancy/giving-a-termination-notice",
        "title": "Giving a Termination Notice",
        "category": "termination"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/ending-a-tenancy/getting-your-bond-back",
        "title": "Getting Your Bond Back",
        "category": "bond_return"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/ending-a-tenancy/disputes-about-the-bond",
        "title": "Disputes About the Bond",
        "category": "bond_dispute"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/problems-during-a-tenancy",
        "title": "Problems During a Tenancy",
        "category": "problems"
    },
    {
        "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/problems-during-a-tenancy/dispute-resolution",
        "title": "Dispute Resolution",
        "category": "dispute"
    },
]


def clean_text(text: str) -> str:
    """清理文本"""
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    # 移除前后空白
    text = text.strip()
    return text


def extract_content(soup: BeautifulSoup, url: str) -> str:
    """提取页面主要内容"""
    # 尝试找到主要内容区域
    main_content = None
    
    # 尝试不同的选择器
    selectors = [
        'main',
        '.main-content',
        '.content',
        '#main-content',
        'article',
        '.page-content',
    ]
    
    for selector in selectors:
        main_content = soup.select_one(selector)
        if main_content:
            break
    
    if not main_content:
        main_content = soup.find('body')
    
    if not main_content:
        return ""
    
    # 移除不需要的元素
    for tag in main_content.find_all(['nav', 'footer', 'header', 'aside', 'script', 'style', 'form']):
        tag.decompose()
    
    # 提取文本
    content_parts = []
    
    for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
        text = clean_text(element.get_text())
        if text and len(text) > 10:  # 忽略太短的文本
            if element.name.startswith('h'):
                content_parts.append(f"\n## {text}\n")
            else:
                content_parts.append(text)
    
    return '\n'.join(content_parts)


def scrape_page(page_info: dict) -> dict:
    """爬取单个页面"""
    url = page_info["url"]
    title = page_info["title"]
    category = page_info["category"]
    
    print(f"Scraping: {title}")
    print(f"  URL: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-AU,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        content = extract_content(soup, url)
        
        if not content:
            print(f"  Warning: No content extracted")
            return None
        
        print(f"  Success: {len(content)} characters")
        
        return {
            "id": f"fair_trading_{category}",
            "content": content,
            "metadata": {
                "source": f"Fair Trading NSW - {title}",
                "type": "guide",
                "category": category,
                "url": url,
                "title": title
            },
            "source": f"Fair Trading NSW - {title}",
            "section": "",
            "title": title
        }
        
    except Exception as e:
        print(f"  Error: {e}")
        return None


def main():
    """主函数"""
    print("=" * 60)
    print("Fair Trading NSW Scraper")
    print("=" * 60)
    
    # 输出目录
    output_dir = Path(__file__).parent.parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 爬取所有页面
    results = []
    
    for i, page_info in enumerate(PAGES_TO_SCRAPE):
        print(f"\n[{i+1}/{len(PAGES_TO_SCRAPE)}]")
        
        result = scrape_page(page_info)
        if result:
            results.append(result)
        
        # 礼貌延迟
        if i < len(PAGES_TO_SCRAPE) - 1:
            time.sleep(1)
    
    # 保存结果
    output_file = output_dir / "fair_trading_chunks.json"
    
    # 加载已有数据
    existing = []
    if output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    
    # 合并数据（去重）
    existing_ids = {item["id"] for item in existing}
    for result in results:
        if result["id"] not in existing_ids:
            existing.append(result)
    
    # 保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"Scraped {len(results)} new pages")
    print(f"Total: {len(existing)} documents")
    print(f"Saved to: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
