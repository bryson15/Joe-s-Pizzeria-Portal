import io
import pyodbc
from fpdf import FPDF

from decimal import Decimal


from azure.storage.blob import BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string("DefaultEndpointsProtocol=https;AccountName=joespizzeriastorage;AccountKey=erxtIerjR+2etuPK5SO/skg+I/4W1IBaMlwFK+p+ffDh5JXWKOXgkQqyXYNwvcgwKa5IQY0NMpVF+AStjYMUEQ==;EndpointSuffix=core.windows.net")
blob_container_client = blob_service_client.get_container_client("pdf-dockets")



import pymongo

CONNECTION_STRING = "mongodb://joes-pizzeria-1155231:5uQ9Ot0n4ZJt0pPHHvaoRHoRrmTahMWZXOTjp0GtqJrKB3d6LGrU1Y52lrk94F5foSKkNAMo2YIdACDbHKfk9g==@joes-pizzeria-1155231.mongo.cosmos.azure.com:10255/?ssl=true&retrywrites=false&replicaSet=globaldb&maxIdleTimeMS=120000&appName=@joes-pizzeria-1155231@"
client = pymongo.MongoClient(CONNECTION_STRING)
db = client.joes_pizzeria_db
collection = db.dockets




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
# what is the list price? does it apply to the item, or does it factory in the quantity



orderItemRows = cursor.fetchall()

for customerRow in customerRows:

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=12)

    lines = [
        f"Order #{customerRow[0]} for {customerRow[2]}",
        "",
        "----- Delivery details ------",
        "Driver: ***LATER***",
        f"Address: {customerRow[5]}",
        f"Postcode: {customerRow[6]}",
        f"Ph.: {customerRow[4]}",
        "",
        "------- Order details -------"
    ]
    subtotal = 0
    for orderItemRow in orderItemRows:
        if (orderItemRow[0] == customerRow[0]):
            lineTotal = orderItemRow[3] * orderItemRow[4] # quantity * list_price
            subtotal += lineTotal
            fLineTotal = "{:.2f}".format(lineTotal)
            spaceLength = 25 - len(orderItemRow[2]) - len(str(orderItemRow[3])) - len(fLineTotal)
            lines.append(f"{orderItemRow[3]} x {orderItemRow[2]}{spaceLength * ' '}${fLineTotal}")
    
    deliveryFee = subtotal * Decimal("0.1")
    total = subtotal + deliveryFee

    fSubtotal = "{:.2f}".format(subtotal)
    fDeliveryFee = "{:.2f}".format(deliveryFee)
    fTotal = "{:.2f}".format(total)

    lines.extend([
        "                     --------",
        f"Subtotal{(20 - len(fSubtotal)) * ' '}${fSubtotal}",
        f"Delivery Fee{(16 - len(fDeliveryFee)) * ' '}${fDeliveryFee}",
        "                     --------",
        f"Total{(23 - len(fTotal)) * ' '}${fTotal}"
    ])

    for line in lines:
        pdf.cell(200, 10, txt=line, ln=True)

    pdf_data = pdf.output(dest='S').encode('latin-1')

    blob_name = f"order_{customerRow[0]}_docket.pdf"
    blob_client = blob_container_client.get_blob_client(blob_name)
    blob_client.upload_blob(pdf_data, blob_type="BlockBlob", overwrite=True)

    blob_url = blob_client.url
    document = {
        "blob_name": blob_name,
        "blob_url": blob_url,
        "order_id": customerRow[0]
    }
    collection.insert_one(document)

# Don't forget to close the connection 
cursor.close()
connection.close()