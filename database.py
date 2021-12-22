"""
Created on Wed Dec 22 2021
@author: Alex Grimwood
Adapted from script by Steven Court
Interaction with QA database
"""

import pypyodbc
from pypyodbc import IntegrityError
import pandas as pd
import easygui as eg

import config

# NOTE: Cols with spaces or hyphens in name must be surrounded by square brackets

DB_PATH = config.PATH_TO_DB
SESSION_TABLE = config.SESSION_TABLE 
RESULTS_TABLE = config.RESULTS_TABLE
PASSWORD = config.PASSWORD



def write_session_data(conn, df_session):
    """Write to session table; return True if successful"""
        
    cursor = conn.cursor()   
    sql = '''
            INSERT INTO "%s" (ADate, MachineName, GA, Energy, [Operator 1],\
            [Operator 2], Electrometer, Chamber, Voltage, Temperature, Pressure,\
            N_dw, C_tp, k_q, k_s, k_elec, k_pol, RBE, Comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          '''%(SESSION_TABLE)
    data = df_session.values.to_list()
    
    try:
        cursor.execute(sql, data )
        conn.commit()
        return True
        
    except IntegrityError:
        eg.msgbox("Entry already exists, nothing written to database","WARNING")
        print("Entry already exists, nothing writen to database")
        return False
        
    

def write_results_data(conn,df_results):
    """Write results to QA database"""    

    cursor = conn.cursor()   
    sql = '''
            INSERT INTO "%s" (Timestamp, ADate, MachineName, GA, Energy,\
            MU_label, MU_requested, R1_measured, R2_measured, R3_measured,\
            R_mean, Dose_mean, R_MU1_ratio, Ratio_error) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)  
            '''%(RESULTS_TABLE)

    for i,row in df_results.iterrows():
        data = row.values.to_list()
        cursor.execute(sql, data)
        
    conn.commit()

    
def write_to_db(df,comment=""):
    
    conn=None  
    try:
        new_connection = 'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;PWD=%s'%(DB_PATH,PASSWORD)    
        conn = pypyodbc.connect(new_connection)                 
    except:
        eg.msgbox("Could not connect to database; nothing written","WARNING")
        print("Could not connect to database; nothing written")
        
    
    if isinstance(conn,pypyodbc.Connection):
        session_written = write_session_data(conn,df_session)
        if session_written:
            write_results_data(conn,df_results)
        
 
    

def main():
    # select excel file in GUI
    f = eg.fileopenbox(msg="Select Results File (.xlsx)", title="Dose Linearity", default='*', filetypes="*.xlsx", multiple=False)
    if f:
      # load session sheet to dataframe
      df_session = pd.read_excel(f, sheet_name='session', use_cols="A:S")
      # load results sheet to dataframe
      df_results = pd.read_excel(f, sheet_name='results', use_cols="A:N")
      # write dataframes to db
      write_to_db(df)
    else:
      eg.msgbox("Results file could not be read","WARNING")
      print("Results file could not be read; nothing written")
      
    
    
    
if __name__=="__main__":
    main()
