from typing import Any

import requests
import json
import pickle

ICONS_URL = "https://github.com/Tomorrow-IO-API/tomorrow-weather-codes/raw/51b9588fa598d7a8fcf26798854e0d74708abcc4/V2_icons/large/png/"


def get_github_file_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Failed to download: {url}")
        return None


def get_github_files(permalink):
    response = requests.get(permalink)

    if response.status_code == 200:

        data = json.loads(response.content)

        items = data["payload"]['tree']['items']

        file_names = [item['name'] for item in items if item['contentType'] == 'file']

        return file_names

    else:
        print(f"Error: Unable to fetch data from the GitHub API. Status Code: {response.status_code}")
        return []


github_file_names: list[Any] = get_github_files("https://github.com/Tomorrow-IO-API/tomorrow-weather-codes/tree"
                                                "/51b9588fa598d7a8fcf26798854e0d74708abcc4/V2_icons/large/png")

# Dictionary to store file content (binary)
png_files = {}

# List of filenames you want to download
filenames = github_file_names

# Download each file and store content in the dictionary
for filename in filenames:
    url = ICONS_URL + filename
    content = get_github_file_content(url)
    if content:
        png_files[filename] = content

with open('data.pkl', 'wb') as f:
    pickle.dump(png_files, f)
