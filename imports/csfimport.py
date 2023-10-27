from functools import reduce
import pandas as pd
import openpyxl
from glob import glob

def get_names_from_header(filepath):
    """From an excel file, get the value index pairs for the header"""
    # open the file
    wb = openpyxl.load_workbook(filepath)
    # get the first sheet
    sheet = wb.worksheets[0]
    # get the header
    header = sheet[1]
    # get the values of the header if the value is not None
    values = [cell.value for cell in header if cell.value is not None]
    
    # get the index of the header
    indexes = [cell.column - 1 for cell in header if cell.value is not None]
    # create a dictionary with the values and indexes
    return dict(zip(values, indexes))

def get_sub_columns(filepath, header_col):
    """Given an excel file, get the sub columns for each of the headers"""
    # get the column indexes for the header
    indexes = get_names_from_header(filepath)
    # open the file
    wb = openpyxl.load_workbook(filepath)
    # get the first sheet
    sheet = wb.worksheets[0]
    # sub columns are in the next row
    sub_columns = sheet[2]
    # start from the header column - 1 until the sub column is None
    sub_headers = [cell.value for cell in sub_columns if cell.value is not None]
    # indexes of the sub columns
    # sub_indexes = [cell.column - 1 for cell in sub_columns if cell.value is not None]
    
    # iterate over sub_columns starting from the header column - 2
    sub_indexes = []
    # print(sub_columns[header_col].value)
    for i in range(header_col - 1, len(sub_columns)):
        # if the sub column is None, break
        # print(i, sub_columns[i].value)
        if sub_columns[i].value is None:
            break
        # else add the index to the list
        sub_indexes.append(i)
    
    return sub_indexes

def get_dataframe_for_header(filepath, header, header_col):
    """Given an excel file and the header column, skips the first row, 
    and reads the excel file from header column - 2 to header column + 2"""
    # columns = list(range(header_col - 1, header_col + 3))
    columns = get_sub_columns(filepath, header_col)
    # print(columns)
    # get the dataframe for the columns
    df = pd.read_excel(filepath, usecols=columns, skiprows=1)
     
    # add the header as a prefix to the column names for all columns except Sample
    df.columns = [f'{header}/{col.split(".")[0]}' if not col.startswith('Sample') else col.split('.')[0] for col in df.columns]
    # column names containing 'plate' are converted to Int64 dtype
    # convert them to string
    df = df.astype({col: 'Int64' for col in df.columns if 'plate' in col})
    


    # print(df.columns)
    # drop rows with empty Sample
    df = df[df['Sample'].notnull()]
    return df

def read_merge_excel(filepath):
    """Given an excel file, read the file and merge the dataframes for each header"""
    # print(filepath)
    # get the column indexes for the header
    indexes = get_names_from_header(filepath)
    print(indexes)
    # get the dataframes for each header
    dataframes = [get_dataframe_for_header(filepath, header, col) for header, col in indexes.items()]
    # merge all dataframes, using left join

    return reduce(lambda left, right: pd.merge(left, right, on='Sample', how='outer'), dataframes)

def fix_date_plate(df, col):
    """Given a dataframe and a column, if the value matches the pattern \d+.\d+.\d+-\d+ transform into a date and extract the number after - in a new column"""
    # if the col type is date, no need to fix
    if df[col].dtype == 'datetime64[ns]':
        return df
    # select the rows that match the pattern
    mask = df[col].str.contains(r'\d+.\d+.\d+-\d+')
    # replace nan with False
    mask = mask.fillna(False)
    # extract the number after - replace with the first part and store the second part in a new column
    df.loc[mask, f'{col}/plate'] = df.loc[mask, col].str.split('-').str[1]
    df.loc[mask, col] = df.loc[mask, col].str.split('-').str[0]
    return df

def fix_date(df, col):
    """Given a dataframe and a date column, transform the rows matching the pattern \d+.\d+.\d+-\d+ into a date"""
    if df[col].dtype == 'datetime64[ns]':
        return df
    # select the rows that match the pattern
    mask = df[col].str.contains(r'\d+.\d+.\d+-\d+')
    # replace nan with False
    mask = mask.fillna(False)
    # extract the number after - replace with the first part and store the second part in a new column
    df.loc[mask, col] = pd.to_datetime(df.loc[mask, col].str.replace(r'-\d+$', ''), format='%d.%m.%y')
    # set the type to date
    df[col] = pd.to_datetime(df[col])
    return df


def read_folder(folder):
    
    # get all excels in folder without 'SantiImport' in the name
    excels = glob(f'{folder}/*.xlsx')
    
    excels = [excel for excel in excels if 'SantiImport' not in excel and 'merged' not in excel and not '~' in excel]

    # print(excels)
    # apply read_merge_excel to all excels
    dfs = [read_merge_excel(excel) for excel in excels]
    merged = reduce(lambda left, right: pd.merge(left, right, on='Sample', how='outer'), dfs)
    # save to csv file in the folder 
    merged.to_csv(f'{folder}/merged.csv', index=False)
    return merged