#  TASK 2: Extract Child SNOMED Condition and Post to Primary Care FHIR Server

import requests
import json
from pathlib import Path
import datetime

# URLs
BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
PRIMARY_CONDITION_URL = "http://137.184.71.65:8080/fhir/Condition"
SNOMED_HERMES_URL = "http://159.65.173.51:8080/v1/snomed"

# Directory setup
DATA_DIR = Path("data")

# Loading access token from JSON file
def get_access_token():
    token_file = DATA_DIR / "access_token.json"
    if not token_file.exists():
        print("access_token.json not found")
        return None
    with open(token_file) as f:
        return json.load(f).get("access_token")

# Building headers
def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }

# Get patient ID from previously saved Task 1 response
def get_task1_patient_id():
    file = DATA_DIR / "task1_patient_id.json"
    if not file.exists():
        print(" task1_patient_id.json not found")
        return None
    with open(file) as f:
        return json.load(f).get("patient_id")

# Retrieve SNOMED code from Task 1 condition

def get_task1_conditions():
    file = DATA_DIR / "disorder_conditions.json"
    if not file.exists():
        print("disorder_conditions.json not found")
        return None
    with open(file) as f:
        disorder_conditions = json.load(f)
        return disorder_conditions

# Get child SNOMED concept
def get_snomed_child(code):
    url = f"{SNOMED_HERMES_URL}/search?constraint=<< {code}"
    res = requests.get(url)

    if res.status_code == 200 and res.json():
        save_json(res.json(), "child_conditions")
        child_code = res.json()[0]['conceptId']
        child_term = res.json()[0]['preferredTerm']

        # Get properties of the parent concept
        url_child = f"{SNOMED_HERMES_URL}/concepts/{child_code}/properties?expand=0&format=id:syn" #query to find finding site of child condition
        res_child = requests.get(url_child)

        if res_child.status_code == 200 and res_child.json():
            properties = res_child.json()
            finding_site_code = None
            finding_site_term = None

            # Looping through all keys to find the Finding site property
            for key, value in properties.items():
                if isinstance(value, dict):
                    for prop_key, prop_value in value.items():
                        if "Finding site" in prop_key:
                            # Found it, now parsing the code and term
                            if ":" in prop_value:
                                finding_site_code, finding_site_term = prop_value.split(":", 1)
                                finding_site_code = finding_site_code.strip()
                                finding_site_term = finding_site_term.strip()
                            break  # Exiting once found

            return child_code, child_term, finding_site_code, finding_site_term

    return None, None, None, None

# Function to save JSON
def save_json(obj, name):
    with open(DATA_DIR / f"{name}.json", "w") as f:
        json.dump(obj, f, indent=2)


# Main task 2 function
def main():
    patient_id = get_task1_patient_id()
    print(patient_id)
    if not patient_id:
        return

    task1_conditions = get_task1_conditions()
    snomed_code = task1_conditions[0]['snomed_code']
    con_verification = task1_conditions[0]['verification']

    print("Selected SNOMED:", snomed_code)

    child_code, child_term, finding_site_code, finding_site_term = get_snomed_child(snomed_code)
    print(child_code, child_term)
    if not child_code:
        print("No child SNOMED found.")
        return

    condition_payload = {
        "resourceType": "Condition",
        "id": "cond2",
        "meta": {
            "profile": ["http://example.org/StructureDefinition/my-condition-profile"]
        },
        "text": {
            "status": "generated",
            "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>Hello</p></div>"
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "code": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": str(child_code),
                "display": child_term
            }],
            "text": child_term
        },
        "clinicalStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": "active"
            }]
        },
        "onsetDateTime": datetime.datetime.now().astimezone().isoformat(),
        "verificationStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": con_verification
            }]
        },
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                "code": "encounter-diagnosis",
                "display": "Encounter Diagnosis"
            }]
        }],
        "severity": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "24484",
                "display": "Severe"
            }]
        },
        "bodySite": [{
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": finding_site_code,
                "display": finding_site_term
            }],
            "text": finding_site_term
        }]
    }

    response = requests.post(PRIMARY_CONDITION_URL, headers=get_headers(), json=condition_payload)
    if response.status_code != 201:
        print("Failed to post child condition.", response.text)
        return
    print("Child Condition Created:", response.json()['id'])

    save_json(condition_payload, "child_condition_payload")
    print("Saved child_condition_payload.json for validation.")

if __name__ == "__main__":
    main()