#  TASK 1: Here we will Extract, Transform, Load (ETL) and save to  JSON files
import random
import requests
import json
from pathlib import Path
import datetime

# These are the FHIR & SNOMED servers
BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
PRIMARY_PATIENT_URL = "http://137.184.71.65:8080/fhir/Patient"
PRIMARY_CONDITION_URL = "http://137.184.71.65:8080/fhir/Condition"
SNOMED_HERMES_URL = "http://159.65.173.51:8080/v1/snomed"

# Setting up Data directory setup
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)


# Loading access token from JSON file
def get_access_token():
    token_file = data_dir / "access_token.json"
    if not token_file.exists(): #this is to handle error when the access token is not found
        print("access_token.json not found")
        return None
    with open(token_file) as f:
        return json.load(f).get("access_token")


# Creating headers for API requests
def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }


# Searching for patient in OpenEMR by name
def search_patient_by_name(name):
    url = f"{BASE_URL}/Patient?name={name}"
    res = requests.get(url, headers=get_headers())
    if res.status_code == 200 and 'entry' in res.json():
        return res.json()['entry'][0]['resource']
    print("No patient found.") #if api call fails, and we don't get a successful response
    return None


# Searching for patient in OpenEMR by name and gender
def search_patient_by_name_gender(name_string, gender):
    url = f'{BASE_URL}/Patient?name={name_string}&gender={gender}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data = response.json()
    if 'entry' in data:
        entry = data['entry']
        for item in entry:
            resource_id = item['resource']['id']
            given_name = f"{item['resource']['name'][0]['given'][0]}"
            family_name = f"{item['resource']['name'][0]['family']}"
            print(f"{resource_id} - {item['resource']['gender']} - {given_name} {family_name}")
    else:
        print('No results found')


# Retrieving SNOMED code from patient's condition

def get_condition_snomed(patient_id):
    url = f"{BASE_URL}/Condition?patient={patient_id}"
    res = requests.get(url, headers=get_headers())
    data = res.json()
    if res.status_code == 200 and 'entry' in data:
        save_json(data, "all_conditions")  # saved all conditions in this json file
        disorder_conditions = []

        for entry in data.get('entry', []):
            resource = entry.get('resource', {})
            code_codings = resource.get('code', {}).get('coding', [])
            display = code_codings[0].get('display', '')
            if '(disorder)' in display:
                disorder_conditions.append({
                    'condition_id': resource.get('id'),
                    'snomed_code': code_codings[0].get('code'),
                    'display': display,
                    'verification': resource.get('verificationStatus', {}).get('coding', [])[0].get('code')
                })
        save_json(disorder_conditions, "disorder_conditions")
        return disorder_conditions
    return None


# Get parent SNOMED concept
def get_snomed_parent(code):
    url = f"{SNOMED_HERMES_URL}/search?constraint=>!{code.strip()}"
    res = requests.get(url)

    if res.status_code == 200 and res.json():
        save_json(res.json(), "parent_conditions")
        parent_code = res.json()[0]['conceptId']
        parent_term = res.json()[0]['preferredTerm']

        # Get properties of the parent concept
        url_parent = f"{SNOMED_HERMES_URL}/concepts/{parent_code}/properties?expand=0&format=id:syn"
        res_parent = requests.get(url_parent)

        if res_parent.status_code == 200 and res_parent.json():
            properties = res_parent.json()
            finding_site_code = None
            finding_site_term = None

            # Looping through all keys to find the Finding site property
            for key, value in properties.items():
                if isinstance(value, dict):
                    for prop_key, prop_value in value.items():
                        if "Finding site" in prop_key:
                            # Found it, now parse the code and term
                            if ":" in prop_value:
                                finding_site_code, finding_site_term = prop_value.split(":", 1)
                                finding_site_code = finding_site_code.strip()
                                finding_site_term = finding_site_term.strip()
                            break  # Exit once found

            return parent_code, parent_term, finding_site_code, finding_site_term

    return None, None, None, None


# Format address
def combined_address(addr):
    return f"{', '.join(addr.get('line', []))} {addr.get('city', '')}, {addr.get('district', '')}, {addr.get('state', '')} {addr.get('postalCode', '')}".strip(
        ', ')


# Saving JSON file locally
def save_json(obj, name):
    with open(data_dir / f"{name}.json", "w") as f:
        json.dump(obj, f, indent=2)


# Main Task 1 function
def main():
    patient_data = search_patient_by_name("Criselda")
    if not patient_data:
        return # if there's no patient with this name

    search_patient_by_name_gender(name_string='Criselda', gender='female')

    #    Extract all conditions and select one disorder condition as the main condition
    disorder_conditions = get_condition_snomed(patient_data['id'])
    snomed_code = disorder_conditions[0]['snomed_code']  # this will call the first disorder condition
    con_verification = disorder_conditions[0]['verification'] #from main disorder to use for posting
    print("Selected SNOMED:", snomed_code) #saved the snomed code of the main disorder condition in snomed_code variable

    #Extract parent condition of the main disorder condition of patient
    parent_code, parent_term, finding_site_code, finding_site_term = get_snomed_parent(snomed_code)
    print(parent_code, parent_term)
    if not parent_code:
        print("No parent SNOMED found.")
        return

    # Create json structure to Post Patient to Primary care EHR
    patient_payload = {
        "resourceType": "Patient",
        "meta": {
            "profile": ["http://example.org/StructureDefinition/my-patient-profile"]
        },
        "text": {
            "status": "generated",
            "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>Hello</p></div>"
        },
        "identifier": [{
            "use": "usual",
            "type": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                    "code": "MR"
                }]
            },
            "system": "urn:oid:1.2.36.146.595.217.0.1",
            "value": str(random.randint(10000, 99999)),
            "period": {
                "start": datetime.datetime.now().astimezone().isoformat()
            }
        }],
        "active": True,
        "name": patient_data['name'],
        "gender": patient_data.get("gender"),
        "birthDate": patient_data.get("birthDate"),
        "deceasedBoolean": False,
        "address": [{
            "text": combined_address(addr),
            "line": addr.get("line", []),
            "city": addr.get("city"),
            "district": addr.get("district", "DefaultDistrict"),
            "state": addr.get("state"),
            "postalCode": addr.get("postalCode"),
            "period": {
                "start": datetime.datetime.now().astimezone().isoformat()
            }
        } for addr in patient_data.get("address", [])]
    }

    res_patient = requests.post(PRIMARY_PATIENT_URL, headers=get_headers(), json=patient_payload)
    if res_patient.status_code != 201:
        print(" Failed to post patient.") #error handling
        return
    patient_id = res_patient.json()['id']
    print(" Patient created:", patient_id)
    # Saved patient_id for future
    with open(data_dir / "task1_patient_id.json", "w") as f:
        json.dump({"patient_id": patient_id}, f)

    # Create and POST Condition
    condition_payload = {
        "resourceType": "Condition",
        "id": "cond1",
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
                "code": str(parent_code),
                "display": parent_term
            }],
            "text": parent_term
        },
        "clinicalStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": "active"
            }]
        },
        "onsetDateTime": "2020-05-20",
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

    res_cond = requests.post(PRIMARY_CONDITION_URL, headers=get_headers(), json=condition_payload)
    if res_cond.status_code != 201:
        print("Failed to post condition.")
        return
    print(" Condition created:", res_cond.json()['id'])

    # Saved both as JSON
    save_json(patient_payload, "patient_details_payload")
    save_json(condition_payload, "parent_condition_payload")
    print(" Saved patient_details_payload.json and parent_condition_payload.json. Now run validation script.")


if __name__ == "__main__":
    main()
