import pandas as pd
import time
from datetime import datetime
from serpapi import GoogleSearch

api_key = '...'

df = pd.read_excel('/.../... .xlsx')

output_file_name = '/.../... .xlsx'

#-------------functions-------------------

def get_data_ids_from_google_maps(q: str) -> list:
    time.sleep(0.02)

    params = {
    'api_key': api_key,
    'q': q,
    'engine': 'google_maps',
    'google_domain': 'google.com',
    'hl': 'en'
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if 'place_results' in results.keys() and 'reviews' in results['place_results'].keys():
        return [[results['place_results']['data_id'], results['place_results']['title']]]
    elif 'local_results' in results.keys():
        return [[result['data_id'], result['title']] for result in results['local_results'] if 'reviews' in result.keys()]
    else:
        return []

def get_one_review_page_from_google_maps(data_id: str, next_page_token:str = False) -> list:
    time.sleep(0.02)

    params = {
    "engine": "google_maps_reviews",
    "data_id": data_id,
    "api_key": api_key
    }
    if next_page_token:
        params.update({'next_page_token': next_page_token})

    search = GoogleSearch(params)
    results = search.get_dict()
    if 'reviews' in results.keys():
        reviews = results["reviews"]
        if 'serpapi_pagination' in results.keys():
            next_page_token = results['serpapi_pagination']['next_page_token']
        else:
            next_page_token = False
        return reviews, next_page_token
    else:
        return False, False

#-----------------------------------------

startTime = datetime.now()

df = df[df.columns[0:4]].values
reviews = []
for row in df:
    temp_reviews = []
    number, physician = row[0], row[1]
    print(number, physician)

    data_ids = get_data_ids_from_google_maps(' '.join(row[1:4]))
    if data_ids:
        for double in data_ids:
            data_id, title = double
            review_page, next_page_token = get_one_review_page_from_google_maps(data_id)
            if review_page:
                for review in review_page:
                    review.update({'data_id': data_id, 'title': title})
                [temp_reviews.append(review) for review in review_page]
                while next_page_token:
                    review_page, next_page_token = get_one_review_page_from_google_maps(data_id, next_page_token)
                    if review_page:
                        for review in review_page:
                            review.update({'data_id': data_id, 'title': title})
                        [temp_reviews.append(review) for review in review_page]

        for review in temp_reviews:
            review['number'] = number
            review['physician'] = physician

        [reviews.append(i) for i in temp_reviews]

pd.DataFrame(reviews).to_excel(output_file_name)

print(datetime.now() - startTime)
