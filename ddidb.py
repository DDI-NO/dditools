#!/usr/bin/python3
import psycopg2
import pandas as pd
# Import the 'config' funtion from the config.py file
from config import config_manager

class DB(object):
    """docstring for DB"""
    def __init__(self):
        # Obtain the configuration parameters
        # params = config()
        params = {
            'host': config_manager.get('DATABASE', 'host'),
            'database': config_manager.get('DATABASE', 'database'),
            'port': config_manager.get('DATABASE', 'port'),
            'user': config_manager.get('DATABASE', 'user'),
            'password': config_manager.get('DATABASE', 'password'),
        }
        # Connect to the PostgreSQL database
        self.conn = psycopg2.connect(**params)
        # Create a new cursor
        self.cur = self.conn.cursor()
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # Close the cursor and connection to so the server can allocate
        # bandwidth to other requests
        self.disconnect()

    def disconnect(self):
        self.cur.close()
        self.conn.close()

    def find_subject_like(self, subject_label, project='apgem') -> str:
        """
        Finds a subject with a subject_label mathing the provided.

        Parameters
        ----------
        subject_label: The subject label to match with the like operator
        project: the project ID to query. Defaults to apgem

        Returns
        -------
        The subject ID if found, None otherwise
        """
        q = f"""select subject_id, subject_label
    from displayfields_xnat_subjectdata
    where project='{project}' and subject_label like '{subject_label}%'"""
        cur = self.cur
        cur.execute(q)
        result = cur.fetchone()
        # if result is not None:
        # 	result = result[0]
        return result

    def find_experiment(self, etype:str, subject:str, visit:str='', project='apgem', subject_accessor='label') -> str:
        """
        Finds a experiment of a given type belonging to a subject at an specific visit. The subject identifier can be the base XNAT identifier or the label. 
        The default is 'label', otherwise must be specified with the subject_accessor named argument. 
        The default project to query is apgem. 
        
        Example: to get the baseline CSF experiment of subject D10215 call find_experiment('csf:CSFData', 'D10215', '1')

        Parameters
        ----------
        etype: the experiment type, determined by its XML element (namespace:element)
        subject: the subject id string (subject_id or subject_label)
        visit: the visit ID string
        project: the project ID to query. Defaults to apgem
        subject_accessor: the item to identify the subject: label or subject XNAT ID. Defaults to 'label'.

        Returns
        -------
        The experiment ID if found, None otherwise
        """
        prefix, element = etype.split(':')
        element = element.lower()
        table = f'displayfields_{prefix}_{element}'

        subject_filter = f"subject_id = (select subject_id from displayfields_xnat_subjectdata where subject_label like '{subject}%'  and project = '{project}')"
        if subject_accessor != 'label':
            subject_filter = f"subject_id = '{subject}'"
        
        visit_filter = ''
        if visit:
            visit_filter = f"and visit_id = '{visit}'"

        q = f"""select expt_id
    from {table}
    where {subject_filter} and project = '{project}' {visit_filter}"""
        # print(q)
        cur = self.cur
        cur.execute(q)
        result = cur.fetchone()
        if result is not None:
            result = result[0]
        return result

    def create_pandas_table(self, sql_query) -> pd.DataFrame:
        '''
        Takes in a PostgreSQL query string and outputs a pandas DataFrame 
        
        Parameters
        ----------
        sql_query: the SQL query to execute

        Returns
        -------
        The resulset in a DataFrame
        '''
        table = pd.read_sql_query(sql_query, self.conn)
        return table

    def query(self, path:str) -> pd.DataFrame:
        '''
        Launches a query from the argument file and returns a pandas Dataframe
        Parameters
        ----------
        path: the path to a file with the SQL query to execute

        Returns
        -------
        The resulset in a DataFrame
        '''
        sql = """"""
        with open(path, 'r', encoding='utf-8-sig') as f:
            sql = f.read()
        return self.create_pandas_table(sql)

    def query_to_df(queryfile):
        '''
        Launches a query from the argument file and returns a pandas Dataframe
        Parameters
        ----------
        path: the path to a file with the SQL query to execute

        Returns
        -------
        The resulset in a DataFrame
        '''
        df = None
        with DB() as db:
            df = db.query(queryfile)
            return df
        
    def query_string_df(query):
        '''
        Takes in a PostgreSQL query string and outputs a pandas DataFrame 

        Parameters
        ----------
        sql_query: the SQL query to execute

        Returns
        -------
        The resulset in a DataFrame
        '''
        df = None
        with DB() as db:
            df = db.create_pandas_table(query)

        return df