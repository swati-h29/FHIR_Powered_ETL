import requests
import json
from pathlib import Path
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
OPENEMR_PATIENT_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir/Patient"
OPENEMR_CONDITION_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir/Condition"

DATA_DIR = Path("data")
ACCESS_FILE = DATA_DIR / "access_token.json"

def get_access_token():
    with open(ACCESS_FILE) as f:
        return json.load(f)["access_token"]


def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }
def fetch_patients():
    url = OPENEMR_PATIENT_URL
    res = requests.get(url, headers=get_headers())
    if res.status_code != 200:
        print(f"Error: {res.status_code}, {res.text}")
    return res.json()



def fetch_conditions():
    url = OPENEMR_CONDITION_URL
    res = requests.get(url, headers=get_headers())
    if res.status_code != 200:
        print(f"Error: {res.status_code}, {res.text}")
    return res.json()



def plot_gender_distribution(genders):
    count = Counter(genders)
    print(f"Gender count: {count}")
    if not count:
        print("No gender data to plot.")
        return

    labels = list(count.keys())
    values = list(count.values())

    color_map = {'male': 'blue', 'female': 'pink', 'unknown': 'gray'}
    colors = [color_map.get(gender, 'gray') for gender in labels]

    plt.bar(labels, values, color=colors)
    plt.title("Patient Count by Gender")
    plt.xlabel("Gender")
    plt.ylabel("Number of Patients")
    plt.tight_layout()

    # Ensure saving to the correct directory
    output_dir = Path(__file__).parent / "data"  # Save to the 'data' folder in the current directory.
    output_dir.mkdir(parents=True, exist_ok=True)  # Create the folder if it doesn't exist.

    print(f"Saving the image to {output_dir / 'patient_count_by_gender.png'}")  # Debugging path
    plt.savefig(output_dir / "patient_count_by_gender.png")
    plt.show()


def plot_birth_decade_distribution(birth_dates):
    decades = []
    for date in birth_dates:
        try:
            year = int(date.split("-")[0])
            decade = f"{year // 10 * 10}s"
            decades.append(decade)
        except:
            continue

    count = Counter(decades)
    print(f"Decade count: {count}")
    if not count:
        print("No birth date data to plot.")
        return

    labels = sorted(count.keys())
    values = [count[d] for d in labels]

    plt.bar(labels, values, color="purple")
    plt.title("Patient Count by Birth Decade")
    plt.xlabel("Birth Decade")
    plt.ylabel("Number of Patients")
    plt.tight_layout()

    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Saving the image to {output_dir / 'patient_count_by_birth_decade.png'}")
    plt.savefig(output_dir / "patient_count_by_birth_decade.png")
    plt.show()


def main():
    data = fetch_patients()
    genders = []
    birth_dates = []

    print(f"Fetched Patient Data: {data}")

    if "entry" in data:
        for entry in data["entry"]:
            res = entry["resource"]
            gender = res.get("gender", "unknown").lower()
            genders.append(gender)
            if "birthDate" in res:
                birth_dates.append(res["birthDate"])

    print(f"Genders: {genders}")
    print(f"Birth Dates: {birth_dates}")

    if not genders or not birth_dates:
        print("Data is missing from the API response. Please check the API response.")
        return

    plot_gender_distribution(genders)
    plot_birth_decade_distribution(birth_dates)


if __name__ == "__main__":
    main()