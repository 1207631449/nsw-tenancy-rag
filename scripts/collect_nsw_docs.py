"""
使用浏览器批量收集 NSW 租房法律文档
"""

import os
import sys
import json
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 要收集的页面
PAGES = [
    {
        "url": "https://www.nsw.gov.au/housing-and-construction/renting-a-place-to-live/getting-repairs-done",
        "title": "Getting Repairs Done",
        "category": "repairs"
    },
    {
        "url": "https://www.nsw.gov.au/housing-and-construction/renting-a-place-to-live/residential-rental-bonds",
        "title": "Residential Rental Bonds",
        "category": "bond"
    },
    {
        "url": "https://www.nsw.gov.au/housing-and-construction/renting-a-place-to-live/rent-increases",
        "title": "Rent Increases",
        "category": "rent_increase"
    },
    {
        "url": "https://www.nsw.gov.au/housing-and-construction/rules/landlord-access-and-entry-to-a-rental-property",
        "title": "Landlord Access and Entry",
        "category": "access"
    },
    {
        "url": "https://www.nsw.gov.au/housing-and-construction/rules/giving-notice-to-end-a-residential-tenancy",
        "title": "Giving Notice to End Tenancy",
        "category": "termination"
    },
    {
        "url": "https://www.nsw.gov.au/housing-and-construction/renting-a-place-to-live/getting-your-bond-back",
        "title": "Getting Your Bond Back",
        "category": "bond_return"
    },
    {
        "url": "https://www.nsw.gov.au/housing-and-construction/renting-a-place-to-live/resolving-residential-tenancy-disputes",
        "title": "Resolving Tenancy Disputes",
        "category": "dispute"
    },
    {
        "url": "https://www.nsw.gov.au/housing-and-construction/rules/when-and-how-rent-can-be-increased",
        "title": "When and How Rent Can Be Increased",
        "category": "rent_rules"
    },
    {
        "url": "https://www.nsw.gov.au/housing-and-construction/rules/residential-tenancy-agreements",
        "title": "Residential Tenancy Agreements",
        "category": "agreement"
    },
    {
        "url": "https://www.nsw.gov.au/housing-and-construction/rules/minimum-standards-for-rental-properties",
        "title": "Minimum Standards for Rental Properties",
        "category": "standards"
    },
    {
        "url": "https://www.nsw.gov.au/housing-and-construction/rules/pets-rentals",
        "title": "Keeping a Pet in a Rental Property",
        "category": "pets"
    },
    {
        "url": "https://www.nsw.gov.au/housing-and-construction/rules/eviction-of-a-tenant-from-a-rental-property",
        "title": "Eviction of a Tenant",
        "category": "eviction"
    },
]


def main():
    from playwright.sync_api import sync_playwright
    
    print("=" * 60)
    print("NSW Rental Law Document Collector")
    print("=" * 60)
    
    output_dir = Path(__file__).parent.parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for i, page_info in enumerate(PAGES):
            print(f"\n[{i+1}/{len(PAGES)}] {page_info['title']}")
            print(f"  URL: {page_info['url']}")
            
            try:
                page.goto(page_info['url'], wait_until='networkidle', timeout=30000)
                time.sleep(1)  # 等待动态内容加载
                
                # 提取主要内容
                content = page.evaluate('''() => {
                    const main = document.querySelector('main');
                    if (!main) return '';
                    
                    // 移除不需要的元素
                    const clone = main.cloneNode(true);
                    for (const el of clone.querySelectorAll('nav, footer, .breadcrumb, .sidebar, .related-links')) {
                        el.remove();
                    }
                    
                    return clone.innerText;
                }''')
                
                if content and len(content) > 200:
                    print(f"  Success: {len(content)} characters")
                    
                    results.append({
                        "id": f"nsw_{page_info['category']}",
                        "content": content,
                        "metadata": {
                            "source": f"NSW Government - {page_info['title']}",
                            "type": "guide",
                            "category": page_info['category'],
                            "url": page_info['url'],
                            "title": page_info['title']
                        },
                        "source": f"NSW Government - {page_info['title']}",
                        "section": "",
                        "title": page_info['title']
                    })
                else:
                    print(f"  Warning: Content too short ({len(content)} chars)")
                    
            except Exception as e:
                print(f"  Error: {e}")
        
        browser.close()
    
    # 保存结果
    output_file = output_dir / "nsw_rental_chunks.json"
    
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
    print(f"Collected {len(results)} new pages")
    print(f"Total: {len(existing)} documents")
    print(f"Saved to: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
