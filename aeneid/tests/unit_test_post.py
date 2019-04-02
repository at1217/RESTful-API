#Amon Tokoro - at3250

import requests
import json


def test_json():
    url = 'http://127.0.0.1:5000/explain/body'
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    data = {"p": "cool"}
    r = requests.post(url, headers=headers, json=data)
    print("Result = ")
    print(json.dumps(r.json(), indent=2, default=str))

test_json()