import os
from dotenv import load_dotenv
from exa_py import Exa

load_dotenv()

exa = Exa(os.getenv('EXA_API_KEY'))


def clean_title(title):
    if not title:
        return '(no title)'
    title = title.split('.tiktok-')[0].strip()
    return title or '(no title)'


while True:
    query = input('Search here (or type quit): ')

    if query.strip().lower() == 'quit':
        break

    if not query.strip():
        continue

    response = exa.search(
        query,
        num_results=5,
        include_domains=['tiktok.com'],
    )

    with open('results.txt', 'a', encoding='utf-8') as file:
        file.write(f'Search: {query}\n')

        for result in response.results:
            title = clean_title(result.title)
            print(title)
            print(result.url)
            print()
            file.write(f'{title}\n{result.url}\n\n')





