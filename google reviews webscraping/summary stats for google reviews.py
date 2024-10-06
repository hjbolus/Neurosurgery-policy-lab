import pandas as pd
import time
from datetime import datetime

if __name__ == "__main__":
    df = pd.read_excel('/Users/harrisbolus/PycharmProjects/pythonProject/google reviews data 021324.xlsx')
    
    numbers = set(df['number'])
    
    list1 = []
    for number in numbers:
        data =  df[df['number'] == number]
        reviews = data['reviews']
    
        list1.append({
        'number': number,
        'single_review': len(data[data['reviews'] == 1]),
        'three_or_fewer': len(data[data['reviews'] < 4]),
        'twenty_plus': len(data[data['reviews'] > 20]),
        'mean': reviews.mean(),
        'median': reviews.median(),
        'stdev': reviews.std()
        })
    
    pd.DataFrame(list1).to_excel('/Users/harrisbolus/PycharmProjects/pythonProject/data to add.xlsx')
