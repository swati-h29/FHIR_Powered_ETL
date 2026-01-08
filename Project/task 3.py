# TASK  3: Create Observation for Existing Patient in Primary Care FHIR Server
import requests
import json
from pathlib import Path
import datetime

FHIR_OBSERVATION_URL = "http://137.184.71.65:8080/fhir/Observation"
data_dir = Path("data")

# Loading access token from file
def get_access_token():
    with open(data_dir / "access_token.json") as f:
        return json.load(f).get("access_token")

# Build the headers
def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }

# Get patient ID from Task 1 output file
def read_patient_id(file_name="task1_patient_id.json"):
    """this reads the patient ID from the given JSON file created in Task 1."""
    try:
        with open(data_dir / file_name, "r") as f:
            patient_resource_id = json.load(f).get("patient_id")
        print(f"Patient ID read from file: {patient_resource_id}")
        return patient_resource_id
    except FileNotFoundError:
        print("Error: task1_patient_id.json file not found. Cannot link observation.")
        return None

# Create observation
def create_blood_pressure_observation(patient_id):
    """this creates a Blood Pressure observation and link it to the patient with id."""
    observation_payload = {
        "resourceType": "Observation",
        "id": patient_id,
        "meta": {
            "versionId": "1",
            "lastUpdated": datetime.date.today().isoformat(),
            "source": "#ytTzu9ovGo3hKfow",
            "profile": ["http://hl7.org/fhir/StructureDefinition/vitalsigns"]
        },
        "text": {
            "status": "generated"
        },
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
                "display": "Vital Signs"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "85354-9",
                "display": "Blood pressure panel with all children optional"
            }],
            "text": "Blood pressure systolic & diastolic"
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "effectiveDateTime": datetime.date.today().isoformat(),
        "performer": [{
            "reference": "Practitioner/8"
        }],
        "interpretation": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": "N",
                "display": "Normal"
            }],
            "text": "Normal Range"
        }],
        "bodySite": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "368209003",
                "display": "Right arm"
            }]
        },
        "component": [{
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "8480-6",
                    "display": "Systolic blood pressure"
                }]
            },
            "valueQuantity": {
                "value": 122 ,
                "unit": "mmHg",
                "system": "http://unitsofmeasure.org",
                "code": "mm[Hg]"
            },
            "interpretation": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "N",
                    "display": "normal"
                }],
                "text": "Normal"
            }]
        }, {
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "8462-4",
                    "display": "Diastolic blood pressure"
                }]
            },
            "valueQuantity": {
                "value": 83,
                "unit": "mmHg",
                "system": "http://unitsofmeasure.org",
                "code": "mm[Hg]"
            },
            "interpretation": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "N",
                    "display": "Normal"
                }],
                "text": "Normal Range"
            }]
        }]
    }

    # Sending the POST request to create the Blood Pressure Observation
    print(f"Sending request to create blood pressure observation for patient {patient_id}")
    response = requests.post(FHIR_OBSERVATION_URL, headers=get_headers(), json=observation_payload)

    if response.status_code == 201:
        observation_id = response.json().get("id")
        print(f"Blood Pressure observation successfully created {observation_id}")
    else:
        print(f"Failed to create observation. Status code: {response.status_code}, Error: {response.text}")

if __name__ == "__main__":
    patient_id = read_patient_id()
    if patient_id:
        create_blood_pressure_observation(patient_id)

