import requests
import json

def test_api_1():

    r = requests.get("http://127.0.0.1:5000")

    print("First REST API returned", r.text)

def test_json():
    params = {"nameLast": "Williams", "fields": "playerID, nameLast, nameFirst"}
    url = 'http://127.0.0.1:5000/api/lahman2017/people'
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    r = requests.get(url, headers=headers, params=params)
    print("Result = ")
    print(r.text)
    print(json.dumps(r.json(), indent=2, default=str))


def test_json2():
    url = 'http://127.0.0.1:5000/explain/body'
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    data = {"p": "cool"}
    r = requests.post(url, headers=headers, json=data)
    print("Result = ")
    print(json.dumps(r.json(), indent=2, default=str))





def test_json3():
    params = {"children": "appearances,batting,nameLast=Williams,batting.yearID=1960,appearances.yearID=1960",
              "fields": "playerID,nameLast,nameFirst,batting.AB,batting.H,appearances.G_all,appearances.GS"}
    url = 'http://127.0.0.1:5000/api/lahman2017/people'
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    r = requests.get(url, headers=headers, params=params)
    print("Result = ")
    print(r.text)
    print(json.dumps(r.json(), indent=2, default=str))



#test_api_1()
#test_json()
#test_json2()
test_json3()