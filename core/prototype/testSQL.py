import pyodbc
import os

if __name__ == "__main__":

    az_sql_server = os.environ['AZURE_SQL_SERVER']
    az_sql_db = os.environ['AZURE_SQL_DATABASE']
    az_sql_user = os.environ['AZURE_SQL_USER']
    az_sql_pass = os.environ['AZURE_SQL_PASS']
    
    az_sql_driver= '{ODBC Driver 17 for SQL Server}'

    print('DRIVER=' + az_sql_driver + 
        ';SERVER=' + az_sql_server + 
        ';PORT=1433;DATABASE=' + az_sql_db + 
        ';UID=' + az_sql_user + 
        ';PWD=' + az_sql_pass)

    cnxn = pyodbc.connect('DRIVER=' + az_sql_driver + 
        ';SERVER=' + az_sql_server + 
        ';PORT=1433;DATABASE=' + az_sql_db + 
        ';UID=' + az_sql_user + 
        ';PWD=' + az_sql_pass)
    
    # cursor = cnxn.cursor()
    # cursor.execute("SELECT TOP 20 pc.Name as CategoryName, p.name as ProductName FROM [SalesLT].[ProductCategory] pc JOIN [SalesLT].[Product] p ON pc.productcategoryid = p.productcategoryid")
    # row = cursor.fetchone()
    # while row:
    #     print (str(row[0]) + " " + str(row[1]))
    #     row = cursor.fetchone()



    print("Finished.")
