import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
load_dotenv()

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
    
    print("Search Results:", text_results)
        
    return text_results
    
def search_tavily(query):
    # curl -X POST https://api.tavily.com/search \
    # -H 'Content-Type: application/json' \
    # -H 'Authorization: Bearer ' \
    # -d '{
    #     "query": ""
    # }'
    
    if not os.getenv('TAVILY_API_KEY'):
        raise ValueError("TAVILY_API_KEY environment variable is not set.")
    
    url = "https://api.tavily.com/search"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {os.getenv('TAVILY_API_KEY', '')}"
    }
    
    data = {
        "query": query
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"Error fetching results: {response.status_code} - {response.text}")
    results = response.json()
    
    res = []
        
    for result in results.get('results', []):
        res.append(result.get('content', ''))
        
    return "\n\n".join(res)

if __name__ == "__main__":
    query = "7229 S Hamlin Ave, Chicago, IL 60629"
    search_results = search_tavily(query)
    print(search_results)