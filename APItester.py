import requests

# r = requests.get('https://newsapi.org/v2/everything?qInTitle=stock%20market&from=2025-11-27&to=2024-11-28&sortBy=popularity&language=en&apiKey=890603a55bfa47048e4490069ebee18c')

# content = r.json()

# articles = content['articles']

# for article in articles:
#     print('TITLE\n', article['title'], '\nDESCRIPTION\n', article['description'])

def get_news (topic, from_date, to_date, language='en', api_key='890603a55bfa47048e4490069ebee18c'):
    url = f'https://newsapi.org/v2/everything?qInTitle={topic}&from={from_date}&to={to_date}&sortBy=popularity&language={language}&apiKey={api_key}'
    r = requests.get(url)
    content = r.json()
    articles = content['articles']
    results = []
    for article in articles:
       results.append(f"TITLE\n'{article['title']}, '\nDESCRIPTION\n', {article['description']}")

    return results

print(get_news(topic='space', from_date='2025-11-27', to_date='2025-11-28'))
