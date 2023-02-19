import pandas as pd

df = pd.read_csv('elements.csv')

arr = []

for row in df.iloc:
    print(row['label'], row['name'])
    arr = int(input())

df['']