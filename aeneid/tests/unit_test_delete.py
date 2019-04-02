import requests
import json

def test_json():
    #params = {"fields": "G_all,GS"}
    url = "http://127.0.0.1:5000/api/lahman2017/people/at3250"
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    r = requests.delete(url, headers=headers)
    print("Result = ")
    print(r.text)
    #print(json.dumps(r.json(), indent=2, default=str))

test_json()