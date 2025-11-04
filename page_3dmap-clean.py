import geopandas as gpd
import pandas as pd
import numpy as np

doc = gpd.read_file("park01-clean/park01_202510091630_clean.shp")

# replace_map = {
#     '中山居': '中山區',
#     '中正': '中正區',
#     '松山': '松山區',
#     '萬華': '萬華區'
# }
# 
# doc['area_name'] = doc['area_name'].replace(replace_map)
# 
# counts = doc['area_name'].value_counts()
# 
# max_count = counts.max()
# sample_sizes = (counts / max_count * 1000).astype(int)
# 
# def proportional_sample(x):
#         n = sample_sizes[x.name]
#         n = min(len(x), n) # 不超過該區原始筆數
#         return x.sample(n=n, random_state=42)
# 
# sampled = doc.groupby('area_name',group_keys=False).apply(proportional_sample)
# 
# # print(sampled['area_name'].value_counts())
# 
# sampled.to_file("park01-clean/park01_202510091630_clean.shp", encoding='utf-8')

cols_to_keep = ['pkid','area_name','roadname','village_na', 'geometry']
doc_reduced = doc[cols_to_keep]

doc_reduced.to_file("park01-clean/park01_202510091630_clean.shp", encoding='utf-8')