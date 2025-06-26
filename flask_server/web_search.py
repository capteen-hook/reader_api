import requests
from bs4 import BeautifulSoup

# query = "7229 S Hamlin Ave, Chicago, IL 60629"
def search_duckduckgo(query):
    url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:84.0) Gecko/20100101 Firefox/84.0",
    }

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all <a> tags with the class 'result__snippet'
    results = soup.find_all("a", class_="result__snippet")

    # Print the text content of each matching tag
    text_results = "".join('Search Result:\n' + result.get_text(strip=True) + '\n\n' for result in results)
        
    return text_resultsq