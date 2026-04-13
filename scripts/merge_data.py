import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 加载所有数据
all_docs = []

# 示例数据
with open('data/processed/sample_chunks.json', 'r', encoding='utf-8') as f:
    all_docs.extend(json.load(f))

# NSW 数据
with open('data/processed/nsw_rental_chunks.json', 'r', encoding='utf-8') as f:
    all_docs.extend(json.load(f))

# Fair Trading 数据 (部分有效)
with open('data/processed/fair_trading_chunks.json', 'r', encoding='utf-8') as f:
    ft_data = json.load(f)
    for doc in ft_data:
        if len(doc['content']) > 2000:  # 只保留内容较长的
            all_docs.append(doc)

# 合并保存
with open('data/processed/all_chunks.json', 'w', encoding='utf-8') as f:
    json.dump(all_docs, f, ensure_ascii=False, indent=2)

print(f'Total documents: {len(all_docs)}')
for doc in all_docs:
    print(f'  - {doc["id"]}: {len(doc["content"])} chars')
