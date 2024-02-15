import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import pandas as pd

#sentiment analysis
xl = pd.read_excel('/Users/harrisbolus/PycharmProjects/pythonProject/healthgrades really last comments 021424.xlsx')

output_file_name = '/Users/harrisbolus/PycharmProjects/pythonProject/healthgrades webscraping sentiments really last batch.xlsx'
comments = list(xl['text'])

sia = SentimentIntensityAnalyzer()

def merge_dicts(dict1, dict2):
    dict1.update(dict2)
    return dict1

output_dict = [merge_dicts(sia.polarity_scores(i), {'text':i}) for i in comments]

df = pd.DataFrame(output_dict)

merge = pd.merge(xl, df, how='right', on='text')

#summary stats
names = set(merge['physician'])
summary = []
for name in names:
    tempdict = {'physician': name}
    data = merge[merge['physician'] == name]
    for column in ['neg','neu','pos','compound']:
        tempdict.update({column + ' mean': data[column].mean(),
                         column + ' std': data[column].std()})
    summary.append(tempdict)

with pd.ExcelWriter(output_file_name) as writer:
    merge.to_excel(writer, sheet_name="aggregate")
    pd.DataFrame(summary).to_excel(writer, sheet_name='summary statistics')
