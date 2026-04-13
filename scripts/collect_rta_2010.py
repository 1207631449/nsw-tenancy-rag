"""
收集 Residential Tenancies Act 2010 完整条款
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re

BASE_URL = "https://legislation.nsw.gov.au/view/html/inforce/current/act-2010-042"

def get_page_content(url):
    """获取页面内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_sections(html):
    """提取所有条款"""
    soup = BeautifulSoup(html, 'html.parser')
    sections = []
    
    # 查找所有条款
    for section in soup.find_all(['section', 'div'], class_=lambda x: x and 'section' in str(x).lower()):
        try:
            # 提取条款编号
            num_elem = section.find(['span', 'h5'], class_=lambda x: x and 'num' in str(x).lower())
            section_num = num_elem.get_text(strip=True) if num_elem else ""
            
            # 提取条款标题
            title_elem = section.find(['span', 'h5'], class_=lambda x: x and 'title' in str(x).lower())
            section_title = title_elem.get_text(strip=True) if title_elem else ""
            
            # 提取条款内容
            content_elem = section.find(['div', 'p'], class_=lambda x: x and 'content' in str(x).lower())
            content = content_elem.get_text(strip=True) if content_elem else section.get_text(strip=True)
            
            if section_num or section_title:
                sections.append({
                    'section': section_num,
                    'title': section_title,
                    'content': content[:2000]  # 限制长度
                })
        except Exception as e:
            continue
    
    return sections

def extract_key_sections(html):
    """提取关键条款（简化版）"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # 关键条款列表
    key_sections = [
        "41",  # Rent increases
        "63",  # Landlord's general obligation (repairs)
        "64",  # Urgent repairs
        "70",  # Locks and security
        "73B", # Pets
        "82",  # Termination notices
        "87C", # Breach of tenancy agreement
        "88",  # Non-payment of rent
        "29",  # Condition reports
        "50",  # Quiet enjoyment
        "55",  # Landlord access
        "56",  # Entry with consent
        "57",  # Limits on entry
    ]
    
    documents = []
    
    # 直接从页面文本中提取
    text = soup.get_text(separator='\n', strip=True)
    
    # 按条款分割
    lines = text.split('\n')
    current_section = None
    current_title = None
    current_content = []
    
    for line in lines:
        # 检测条款编号
        match = re.match(r'^(\d+[A-Z]?)\s+(.+)$', line.strip())
        if match:
            # 保存上一个条款
            if current_section and current_content:
                documents.append({
                    'id': f'rta_2010_{current_section}',
                    'source': 'Residential Tenancies Act 2010 (NSW)',
                    'title': current_title or f'Section {current_section}',
                    'content': '\n'.join(current_content),
                    'metadata': {
                        'section': current_section,
                        'url': f'{BASE_URL}#sec.{current_section}'
                    }
                })
            
            current_section = match.group(1)
            current_title = match.group(2)
            current_content = [line]
        elif current_section:
            current_content.append(line)
    
    # 保存最后一个条款
    if current_section and current_content:
        documents.append({
            'id': f'rta_2010_{current_section}',
            'source': 'Residential Tenancies Act 2010 (NSW)',
            'title': current_title or f'Section {current_section}',
            'content': '\n'.join(current_content),
            'metadata': {
                'section': current_section,
                'url': f'{BASE_URL}#sec.{current_section}'
            }
        })
    
    return documents

def main():
    print("Fetching Residential Tenancies Act 2010...")
    html = get_page_content(BASE_URL)
    
    if not html:
        print("Failed to fetch page")
        return
    
    print("Extracting sections...")
    documents = extract_key_sections(html)
    
    print(f"Found {len(documents)} sections")
    
    # 保存
    output_path = 'data/processed/rta_2010_sections.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"Saved to {output_path}")
    
    # 显示提取的条款
    for doc in documents[:10]:
        print(f"  Section {doc['metadata']['section']}: {doc['title'][:50]}")

if __name__ == "__main__":
    main()
