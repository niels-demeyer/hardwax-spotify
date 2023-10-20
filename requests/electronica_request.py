import requests
import json
import os
import shutil
import html

# Delete the previous files
directory_path = "outputs/electronica"
if os.path.exists(directory_path):
    shutil.rmtree(directory_path)

url = "https://hardwax.com/electronica.json"

payload = ""
headers = {
    #get your headers (use a program like insomnia )
}

page = 1
results_count = 0

if not os.path.exists(directory_path):
    os.makedirs(directory_path)


def unescape_html_entities(data):
    for item in data:
        if "html" in item["result"]:
            item["result"]["html"] = html.unescape(item["result"]["html"])
    return data


while True:
    querystring = {"page": str(page), "view": "true"}
    response = requests.request(
        "GET", url, data=payload, headers=headers, params=querystring
    )

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        break

    # Unescape HTML entities before saving
    data = response.json()
    unescaped_data = unescape_html_entities(data["response"]["results"])

    with open(f"{directory_path}/electronica_{page}.json", "w") as f:
        json.dump(response.json(), f)

    page_results_count = len(response.json()["response"]["results"])
    results_count += page_results_count
    print(f"Page {page} contains {page_results_count} items.")

    try:
        if not response.json()["response"]["next"]:
            break
    except KeyError:
        print("No more pages to visit.")
        break

    page += 1

print(f"\nTotal number of items: {results_count}")

# Join all the results into a single JSON file
all_results = []
for page in range(1, results_count // 32 + 2):
    with open(f"{directory_path}/electronica_{page}.json", "r") as f:
        all_results.extend(json.load(f)["response"]["results"])

with open(f"{directory_path}/electronica_all.json", "w") as f:
    json.dump(all_results, f)
