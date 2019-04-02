#Amon Tokoro - at3250

from aeneid.dbservices.BaseDataTable import BaseDataTable
from aeneid.dbservices.DerivedDataTable import DerivedDataTable
from aeneid.dbservices.DataExceptions import DataException
#from aeneid.dbservices import dataservice as ds
import pandas as pd
import logging
import operator
import json




import pymysql


class RDBDataTable(BaseDataTable):
    """
    RDBDataTable is relation DB implementation of the BaseDataTable.
    """

    # Default connection information in case the code does not pass an object
    # specific connection on object creation.
    #
    # You must replace with your own schema, user id and password.
    #
    _default_connect_info = {
        'host': 'localhost',
        'user': 'dbuser',
        'password': 'dbuserdbuser',
        'db': 'lahman2017',
        'port': 3306
    }

    def __init__(self, table_name, key_columns=None, connect_info=None, debug=True):
        """

        :param table_name: The name of the RDB table.
        :param connect_info: Dictionary of parameters necessary to connect to the data.
        :param key_columns: List, in order, of the columns (fields) that comprise the primary key.
        """

        # Initialize and store information in the parent class.
        super().__init__(table_name, connect_info, key_columns, debug)

        # If there is not explicit connect information, use the defaults.
        if connect_info is None:
            self._connect_info = RDBDataTable._default_connect_info

        # Create a connection to use inside this object. In general, this is not the right approach.
        # There would be a connection pool shared across many classes and applications.
        self._cnx = pymysql.connect(
            host=self._connect_info['host'],
            user=self._connect_info['user'],
            password=self._connect_info['password'],
            db=self._connect_info['db'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor)

        #print("table_name",table_name)
        #print("key_column",self._key_columns)


        #if self._key_columns is not None:
            #print("Thank you for your input but I can figure the keys out by myself")

        self._key_columns = self._get_primary_key_definition()


        self._related_resources = None

        tn = self._table_name.split('.')
        #print("tn ", tn)
        if len(tn) == 1:
            self._schema = self._connect_info['db']
            self._table = tn[0]

        else:
            self._schema = tn[0]
            self._table = tn[1]


        self._load_foreign_key_info()


        # except Exception as e:
        #     raise(DataTableException(None,None,e))


        #self._key_columns = self._get_primary_key_columns()

    def debug_message(self, *m):
        """
        Prints some debug information if self._debug is True
        :param m: List of things to print.
        :return: None
        """
        #if self._debug:
            #print(" *** DEBUG:", *m)

    def __str__(self):
        """

        :return: String representation of the data table.
        """
        result = "RDBDataTable: table_name = " + self._table_name
        result += "\nTable type = " + str(type(self))
        result += "\nKey fields: " + str(self._key_columns)

        # Find out how many rows are in the table.
        q1 = "SELECT count(*) as count from " + self._table_name
        r1 = self._run_q(q1, fetch=True, commit=True)
        result += "\nNo. of rows = " + str(r1[0]['count'])

        # Get the first five rows and print to show sample data.
        # Query to get data.
        q = "select * from " + self._table_name + " limit 5"

        # Read into a data frame to make pretty print easier.
        df = pd.read_sql(q, self._cnx)
        result += "\nFirst five rows:\n"
        result += df.to_string()

        return result

    def _run_q(self, q, args=None, fields=None, fetch=True, cnx=None, commit=True):
        """

        :param q: An SQL query string that may have %s slots for argument insertion. The string
            may also have {} after select for columns to choose.
        :param args: A tuple of values to insert in the %s slots.
        :param fetch: If true, return the result.
        :param cnx: A database connection. May be None
        :param commit: Do not worry about this for now. This is more wizard stuff.
        :return: A result set or None.
        """

        # Use the connection in the object if no connection provided.
        if cnx is None:
            cnx = self._cnx

        # Convert the list of columns into the form "col1, col2, ..." for following SELECT.
        if fields:
            q = q.format(",".join(fields))

        cursor = cnx.cursor()  # Just ignore this for now.

        # If debugging is turned on, will print the query sent to the database.
        self.debug_message("Query = ", cursor.mogrify(q, args))

        r = cursor.execute(q, args)  # Execute the query.

        # Technically, INSERT, UPDATE and DELETE do not return results.
        # Sometimes the connector libraries return the number of created/deleted rows.
        if fetch:
            r = cursor.fetchall()  # Return all elements of the result.
        else:
            # r = None
            pass

        if commit:  # Do not worry about this for now.
            cnx.commit()

        return r

    def _run_insert(self, table_name, column_list, values_list, cnx=None, commit=False):
        """

        :param table_name: Name of the table to insert data. Probably should just get from the object data.
        :param column_list: List of columns for insert.
        :param values_list: List of column values.
        :param cnx: Ignore this for now.
        :param commit: Ignore this for now.
        :return:
        """
        try:
            q = "insert into " + table_name + " "

            # If the column list is not None, form the (col1, col2, ...) part of the statement.
            if column_list is not None:
                q += "(" + ",".join(column_list) + ") "

            # We will use query parameters. For a term of the form values(%s, %s, ...) with one slot for
            # each value to insert.
            values = ["%s"] * len(values_list)

            # Form the values(%s, %s, ...) part of the statement.
            values = " ( " + ",".join(values) + ") "
            values = "values" + values

            # Put all together.
            q += values

            result = self._run_q(q, args=values_list, fields=None, fetch=False, cnx=cnx, commit=True)

            return result

        except Exception as e:
            print("Got exception = ", e)
            raise e

    def _get_primary_key_columns(self):
        """

        :return: The names of the primary key columns in the form ['col1', ..., 'coln']

        The current implementation just returns the list of keys passed in the constructor.
        An extended implementation would/should query database data/metadata to get the information.
        """
        q = "SHOW KEYS FROM " + self._table_name + " WHERE KEY_name = 'PRIMARY'"
        rows = self._run_q(q, args=None)

        keys = [r["Column_name"] for r in rows]

        return keys


    def find_by_primary_key(self, key_fields, field_list=None):
        """

        :param key_fields: The values for the key_columns, in order, to use to find a record.
        :param field_list: A subset of the fields of the record to return.
        :return: None, or a dictionary containing the request fields for the record identified
            by the key.
        """

        # Get the key_columns specified on table create.
        key_columns = self._get_primary_key_columns()

        #key_fields = list(key_fields)
        #key_fields = ''.join(key_fields)
        #print(key_fields)

        # Zipping together key_columns and passed fields produces a valid template
        tmp = dict(zip(key_columns, key_fields))
        #print(tmp)
        # Call find_by_template. This returns a DerivedDataTable.
        result = self.find_by_template(tmp, field_list)

        # For various reasons, we do not return a DerivedDataTable for find_by_primary_key().
        # We return the single row. This follows REST semantics.
        if result is not None:
            result = result.get_rows()

            if result is not None and len(result) > 0:
                result = result[0]
            else:
                result = None

        return result

    def _get_extras(self, limit=None, offset=None, order_by=None):
        result = ' '
        if order_by:
            result += ' order by ' + order_by + ' '
        if limit:
            result += ' limit ' + str(limit)
        if offset:
            result += ' offset ' + str(offset)

        return result

    def _template_to_where_clause(self, t):
        """
        Convert a query template into a WHERE clause.
        :param t: Query template.
        :return: (WHERE clause, arg values for %s in clause)
        """
        terms = []
        args = []
        w_clause = ""

        # The where clause will be of the for col1=%s, col2=%s, ...
        # Build a list containing the individual col1=%s
        # The args passed to +run_q will be the values in the template in the same order.
        for k, v in t.items():
            temp_s = k + "=%s "
            terms.append(temp_s)
            args.append(v)

        if len(terms) > 0:
            w_clause = "WHERE " + " AND ".join(terms)
        else:
            w_clause = ""
            args = None

        return w_clause, args

    def _project(self, rows, field_list):

        return rows

        pass

        """
        result = []

        if field_list is None:
            result = rows
        else:
            for r in rows:
                new_r = {f: r[f] for f in field_list}
                result.append(new_r)

        return result
        """

    def find_by_template(self, template, field_list=None, limit=None,
                         offset=None, order_by=None, follow_paths=False,
                         commit=True):
        """

        :param template: A dictionary of the form { "field1" : value1, "field2": value2, ...}
        :param field_list: A list of request fields of the form, ['fielda', 'fieldb', ...]
        :param limit: Do not worry about this for now.
        :param offset: Do not worry about this for now.
        :param order_by: Do not worry about this for now.
        :return: A list containing dictionaries. A dictionary is in the list representing each record
            that matches the template. The dictionary only contains the requested fields.
        """

        result = None

        try:
            # Compute the where clause.
            w_clause = self._template_to_where_clause(template)

            if field_list is None:
                # If there is not field list, we are doing 'select *'
                f_select = ['*']
            else:
                f_select = field_list

            ext = self._get_extras(limit, offset, order_by)

            # Query template.
            # _run_q will use args for %s terms and will format the field selection into {}
            q = "select {} from " + self._table_name + " " + w_clause[0] + " " + ext

            result = self._run_q(q, args=w_clause[1], fields=f_select, fetch=True, commit=commit)

            result = self._project(result, field_list)

            # SELECT queries always produce tables.
            result = DerivedDataTable("SELECT(" + self._table_name + ")", result)

        except Exception as e:
            print("Exception e = ", e)
            raise e

        return result

    def find_by_template2(self, template, field_list=None, limit=None,
                         offset=None, order_by=None, follow_paths=False,
                         commit=True):

        result = None

        if field_list is None:
            # If there is not field list, we are doing 'select *'
            f_select = ['*']
        else:
            f_select = field_list

        ext = self._get_extras(limit, offset, order_by)

        q = "select {} from " + self._table_name + " " + w_clause[0] + " " + ext

    def delete_by_template(self, template):
        """

        Deletes all records that match the template.

        :param template: A template.
        :return: A count of the rows deleted.
        """
        try:
            w_clause = self._template_to_where_clause(template)

            q = "delete from " + self._table_name + " " + w_clause[0]

            result = self._run_q(q, args=w_clause[1], fields=None, fetch=False, cnx=None, commit=True)

        except Exception as e:
            logging.error("RDBDataTable.delete_by_template exception", exc_info = True)
            raise e

        return result

    def delete_by_key(self, key_fields):

        try:
            k = dict(zip(self._key_columns, key_fields))
            return self.delete_by_template(k)

        except Exception as e:
            logging.error("RDBDataTable.delete_by_key exception", exc_info = True)
            raise e


    def insert(self, new_record):
        """

        :param new_record: A dictionary representing a row to add to the set of records.
        :return: None
        """
        # Get the list of columns.
        column_list = list(new_record.keys())

        # Get corresponding list of values.
        value_list = list(new_record.values())

        # Name of table.
        t_name = self._table_name

        # Perform insert.
        return self._run_insert(t_name, column_list, value_list)



    def update_by_template(self, template, new_values):
        """

        :param template: A template that defines which matching rows to update.
        :param new_values: A dictionary containing fields and the values to set for the corresponding fields
            in the records.
        :return: The number of rows updates.
        """
        raise NotImplementedError("Student must implement.")

    def update_by_key(self, key_fields, new_values):
        raise NotImplementedError("Student must implement.")


    def join_tables(self,dbname, children):


        args = children.split(",")

        join_clause = "JOIN " + "%s"

        return join_clause, args


    def get_primary_key(self, table):
        """

        :return: The names of the primary key columns in the form ['col1', ..., 'coln']

        The current implementation just returns the list of keys passed in the constructor.
        An extended implementation would/should query database data/metadata to get the information.
        """
        keys = None

        q = "SHOW KEYS FROM " + self._table + " WHERE KEY_name = 'PRIMARY'"
        rows = self._run_q(q, args=None)

        for r in rows:
            if r["Column_name"]:
                if r["Seq_in_index"] == 1:
                    keys = r["Column_name"]

                else:
                    print("Primary key was not found")

        return keys



    def _on_clause(self, dbname, children):

        args = children.split(",")
        child = []
        pair = []



        parent_key = self.get_primary_key(dbname)
        parent = dbname + "." + parent_key

        for i in range(len(args)):
            result = self.get_primary_key(args[i])
            child.append(result)
            new_result = "= " + args[i] + "." + child[i]
            pair.append(new_result)

        o_clause = "ON " + parent + pair[0] + " AND " + parent + pair[1]

        return o_clause


    def _load_foreign_key_info(self):

        result = None
        result = self._related_resources


        if result is None:
            schema_name = self._schema
            #print("schema",schema_name)
            q = """
            SELECT
                CONSTRAINT_NAME,
                TABLE_SCHEMA,
                TABLE_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_TABLE_SCHEMA,
                REFERENCED_COLUMN_NAME,
                ORDINAL_POSITION,
                POSITION_IN_UNIQUE_CONSTRAINT
                    FROM
                        INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE
                        REFERENCED_TABLE_SCHEMA = %s
                        AND
                            ((table_name=%s) or (REFERENCED_TABLE_NAME=%s))
                """

            args = (self._schema, self._table, self._table)
            #print("args",args)

            result = self._run_q(q, args)
            #print("result",result)
            paths = None

            if result is not None and len(result) > 0:
                paths = {}
                for r in result:
                    #print("r", r['CONSTRAINT_NAME'])
                    p = paths.get(r['CONSTRAINT_NAME'], None)

                    if p is None:
                        if r['REFERENCED_TABLE_NAME'].lower() == self._table:
                            to_me = True

                        else:
                            to_me = False
                        #print("to_me",to_me)

                        p = {}
                        p['to_me'] = to_me
                        p['MAP'] = []
                        p['CONSTRAINT_NAME'] = r['CONSTRAINT_NAME']
                        p['TABLE_NAME'] = r['TABLE_NAME']
                        p['TABLE_SCHEMA'] = r['TABLE_SCHEMA']
                        p['REFERENCED_TABLE_NAME'] = r['REFERENCED_TABLE_NAME']
                        p['REFERENCED_TABLE_SCHEMA'] = r['REFERENCED_TABLE_SCHEMA']

                        #print("p", p)

                        paths[r['CONSTRAINT_NAME']] = p

                        #print("paths",paths)



                    t = (r['COLUMN_NAME'], r['REFERENCED_COLUMN_NAME'])
                    #print("t", t)


                    p['MAP'].append(t)

            #print(paths)
            self._related_resources = paths


    def _get_primary_key_definition(self):
        keys = None

        q = "SHOW KEYS FROM " + self._table_name + " WHERE key_name = 'PRIMARY'"
        rows = self._run_q(q, args=None,fetch=True)
        #print(len(rows))

        if rows and len(rows) > 0:
            keys = [[r["Column_name"], r['Seq_in_index']] for r in rows]
            keys = sorted(keys, key=operator.itemgetter(1))
            keys = [k[0] for k in keys]
            #print(keys)

        return keys


    def _key_to_template(self, key):

        result = dict(zip(self._key_columns, key))
        return result

    def _map_key(self, key, related):
        if not "." in related:
            related_table_name = self._schema + "." + related

        else:
            related_table_name = related

        my_key = key

        other_key_columns = ds.get_data_table(related_table_name).get_primary_key_columns()

        mapped = None

        for k, v in self._related_resources.item():

            if v['to_me'] == True:
                r = v['TABLE_SCHEMA'].lower() + "." + v['TABLE_NAME'].lower()

            else:
                r = v['TABLE_SCHEMA'].lower() + "." + v['REFERENCED_TABLE_NAME'].lower()


            mapped = {}

            if r == related_table_name:

                for p in v['MAP']:
                    if v['to_me']:
                        my_col = p[1]
                        other_col = p[0]
                    else:
                        my_col = p[0]
                        other_col = p[1]

                    m_key = my_key.get(my_col,None)
                    if m_key is None:
                        return None
                    mapped[other_col] = m_key

                return mapped

        return mapped



    def get_primary_key_columns(self):
        return self._key_columns



    def find_by_path_key(self, parent_resource, key, child_resource, field_list=None,
                         limit=None, offset=None, order_by=None):
        result = None

        try:
            tmp = self._key_to_template(key)
            mapped_key = self._map_key(tmp,child_resource)

            # if mapped_key is None:
            #     #raise DataTableException(DataTableException._integrity_error, None, None)

            if "." not in child_resource:
                child_table_name = self._schema + '.' + child_resource

            else:
                child_table_name = child_resource

            child_table = ds.get_data_table(child_table_name)
            result = child_table.find_by_template(mapped_key, field_list, limit=limit, offset=offset, order_by=order_by)

        except Exception as e:
            logging.exception("RDBDataTable.find_by_path_key: e = ", str(e))
            raise e

        return result

    def insert_related(self,key,new_row,related_resource):

        related_tbl = ds.get_data_table(related_resource)
        tmp = self._key_to_template(key)

        mapped_key = self._map_key(tmp,related_resource)
        if mapped_key is None:
            row= self.find_by_primary_key(key)
            mapped_key = self._map_key(row)

            # if mapped_key is None:
            #    # de = DataTableException(DataTableException._integrity_error, "Invalid path", None)
            #     #raise(de)


        for k,v in mapped_key.items():
            new_row[k] = v

        result = related_tbl.insert(new_row)

        return result

    def _get_join_clause(self,parent_resource, child_resource):

        result_terms = []

        for k, v in self._related_resources.items():
            if(v["TABLE_NAME"].lower() == parent_resource and v["REFERENCED_TABLE_NAME"].lower() == child_resource) \
                or \
                (v["TABLE_NAME"].lower() == child_resource and v["REFERENCED_TABLE_NAME"].lower() == parent_resource):

                for m in v['MAP']:
                    result_terms.append(v['TABLE_NAME'] + "." + m[0] + "=" + \
                                        v['REFERENCED_TABLE_NAME'] + "." + m[1])

                    break

        if result_terms:
            result = " AND ".join(result_terms)

        else:
            result = None

        return result


    def create_join_on_clause(self, parent_resource, child_resource):

        parent_key = self.get_primary_key(parent_resource)
        parent = parent_resource + "." + parent_key

        child_key = self.get_primary_key(child_resource)
        child = child_resource + "." + child_key

        on = "ON " + parent + "=" + child


        result = parent_resource + " JOIN " + child_resource + on

        return result




    def find_by_path_template_pair(self,parent_resource,child_resource=None,template=None,field_list=None,limit=None,
                                   offset=None,order_by=None):

        result = None
        jcs=[]

        try:
            q = "SELECT {column}\n FROM {table}\n {ON}\n {WHERE}\n {EXTRAS}"

            on_c = None

            if child_resource:
                field_list = self._add_aliases(field_list)

            jc = self._get_join_clause(parent_resource, child_resource)

            on_c = jc
            tables = " " + parent_resource + " " + child_resource + " "

            wc = self._template_to_where_clause(template)

            if on_c is not None:
                w_string = wc[0] + " AND " + on_c

            else:
                on_c = " "
                w_string = wc[0]

            extras = self._get_extras(limit=limit,offset=offset,order_by=order_by)

            q = q.format(columns=field_list,tables=tables,on=" ",where=w_string,extras=extras)

            result = self._run_q(q, wc[1],fetch=True)


            #post_process_join()

            return result

        except Exception as e:
            print("find_by_path_template exception = ", e)


    def find_by_path_template(self,parent_resource,
                              child_resources=None,
                              template=None,
                              field_list=None,
                              limit=None,
                              offset=None,
                              order_by=None):

        child_resource_list = None
        field_array = None

        if child_resources:
            child_resource_list = child_resources.split(",")

        field_array = field_list

        if child_resource_list is None:
            return self.find_by_template(template,field_list,limit,offset,order_by)
        else:
            result = None
            parent_template = self._get_specific_template(parent_resource,template)
            parent_fields = [f for f in field_array if (parent_resource + ".") in f]


            for c in child_resource_list:
                child_template = self._get_specific_template(c, template)
                child_fields = [f for f in field_array if (c + ".") in f]

                if child_template is not None:
                    all_template = {**parent_template, **child_template}

                else:
                    all_template = parent_template

                all_fields = ".".join(parent_fields + child_fields)

                t = self.find_by_path_template_pair(parent_resource,c,all_template,
                                                    all_fields,limit,offset,order_by)

                if result is None:
                    result = t
                else:
                    for sub_r in result:
                        for sub_t in t:
                            rp_s = str(sub_r[parent_resource])
                            tp_s = str(sub_t[parent_resource])

                            if tp_s == rp_s:
                                sub_r[c] = sub_t[c]
                                break

            return result




