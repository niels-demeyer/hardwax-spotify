import requests
import json
import os
import shutil
import html

# Directory for saving the output
directory_path = "outputs/reggae"
if os.path.exists(directory_path):
    shutil.rmtree(directory_path)
os.makedirs(directory_path)

base_url = "https://hardwax.com/records.json"
section_url = "https://hardwax.com/section/reggae.json"
headers = {
    #get your headers (use a program like insomnia )
}

all_results = []
page = 1


def unescape_html_entities(data):
    for item in data:
        if "html" in item:
            item["html"] = html.unescape(item["html"])
    return data


while True:
    # Fetch the paginated reggae section
    response = requests.get(f"{section_url}?page={page}", headers=headers)

    if response.status_code != 200:
        print(f"Error fetching page {page}: {response.status_code}")
        break

    # Extract slugs from the response
    data = response.json()
    slugs = data.get("results", [])

    # Print the fetched data for diagnosis
    print(f"Data for page {page}: {data}")
    print(f"Extracted slugs for page {page}: {slugs}")

    if not slugs:
        # No more results, break out of the loop
        break

    # Fetch specific records using the slugs
    slug_str = ",".join(slugs)
    records_response = requests.get(f"{base_url}?slugs={slug_str}", headers=headers)

    if records_response.status_code == 200:
        records_data = records_response.json()["results"]

        # Unescape HTML entities before adding to the results
        unescaped_records_data = unescape_html_entities(records_data)
        all_results.extend(unescaped_records_data)
    else:
        print(
            f"Error fetching records for slugs {slug_str}: {records_response.status_code}"
        )

    page += 1

# Save all the data to a JSON file
with open(f"{directory_path}/reggae_all.json", "w") as f:
    json.dump(all_results, f)

print(f"Total items fetched: {len(all_results)}")
