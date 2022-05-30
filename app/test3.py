import pyodbc
import pandas as pd

server = 'localhost'
database = 'test2'
username = 'root'
password = 'f2f54321'

cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)

cursor = cnxn.cursor()

query = "SELECT [id], [timestamp] FROM `temp`;"
df = pd.read_sql(query, cnxn)