from flask import Flask
from aeneid.dbservices import dataservice as ds
from flask import Flask
from flask import request
import os
import json
import copy
from aeneid.utils import utils as utils
import re
from aeneid.utils import webutils as wu
from aeneid.dbservices.DataExceptions import DataException
from flask import Response
from urllib.parse import urlencode


# Default delimiter to delineate primary key fields in string.
key_delimiter = "_"


app = Flask(__name__)

def compute_links(result,limit,offset):

    result['links'] = []

    self = {"rel": "self", "href": request.url}
    result['links'].append(self)

    next_offset = int(offset) + int(limit)

    base = request.base_url
    args = {}
    for k, v in request.args.items():
        if not k == 'offset':
            args[k] = v
        else:
            args[k] = next_offset

    params = urlencode(args)
    self = {"rel": "next", "href": base + "?" + params}
    result['links'].append(self)

    return result



@app.route('/')
def hello_world():
    return """
            You probably want to go either to the content home page or call an API at /api.
            When you despair during completing the homework, remember that
            Audentes fortuna iuvat.
            """

@app.route('/explain', methods=['GET', 'PUT', 'POST', 'DELETE'])
def explain_what():

    result = "Explain what?"
    response = Response(result, status=200, mimetype="text/plain")

    return response

@app.route('/explain/<concept>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def explain(concept):

    mt = "text/plain"

    if concept == "route":
        result = """
                    A route definition has the form /x/y/z.
                    If an element in the definition is of the for <x>,
                    Flask passes the element's value to a parameter x in the function definition.
                    """
    elif concept == 'request':
        result = """
                http://flask.pocoo.org/docs/1.0/api/#incoming-request-data
                explains the request object.
            """
    elif concept == 'method':
        method = request.method

        result = """
                    The @app.route() example shows how to define eligible methods.
                    explains the request object. The Flask framework request.method
                    is how you determine the method sent.
                    
                    This request sent the method:
                    """ \
                    + request.method
    elif concept == 'query':
        result = """
                    A query string is of the form '?param1=value1&param2=value2.'
                    Try invoking ' http://127.0.0.1:5000/explain/query?param1=value1&param2=value2.
                    
                """

        if len(request.args) > 0:
            result += """
                Query parameters are:
                """
            qparams = str(request.args)
            result += qparams
    elif concept == "body":
        if request.method != 'PUT' and request.method != 'POST':
            result = """
                Only PUT and POST have bodies/data.
            """
        else:
            result = """
                The content type was
            """ + request.content_type

            if "text/plain" in request.content_type:
                result += """
                You sent plain text.
                
                request.data will contain the body.
                
                Your plain text was:
                
                """ + str(request.data) + \
                """
                
                Do not worry about the b'' thing. That is Python showing the string encoding.
                """
            elif "application/json" in request.content_type:
                js = request.get_json()
                mt = "application/json"
                result = {
                    "YouSent": "Some JSON. Cool!",
                    "Note": "The cool kids use JSON.",
                    "YourJSONWas": js
                }
                result = json.dumps(result, indent=2)
            else:
                """
                I have no idea what you sent.
                """
    else:
        result = """
            I should not have to explain all of these concepts. You should be able to read the documents.
        """

    response = Response(result, status=200, mimetype=mt)

    return response

@app.route('/api')
def api():
    return 'You probably want to call an API on one of the resources.'


@app.route('/api/<dbname>/<resource_name>/<primary_key>', methods=['GET','PUT','DELETE'])
def handle_resource(dbname, resource_name, primary_key):

    resp = Response("Internal server error", status=500, mimetype="text/plain")

    try:

        # The design pattern is that the primary key comes in in the form value1_value2_value3
        key_columns = primary_key.split(key_delimiter)

        # Merge dbname and resource names to form the dbschema.tablename element for the resource.
        # This should probably occur in the data service and not here.
        resource = dbname + "." + resource_name

        if request.method == 'GET':

            # Look for the fields=f1,f2, ... argument in the query parameters.
            field_list = request.args.get('fields', None)
            if field_list is not None:
                field_list = field_list.split(",")

            # Call the data service layer.
            result = ds.get_by_primary_key(resource, key_columns, field_list=field_list)

            if result:
                # We managed to find a row. Return JSON data and 200
                result_data = json.dumps(result, default=str)
                resp = Response(result_data, status=200, mimetype='application/json')

            else:
                resp = Response("NOT FOUND", status=404, mimetype='text/plain')

        elif request.method == 'DELETE':
            result = ds.delete(resource, key_columns)
            if result and result >= 1:
                resp = Response("DELETED", status=200, mimetype='text/plain')
            else:
                resp = Response("NOT FOUND", status=404, mimetype='text/plain')

        else:
            resp = Response("I am a teapot that will not PUT", status=422, mimetype="text/plain")



    except Exception as e:
        # We need a better overall approach to generating correct errors.
        utils.debug_message("Something awlful happened, e = ", e)

    return resp

@app.route('/api/<dbname>/<resource_name>', methods=['GET','POST'])
def handle_collection(dbname, resource_name):

    resp = Response("Internal server error", status=500, mimetype="text/plain")

    result = None
    e = None
    #context = get_context()

    try:

       # children = context.get("children",None)
       #  if children is not None:
       #      resp = handle_path(dbname,resource_name,context)
       #
       #  else:

            # Form the compound resource names dbschema.table_name
            resource = dbname + "." + resource_name

            if request.method == "GET":

                children = request.args.get('children', None)
                if children is not None:
                    children = children.split(",")

                    key_names, table_name = create_key_table_name(children, resource_name)


                    new_key_name = []
                    for i in range(len(key_names)):
                        new_key_name.append(key_names[i].split("="))

                    dic = dict(new_key_name)
                    # print(dic)
                    dict_list = []
                    for key, value in dic.items():
                        temp = {key: value}
                        dict_list.append(temp)



                # Get the field list if it exists.
                field_list = request.args.get('fields', None)
                if field_list is not None:
                    field_list = field_list.split(",")

                    parent_fields, child1_fields, child2_fields = create_fields(field_list, table_name)


                    dic_key = create_dictionary(dic,table_name)

                    del dic_key["nameLast"]






                # limit = request.args.get('limit', None)
                # offset = request.args.get('offset', None)
                # order_by = request.args.get('order_by', None)
                #
                # if limit:
                #     limit=int(limit)
                #
                # if offset:
                #     offset=int(offset)
                #
                # # The query string is of the form ?f1=v1&f2=v2& ...
                # # This maps to a query template of the form { "f1" : "v1", ... }
                # # We need to ignore the fields parameters.
                # tmp = None
                # for k,v in request.args.items():
                #     if (not k == 'fields') and (not k == 'limit') and (not k == 'offset') and \
                #                 (not k == 'order_by'):
                #         if tmp is None:
                #             tmp = {}
                #         tmp[k] = v

                # Find by template.
                first_result = ds.get_by_template(resource, dict_list[0], field_list=parent_fields)


                playerid = get_playerid(first_result)
                id_dic = create_pair_for_playerid(playerid)

                new_key = new_id_dic(id_dic, dic_key)



                child1_name = dbname + "." + table_name[1]
                child2_name = dbname + "." + table_name[2]

                child1_fields.insert(0,'playerID')
                child2_fields.insert(0, 'playerID')



                second = second_temp(new_key,child1_name,child1_fields)

                third = second_temp(new_key,child2_name,child2_fields)

                first_final = find_final_temp(first_result)

                second_final = find_final_temp(second)
                del second_final['playerID']

                third_final = find_final_temp(third)
                del third_final['playerID']

                # new_pair = extract_only_key(dict_list)
                #
                # second_result = ds.get_by_template(child1_name, new_pair[1], field_list=child1_fields)
                #
                # third_result = ds.get_by_template(child2_name, new_pair[2], field_list=child2_fields)





                if first_final and second_final and third_final:
                    result = final_temp(first_final,second_final,third_final)
                    #result = compute_links(result)
                    result_data = json.dumps(result, default=str)
                    resp = Response(result_data, status=200, mimetype='application/json')
                else:
                    resp = Response("Not found", status=404, mimetype="text/plain")

            elif request.method == "POST":

                new_r = request.get_json()
                result = ds.create(resource, new_r)
                if result is not None and result == 1:
                    resp = Response("CREATED", status=201, mimetype="text/plain")
    except Exception as e:
        utils.debug_message("Something awlful happened, e = ", e)

    return resp



@app.route('/api/<dbname>/<table_name>/<primary_key>/<table2_name>', methods=['GET'])
def handle_two_table(dbname, table_name, primary_key, table2_name):

    resp = Response("Internal server error", status=500, mimetype="text/plain")

    primary_key = primary_key.split(key_delimiter)
    #print(list(key_columns))



    try:
        parent_resource = dbname + "." + table_name
        child_resource = dbname + "." + table2_name
        #print(list(primary_key))

        table1 = ds.get_by_primary_key(parent_resource, primary_key)
        #table2 = ds.get_by_primary_key(child_resource, primary_key)


        if request.method == "GET":
            # Get the field list if it exists.
            field_list = request.args.get('fields', None)
            if field_list is not None:
                field_list = field_list.split(",")


            tmp = None
            for k, v in request.args.items():
                if (not k == 'fields') and (not k == 'limit') and (not k == 'offset') and \
                        (not k == 'order_by'):
                    if tmp is None:
                        tmp = {}
                    tmp[k] = v

            tmp2 = None
            for k, v in table1.items():
                if(v == primary_key[0]):
                    if tmp2 is None:
                        tmp2 = {}
                    tmp2[k] = v
                    break


            new_temp = merge_two_dicts(tmp,tmp2)
            result = ds.get_by_template(child_resource, new_temp, field_list=field_list)



            if result:
                result = {"data": result}
                #result = compute_links(result)
                result_data = json.dumps(result, default=str)
                resp = Response(result_data, status=200, mimetype='application/json')
            else:
                resp = Response("Not found", status=404, mimetype="text/plain")

    except Exception as e:
        utils.debug_message("Something awlful happened, e = ", e)

    return resp





def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


def unique(list):
    unique_list = []

    for x in list:

        if x not in unique_list:
            unique_list.append(x)

    return unique_list

def remove_table_name(list,table_name):
    for i in range(len(list)):


        for j in range(len(table_name)):
            if(table_name[j] in list[i]):
                remove = table_name[j] + "."
                list[i] = list[i].replace(remove,'')

    return list
def create_fields(field_list, table_name):
    parent_fields = []
    children_fields = []

    for i in range(len(field_list)):
        for j in range(len(table_name)):

            if (table_name[j] not in field_list[i]):
                if "." in field_list[i]:
                    continue
                else:

                    parent_fields.append(field_list[i])
            else:
                children_fields.append(field_list[i])

    parent_fields = unique(parent_fields)

    child1_fields = []
    child2_fields = []

    for i in range(len(children_fields)):

        if table_name[1] in children_fields[i]:
            child1_fields.append(children_fields[i])
        else:
            child2_fields.append(children_fields[i])

    child1_fields = unique(child1_fields)
    child2_fields = unique(child2_fields)

    child1_fields = remove_table_name(child1_fields, table_name)
    child2_fields = remove_table_name(child2_fields, table_name)

    return parent_fields, child1_fields, child2_fields

def create_key_table_name(children ,resource_name):
    key_names = []
    table_name = []
    for i in range(len(children)):
        if '=' in children[i]:

            key_names.append(children[i])
        else:

            table_name.append(children[i])

    table_name.insert(0, resource_name)

    return key_names, table_name

def create_dictionary(dictionary,table_name):
    dic_key = {}
    for k, v in dictionary.items():
        for j in range(len(table_name)):
            if '.' not in k:
                # if table_name[j] not in k:
                dic_key[k] = v

            else:
                if table_name[j] in k:
                    remove = table_name[j] + "."
                    k = k.replace(remove, '')
                    dic_key[k] = v

    return dic_key

def extract_only_key(list_of_dict):
    for dic in list_of_dict:
        for key, value in list(dic.items()):
            if '.' in key:
                new_key = key[key.find('.') + 1:]

                dic.pop(key)
                dic[new_key] = value

                dic = list_of_dict
            else:
                continue
    return dic

def get_playerid(dictionary):
    playerid_list = []
    for dic in dictionary:
        for k, v in dic.items():
            if k == 'playerID':
                playerid_list.append(v)
            else:
                continue
    return playerid_list


def create_pair_for_playerid(list):
    key = 'playerID'
    new_list = []
    for i in range(len(list)):
        case = {key: list[i]}
        new_list.append(case)
    return new_list

def second_temp(dic, child1_name, child1_fields):
    new_list = []

    for i in dic:
        new = ds.get_by_template(child1_name, i, field_list=child1_fields)
        if isinstance(new, tuple):
            continue
        else:
            a = dict((key, d[key]) for d in new for key in d)
            new_list.append(a)

    return new_list

def find_final_temp(temp):

    for i in temp:
        for k,v in i.items():
            if (k == 'playerID' and v == 'willite01'):

                    row = i
                    break
            else:
                continue
    return row

def new_id_dic(original, new):
    for i in original:
        i.update(new)

    return original

def final_temp(first,second,third):
    first = {'people': first}
    second = {'batting': second}
    third = {'appearances': third}

    a = []
    a.append(first)
    a.append(second)
    a.append(third)

    return a

if __name__ == '__main__':
    app.run(debug='True')
