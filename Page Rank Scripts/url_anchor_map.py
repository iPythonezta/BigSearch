import pandas as pd
import json
page_rank_links = pd.read_csv('..\\Data\\Page_rank_files\\Page_rank_links.csv')
page_rank_links.drop(columns=['from_url'], inplace=True)
# Drop rows where anchor_text is NaN
page_rank_links.dropna(subset=['anchor_text'], inplace=True)
# merge all anchor text for each to_url into a single string
page_rank_links = page_rank_links.groupby('to_url')['anchor_text'].apply(lambda x: ' '.join(x)).reset_index()
to_url_to_anchor = dict(zip(page_rank_links['to_url'], page_rank_links['anchor_text']))

with open('..\\Data\\Page_rank_files\\url_to_anchor_text.json', 'w', encoding='utf-8') as f:
    json.dump(to_url_to_anchor, f, ensure_ascii=False, indent=2)