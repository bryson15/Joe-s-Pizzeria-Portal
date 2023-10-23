import pyodbc

# Define connection string

password = 'ICT320_student' 
driver= '{ODBC Driver 18 for SQL Server}'

connection_string = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:joes-place-server.database.windows.net,1433;Database=joes-place-db;Uid=student320;Pwd={ICT320_student};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

# Establish connection
connection = pyodbc.connect(connection_string)
cursor = connection.cursor()

# Query the database
order_date_to_query = '2023-09-17'

cursor.execute(
    "SELECT po.order_id, pc.customer_id, pc.first_name, pc.last_name, pc.phone, pc.address, pc.post_code FROM pizza.orders as po JOIN pizza.customers as pc ON po.customer_id = pc.customer_id WHERE po.order_date = ?", order_date_to_query
)

customerRows = cursor.fetchall()

cursor.execute(
    "SELECT po.order_id, poi.order_item_id, poi.product_name, poi.quantity, poi.list_price FROM pizza.orders as po JOIN pizza.order_items as poi ON po.order_id = poi.order_id WHERE po.order_date = ?", order_date_to_query
)

orderItemRows = cursor.fetchall()

for customerRow in customerRows:
    print(customerRow)
    for orderItemRow in orderItemRows:
        print(orderItemRow)



# Don't forget to close the connection 
cursor.close()
connection.close()

"""
Login failed as the database has exhausted the free vCore seconds allocated for the month of October 2023 and cannot be resumed until 12:00 AM (UTC) on November 01, 2023. To regain access to the database immediately, you can choose to enable overage billing and be charged for the additional usage.

"""


"""
SELECT po.order_id, poi.product_name, poi.quantity 
FROM pizza.orders as po
JOIN pizza.order_items as poi
ON po.order_id = poi.order_id
WHERE po.order_date = '2023-09-17';

"""