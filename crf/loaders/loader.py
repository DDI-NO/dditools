
import logging
# logger = logging.getLogger("xnatimport")
import importlib
import yaml
import os
from pathlib import Path
from csv import DictReader, reader
from pprint import pprint
from lxml import etree

DEFAULT_READ_METHOD = 'get_val'
DEFAULT_EMPTY_VALUE = 'NULL'

def load_config(version):
    '''
    Loads the data reading configuration for the given version and returns the config dict object
    '''
    file_path = os.path.realpath(__file__)
    file_path = Path(file_path).parent.absolute()
    config_file = f'{file_path}/config{version}.yaml'
    logging.info('Configuration file %s', config_file)
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        return config

class InvalidVersionException(Exception):
    pass

class CheckingErrorException(Exception):
    def __init__(self, errors) -> None:
        super().__init__()
        self.errors = errors

class CRFLoader():
    '''
    The base class to read raw SDAPS CSV data and retrieve XNAT-mapped data structures.
    Each CRF version must provide a specific CSV variable reading-mapping and a subclass of this class to 
    implement specific extra functionalities. 

    ...

    Attributes 
    ---------- 
    data : ordered dict
        The data read from the source SDAPS CSV
    config : YAML dict
        the expected variables and read methods and XNAT mapping for a given version 
    '''
        
    def __init__(self, data_source, config):
        '''
        Constructs a loader reading the data source and assigning configuration

        Parameters
        ----------
            data_source : str
                The path to the CSV file from SDAPS
            config : dict
                The variable configuration file, already parsed from the YAML definition
        '''
        directory = os.path.dirname(data_source)
        self.sdaps_file = os.path.join(directory, 'questionnaire.sdaps')
        logging.info('Data file %s', data_source)
        logging.info('SDAPS file %s', self.sdaps_file)
        with open(data_source, 'r') as csv:
            # The default dict based data reader
            dict_reader = DictReader(csv)
            self.data = next(dict_reader)

        # column index reader for variable naming issues in the CSV 
        # with open(data_source, 'r') as csv_col:
        #     col_reader = reader(csv_col)
        #     self.col_data = list(col_reader)[1]
        self.check_csv_data()

        self.config = config
        
    def check_csv_data(self):
        errors = []
        with open(self.sdaps_file, 'r') as sf:
            lines = sf.readlines()
            for k,v in self.data.items():
                if 'error' in v:
                    item = self.find_item_number(v, lines)
                    errors.append((k, v, item))
        
        if len(errors) > 0:
            pass
            # raise CheckingErrorException(errors)

    def find_item_number(self, variable_name, sdaps_lines):
        for line in sdaps_lines:
            if variable_name in line and 'Variable' in line:
                return line.split('=')[0].split('[')[2].split(']')[0]
        return None

    def is_valid(self, value):
        '''
        Tests if a value is valid in the sense of SDAPS. 
        Invalid values:
            * -1 
            * -2
            * 'NULL'
            * 'NA
        
        Parameters
        ----------
        value : str
            The value to test
        
        Returns
        -------
        True if the value is valid, False otherwise
        '''
        return value != '-1' and value != '-2' and value != 'NULL' and value != 'NA'

    def get_val(self, var:str, experiment_vars=None, nullvalue='NULL'):
        '''
        Retrieves the value assigned to the key with the var name from the data dict. 
        If the SDAPS value is -1, -2, NA or -999 returns 'NULL'.  
        
        Parameters
        ----------
        var : str
            The variable name to use as key
        
        Returns
        -------
        The value found or 'NULL' if the value is -1, -2 or -999
        '''

        value = self.data[var]
        
        
        if value == '-1' or value == '-2' or value == '-999' or value == 'NA':
            value = nullvalue
        ## if value == -2 a checking error TODO
        if 'error' in value:
            # raise Exception(f'Invalid checked value for {var}. Review the recognition.') 
            # TODO code an option to decide the behaviour when error, ignore or raise exception
            # ignore for now
            value = nullvalue
        return value

    def get_number_from_digits(self, name, n_digits, experiment_vars=None ):
        '''
        Constructs an integer value from the partial digits as stored in SDAPS.
        The method iterates through the different SDAPS variables constructed by appending the n step to the 
        variable stem name: varstem_n, n in (1, n_digits+1)    
        
        Parameters
        ----------
        name : str
            The variable name to use as key
        n_digits : int
            The number of digits that conforms the final number
        
        Returns
        -------
        str A valid integer constructed by joining all intermediate digits
        '''
        value = ''
        for i in range(1, n_digits + 1):
            var = f'{name}_{i}'
            temp = self.get_val(var)
            # print(var, temp, self.is_valid(temp))
            if self.is_valid(temp):
                value += temp
            else:
                ## if there is an invalid digit, the number cannot be complete,
                ## so return an empty string
                ## TODO should log or something
                return ''
        if value != '':
            value = str(int(value))
        return value
    
    def find_checked(self,  name:str, start:int=1, top:int=0, value_map:dict=None, experiment_vars=None): # type: ignore
        '''
        Returns the index of the checked item from a set of consecutive SDAPS items.
        The items are iterated from a stem name variable, and an indexed suffix: varstem_n, n in (start, top+1).
        The first item with a sdaps checked value ('1') is selected. 
        
        Parameters
        ----------
        name : str
            The variable name to use as stem
        start : int
            The start index position to iterate from
        top : int
            The final index positio to iterate to
        value_map : dict
            A dictionary for the case when the actual XNAT value depends on the SDAPS variable name.
            The method will assign the value found in the mapping when reaching a checked variable.
        Returns
        -------
        The integer index of the checked item, which will be the expected SDAPS value
        '''
        value = 'NULL'
        for i in range(start, top+1):
            var = f'{name}_{i}'
            temp = self.get_val(var)
            
            if temp == '1':
                if value_map is not None:
                    # print(var, temp, value_map[var])
                    return value_map[var]
                else:
                    return str(i)
        return value

    def find_checked_value(self, var: str = None, experiment_vars=None,   items:list=[]): # type: ignore
        ''''
        Finds the checked item in a list of CSV variable names, returning the first one with
        a valid value. 

        Parameters
        ----------
        items (list): the list of variable names 
            
        Returns
        -------
        the first valid value
        '''
        for v in items:
            temp = self.get_val(v)
            if self.is_valid(temp):
                return temp
        return 'NULL'

    def find_text_field(self, var, experiment_vars=None ):
        ''''
        Finds the string value of a SDAPS text field and returns it if the value is not '0', '1' or ''. 

        Parameters
        ----------
        var : str
            The variable name as key
            
        Returns
        -------
        The string value or 'NULL' if the found value is '0', '1' or ''
        '''
        ret_value = 'NULL'
        data_val = self.data[var]
        if data_val != '0' and data_val != '1' and data_val != '':
            ret_value = data_val
        return ret_value

    def join_comments(self, *comments):
        ''''
        Utility method that joins the found text from the set of provided variables. 
        For this purpose, the method calls find_text_field

        Parameters
        ----------
        comments 
            The set of variable names to retrieve text from
            
        Returns
        -------
        The joined comments, separated by new lines
        '''
        previous_comment = 'NULL'
        final_comment = ''
        for comment_var in comments:
            # ignore  experiment_vars and var_config, 
            comment = self.find_text_field(comment_var)
            if comment != 'NULL':
                final_comment += ('\n' + comment) if previous_comment != 'NULL' else comment
        return final_comment

    def val_map(self,  var, value_mapping=None, experiment_vars=None, nullvalue=DEFAULT_EMPTY_VALUE):
        ''''
        Obtains the mapped value from a given variable. That is, it translates the checked SDAPS value to a final XNAT value. 

        Parameters
        ----------
        var : str 
            The variable name key
        value_mapping : dict
            The dictionary to map the SDAPS value to the target XNAT value
            
        Returns
        -------
        The mapped XNAT value
        '''
        # get the SDAPS value
        data_val = self.data[var]
        # map to the final value from the provided value mapping
        # if there is no mapping for the data value, get default NULL value
        # this situation should happen when the item is not checked, receiving -1
        mapped_val = value_mapping.get(data_val, nullvalue)
        return mapped_val

    def get_date(self,  var, experiment_vars=None):
        '''
        Constructs a date ISO string in YYYY-mm-dd format from the stem variable name. 

        Parameters
        ----------
        var : str
            The stem variable name, so the method can access {var}_year_1, {var}_month and {var}_day
        
        Returns
        -------
        The ISO date in YYYY-mm-dd format
        '''
        date_year_1 = self.get_val(f'{var}_year_1')
        date_month = self.get_val(f'{var}_month')
        date_day = self.get_val(f'{var}_day')
        date = 'NULL'
        if self.is_valid(date_day) and self.is_valid(date_month) and self.is_valid(date_year_1): 
            date = f"202{date_year_1}-{date_month}-{date_day}"
        ## TODO
        ## else log a warning or error, since dates are important
        return date

    def year_command(self, var:str, experiment_vars=None):
        nums = [self.data[f'{var}_year_{n}'] for n in range(1,5)]
        final_number = ''
        if not 'NA' in nums:
            final_number = ''.join(nums)
        return final_number

    def score(self, var:str=None, experiment_vars=None, items:list=[], number_type='int', nullvalue='NULL'):# type: ignore
        '''
        Calculates the total sum score from a list of variable names by retrieving 
        their checked values.
            Parameters:
                - var (str): the name of the variable to assign the score value
                - items (list): the list of varirable names to compute the sum score
            Returns:
                The total sum of the values assigned to the variables in the list
        '''
        value = nullvalue
        if var is not None:
            total = 0
            all_missing = True
            for item in items:
                val = self.read_value(item, experiment_vars=experiment_vars)
                
                if val != 'NULL':
                    all_missing = False
                    if number_type == 'int':
                        total += int(val)
                    if number_type == 'float':
                        total += float(val)
            # a check that in case all score items are NULL, return default NULL value for the score
            if not all_missing:
                value = str(total)               

        return value
    
    def avg(self, experiment_vars=None,   var:str=None, items:list=[]):
        '''
        Calculates the avarage score from a list of variable names by retrieving 
        their checked values and dividing by the number of items.
            Parameters:
                - var (str): the name of the variable to assign the score value
                - items (list): the list of varirable names to compute the average score
            Returns:
                The average of the values assigned to the variables in the list
        '''
        score = self.score(var, items, experiment_vars=experiment_vars)
        if score != '' and score != 'NULL':
            score = int(score)
        avg = ''
        if self.is_valid(score):
            avg = score / len(items)
                          
        return avg

    def constant(self, var, constant_value='NULL', experiment_vars=None,):
        '''
        A utility method so it is possible to dynamically retrieve a constant value for the variable as defined in the configuration

        Parameters
        ----------
        var : str
            The variable name as key
        constan_value : str
            The defined constant value
        
        Returns
        -------
        The passed constant value 
        
        '''
        return constant_value
    @staticmethod
    def get_loader(crf_version:str, data_file) -> 'CRFLoader':
        '''
        Factory function that initializes and return a CRFLoader subclass instance from the provided CRF version.

        Parameters
        ----------
        crf_version : str
            The CRF version to initialize a CRFLoader implementation
        data_file : str
            The path to the SDAPS CSV data file

        Returns
        -------
        A CRFLoader instance for the passed CRF version
        '''
        # Standard import
        flat = crf_version.replace('.', '')
        
        module = f'.loader{flat}'
        loaderclassstr = f'Loader{flat}'
        #print(crf_version, flat, loaderclassstr)
        logging.info('CRF version %s', crf_version)
        
        LoaderClass = getattr(importlib.import_module(module, package=__package__), loaderclassstr)
        # Instantiate the class (pass arguments to the constructor, if needed)
        config = load_config(flat)
        instance = LoaderClass(data_file, config)
        logging.info('Loader %s', loaderclassstr)      
        return instance

    def get_configured_experiment_names(self):
        return list(self.config['experiments'].keys())
    
    def get_configured_experiments(self):
        return self.config['experiments']

    def read_value(self, var, experiment_vars=None):
        #print(var)
        var_config = experiment_vars[var]
        method_name = DEFAULT_READ_METHOD
        ## store column index argument if present in variable config
        #col = var_config['col'] if 'col' in var_config else None
        kwargs = {}
        # get method config if present, else use default read method 'get_val'
        if 'read_method' in var_config:
            method_config = var_config['read_method']
            method_name = method_config['name']
            # only get method_kwargs if it is in the config dict
            config_kwargs = method_config['method_kwargs'] if 'method_kwargs' in method_config else {}
            kwargs = config_kwargs#{**kwargs, **config_kwargs}
        
        read_method = getattr(self, method_name)
        kwargs['experiment_vars'] = experiment_vars
        #pprint(kwargs)
        #print(kwargs.keys())
        value = read_method(var, **kwargs)
        
        return value

    # def get_schema_from_prefix(self, datatype_prefix):
    #     r = self.xnat.get(f'/xapi/schemas/{datatype_prefix}')
    #     r.content
    #     xml = etree.fromstring(r.content)
    #     return xml

    # def exists_in_schema(self, element_name:str, schema):
    #     """
    #     Retrieves the datatype schema from XNAT and inspects via XPATH if the element is defined in it. 
    #     Returns true if exists, False otherwise.

    #     Parameters
    #     ----------
    #     element_name : str
    #         The element name as it is supposed to be in the schema.
    #     datatype : str
    #         The datatype prefix, which should be the name of the xsd file.
    #     """
        
    #     # an element exists if the returned list from xpath has content
    #     search = schema.xpath(
    #         f"//xs:element[@name='{element_name}']", 
    #         namespaces={'xs' : "http://www.w3.org/2001/XMLSchema"})
    #     return len(search) > 0

    def get_data(self, experiment:str):
        '''
        Returns the XNAT data dict for the passed experiment section identifier, as defined in a configuration YAML.
        For this, it iterates through the section defined CRF variables and apply their read method and transformations.

        Parameters
        ----------
        experiment : str
            The experiment section identifier.
        
        Returns
        -------
        A dictionary with XNAT variable paths as keys and found values
        '''
        experiment_data = {}
        experiment_config = self.config['experiments'][experiment]
        # get datatype schema from prefix for inspection
        #schema = self.get_schema_from_prefix(experiment_config['prefix'])
        
        # iterate through sections
        sections = experiment_config['sections']
        for section, section_config in sections.items():
            
            experiment_data[section] = {'title' : section_config['title']}
            section_data = {}
            # iterate through variable to set the values
            experiment_vars = section_config['variables']
            value = ''
            for var, var_config in experiment_vars.items():
                try:
                    xnat_path = var_config['path']
                    # only add variables that are defined in the schema. Otherwise XNAT stops when using mset method
                    #element_name = xnat_path.split('/')[-1]
                    #if self.exists_in_schema(element_name, schema):
                        #print(var)
                    value = self.read_value(var, experiment_vars=experiment_vars)
                    section_data[xnat_path] = value
                    
                except KeyError as e:
                    raise KeyError(f'Error while getting {var} in {section}') from e
            experiment_data[section]['data'] = section_data
            
        
        # run finisher method if defined in the loader subclass
        finisher_method = getattr(self, experiment, None)
        if finisher_method is not None:
            experiment_data = finisher_method(experiment_data)

        return experiment_data

    def process_subjectdata(self, subject_section):
        data = {}
        vars = self.config['subject'][subject_section]
        
        value = ''
        for var, var_config in vars.items():
            try:
                xnat_path = var_config['path']

                value = self.read_value(var, experiment_vars=vars)
                data[xnat_path] = value
            except KeyError as e:
                raise KeyError(f'Error while getting {var} in {subject_section}') from e
        return data

    def get_subjectdata(self):
        xnat_subjectdata = self.process_subjectdata('subject_data')
        yob = ''
        y1 = self.data['yob_yob_1']
        y2 = self.data['yob_yob_2']
        if self.is_valid(y1) and self.is_valid(y2):
            yob = f"19{self.data['yob_yob_1']}{self.data['yob_yob_2']}"
        xnat_subjectdata['xnat:subjectData/demographics[@xsi:type=xnat:demographicData]/yob'] = yob
        
        ddi_dem = self.process_subjectdata('dem_data')
        return xnat_subjectdata, ddi_dem

    def get_mhdata(self):
        return self.get_data('mh_data')

    def get_phyexdata(self):
        return self.get_data('phyex_data')

    def get_csdata(self):
        return self.get_data('cs_data')

    def get_diagdata(self):
        return self.get_data('diag_data')

    def get_mrrep_data(self):
        return self.get_data('mrrep_data')

    def get_cover_data(self):
        cover_data = self.get_data('cover_data')
        if self.data['exclusion'] == '1':
            if self.data['stag_date_same_as_main'] == '1':
                exclusion_date = self.get_date('date')
                cover_data['cover:CoverData/exclusion_date'] = exclusion_date
        else:
            cover_data['cover:CoverData/inclusion'] = '1'

        return cover_data
