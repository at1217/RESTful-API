from aeneid.dbservices.RDBDataTable import RDBDataTable
import logging
logging.basicConfig(level=logging.DEBUG)
from aeneid.dbservices import dataservice as ds

# def test_create():
#     tbl = RDBDataTable("people")
#     print("test_create: tbl = ", tbl)


def test_create():

    result = ds.create("lahman2017.people",
                       {"playerID": "at3250", "nameLast": "Tokoro", "nameFirst":"Amon"})

    print("result: ", result)


test_create()


