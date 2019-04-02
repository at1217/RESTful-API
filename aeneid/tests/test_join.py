import requests
import json

def test_join_by_primary_key():
    url = '127.0.0.1:5000/api/lahman2017/people/willite01/batting?fields=ab,h&yearid=1960'
    headers = {'Content-Type': 'application/json; charset=utf-8'}