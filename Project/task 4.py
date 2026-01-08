# TASK 4: Create Procedure for Existing Patient in Primary Care FHIR Server

import requests
import json
from pathlib import Path
import datetime

# URLs
PRIMARY_PROCEDURE_URL = "http://137.184.71.65:8080/fhir/Procedure"

# Directory setup
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Load access token
def get_access_token():
    token_file = DATA_DIR / "access_token.json"
    if not token_file.exists():
        print("access_token.json not found")
        return None
    with open(token_file) as f:
        return json.load(f).get("access_token")

# Build headers
def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }

# Get patient ID from Task 1 output file
def get_task1_patient_id():
    file = DATA_DIR / "task1_patient_id.json"
    if not file.exists():
        print("task1_patient_id.json not found")
        return None
    with open(file) as f:
        patient_id = json.load(f).get("patient_id")
        print(f"Patient ID read from file: {patient_id}")
        return patient_id

# Create and post Procedure
def create_procedure(patient_id):
    procedure_payload = {
        "resourceType": "Procedure",
        "text": {
            "status": "generated",
            "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>Functional Endoscopic Sinus Surgery</p></div>"
        },
        "status": "completed",
        "code": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "1220582003",  # SCTID for Functional Endoscopic Sinus Surgery
                "display": "Functional Endoscopic Sinus Surgery (Procedure)"
            }],
            "text": "Functional Endoscopic Sinus Surgery"
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "performedDateTime": datetime.datetime.now().isoformat(),
        "recorder": {
            "reference": "Practitioner/8",
            "display": "Dr Adam Careful"
        },
        "performer": [{
            "actor": {
                "reference": "Practitioner/8",
                "display": "Dr Adam Careful"
            }
        }],
        "followUp": [{
            "text": "Post-operative care: Monitor for signs of infection, avoid nasal trauma."
        }],
        "note": [{
            "text": "Procedure completed without complications."
        }]
    }
    print(f"Sending request to create procedure for patient {patient_id}")
    res = requests.post(PRIMARY_PROCEDURE_URL, headers=get_headers(), json=procedure_payload)
    if res.status_code == 201:
        procedure_id = res.json().get("id")
        print(f"Procedure successfully created: {procedure_id}")
    else:
        print("Failed to create procedure:", res.status_code, res.text)

if __name__ == "__main__":
    patient_id = get_task1_patient_id()
    if patient_id:
        create_procedure(patient_id)
