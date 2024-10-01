import requests
from bs4 import BeautifulSoup
import json

def scrape_renewi_tour(url):
    # Send request to the webpage
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    stages = []
    current_stage = {}
    capture_race_summary = False
    capture_results = False

    # Loop through all <p> elements
    for p_tag in soup.find_all('p'):
        # Find <a> tag and check for "map-0" in href attribute to detect stage anchor points
        a_tag = p_tag.find('a')
        if a_tag and a_tag.get('href') and "map-" in a_tag['href']:
            if current_stage:  # Append the current stage before creating a new one
                stages.append(current_stage)
            current_stage = {
                'stage_name': p_tag.text.strip(),
                'total_summary': "",
                'result': "",
                'gc': "N/A",
                'others': "N/A"
            }

        # Start capturing race summary after encountering <strong>The race:</strong>
        if p_tag.find('strong') and "The race:" in p_tag.find('strong').text:
            capture_race_summary = True
            continue  # Skip to the next <p> element

        # Stop capturing race summary at <strong>Complete results:</strong> and start capturing results
        if p_tag.find('strong') and "Complete results:" in p_tag.find('strong').text:
            capture_race_summary = False
            capture_results = True
            continue

        # Stop capturing results when encountering <strong><img ... GC after stage</strong>
        if p_tag.find('strong') and p_tag.find('img') and "GC after stage" in p_tag.find('strong').text:
            capture_results = False

        # Append text to total summary if in race summary section
        if capture_race_summary:
            current_stage['total_summary'] += p_tag.text.strip() + " "

        # Capture the <tbody> tag content for result
        if capture_results:
            tbody_tag = p_tag.find_next('tbody')
            if tbody_tag:
                current_stage['result'] = str(tbody_tag)
                capture_results = False  # Stop capturing after we find the <tbody>

    # Append the last stage processed
    if current_stage:
        stages.append(current_stage)

    return json.dumps(stages, indent=4)

# URL of the Renewi Tour page
url = 'https://www.bikeraceinfo.com/stageraces/Benelux/2024-Renewi-Tour.html'
data = scrape_renewi_tour(url)
print(data)
