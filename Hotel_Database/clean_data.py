import chardet
import pandas as pd

with open('hotels(0, 10000).csv', 'rb') as f:
    result = chardet.detect(f.readline())  # or readline if the file is large

def concat_and_clean(df1, df2, column_name):
    return pd.concat([df1, df2]).drop_duplicates(subset=column_name).reset_index(drop=True)

df1 = pd.read_csv("hotels(0, 10000).csv", keep_default_na=False)
df2 = pd.read_csv("hotels(0, 10000).csv", keep_default_na=False)
final = concat_and_clean(df1, df2, "hotel")
pd.DataFrame(final).to_csv("cleaned_hotels.csv")
print('number of cities: '+str(len(final['city'].unique())))