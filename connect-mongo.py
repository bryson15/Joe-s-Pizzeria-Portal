import pymongo

CONNECTION_STRING = "mongodb://joes-pizzeria-1155231:5uQ9Ot0n4ZJt0pPHHvaoRHoRrmTahMWZXOTjp0GtqJrKB3d6LGrU1Y52lrk94F5foSKkNAMo2YIdACDbHKfk9g==@joes-pizzeria-1155231.mongo.cosmos.azure.com:10255/?ssl=true&retrywrites=false&replicaSet=globaldb&maxIdleTimeMS=120000&appName=@joes-pizzeria-1155231@"
client = pymongo.MongoClient(CONNECTION_STRING)
db = client.joes_pizzeria_db
collection = db.dockets
# Define your document
document = {
    "name": "John Doe",
    "address": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip": "12345"
}

# Add the document to the collection
collection.insert_one(document)