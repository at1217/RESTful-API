#Amon Tokoro - at3250

import requests
import json

def test_json2():
    params = {"yearid": "1960",
              "fields": "ab,h"}
    url = 'http://127.0.0.1:5000/api/lahman2017/people/willite01/batting'
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    r = requests.get(url, headers=headers, params=params)
    print("Result = ")
    print(r.text)
    print(json.dumps(r.json(), indent=2, default=str))

test_json2()