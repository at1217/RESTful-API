#Amon Tokoro - at3250

import requests
import json

def test_json3():
    params = {"children": "appearances,batting,nameLast=Williams,batting.yearID=1960,appearances.yearID=1960",
              "fields": "playerID,nameLast,nameFirst,batting.AB,batting.H,appearances.G_all,appearances.GS"}
    url = 'http://127.0.0.1:5000/api/lahman2017/people'
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    r = requests.get(url, headers=headers, params=params)
    print("Result = ")
    print(r.text)
    print(json.dumps(r.json(), indent=2, default=str))

test_json3()