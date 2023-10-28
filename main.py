import pyodbc
from fpdf import FPDF
from decimal import Decimal
from azure.storage.blob import BlobServiceClient
import pymongo

class Singleton(type):
    """
    A metaclass for implementing the Singleton pattern.
    """
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance
    
class MongoSingleton(type):
    """
    A metaclass for implementing the Singleton pattern for each distinct collection_name.
    """
    _instances = {}

    def __call__(cls, collection_name, *args, **kwargs):
        if collection_name not in cls._instances:
            instance = super().__call__(collection_name, *args, **kwargs)
            cls._instances[collection_name] = instance
        return cls._instances[collection_name]

class AzureBlob(metaclass=Singleton):
    """
    A class for interacting with Azure Blob storage.
    """ 
    def __init__(self):
        """
        Constructor for establishing connection.
        """
        connection_string = "DefaultEndpointsProtocol=https;AccountName=joespizzeriastorage;AccountKey=erxtIerjR+2etuPK5SO/skg+I/4W1IBaMlwFK+p+ffDh5JXWKOXgkQqyXYNwvcgwKa5IQY0NMpVF+AStjYMUEQ==;EndpointSuffix=core.windows.net"
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.blob_container_client = self.blob_service_client.get_container_client("pdf-dockets")

    def upload_pdf(self, pdf_data, blob_name):
        """
        Uploads a PDF to the blob storage.
        
        Parameters:
            - pdf_data (bytes): The PDF data in bytes.
            - blob_name (str): The name of the blob.
        
        Returns:
            - str: The URL of the uploaded blob.
        """
        blob_client = self.blob_container_client.get_blob_client(blob_name)
        blob_client.upload_blob(pdf_data, blob_type="BlockBlob", overwrite=True)
        return blob_client.url
    
    def get_pdf(self, blob_name):
        """
        Downloads a PDF from the blob storage.
        
        Parameters:
            - blob_name (str): The name of the blob to retrieve.
        
        Returns:
            - bytes: The data of the downloaded blob.
        """
        blob_client = self.blob_container_client.get_blob_client(blob_name)
        blob_data = blob_client.download_blob()
        return blob_data.readall()

class MongoDB(metaclass=MongoSingleton):
    """
    A class for interacting with a given MongoDB collection.
    """

    def __init__(self, collection_name):
        """
        Constructor for establishing collection_name and connection.
        
        Parameters:
            - collection_name (str): The name of the collection to interact with.
        """
        self.collection_name = collection_name
        self.connect()

    def is_connected(self):
        """
        Determines whether there's a connection to MongoDB.
        
        Returns:
            - bool: True if connected, False otherwise.
        """
        try:
            self.client.server_info()
            return True
        except:
            return False

    def connect(self):
        """
        Establishes connection to MongoDB and sets up collection object.
        """
        connection_string = "mongodb://joes-pizzeria-1155231:5uQ9Ot0n4ZJt0pPHHvaoRHoRrmTahMWZXOTjp0GtqJrKB3d6LGrU1Y52lrk94F5foSKkNAMo2YIdACDbHKfk9g==@joes-pizzeria-1155231.mongo.cosmos.azure.com:10255/?ssl=true&retrywrites=false&replicaSet=globaldb&maxIdleTimeMS=120000&appName=@joes-pizzeria-1155231@"
        self.client = pymongo.MongoClient(connection_string)
        self.db = self.client["joes_pizzeria_db"]
        self.collection = self.db[self.collection_name]

    def upsert_document(self, document, document_id):
        """
        Upserts (updates or inserts) a document into the MongoDB collection.

        Parameters:
        - document (dict): The document to be upserted. 
        - document_id (str): The key in the document to be used as the primary identifier for upserting.
        """
        if not self.is_connected():
            self.connect()
        self.collection.update_one(
            {document_id: document[document_id]},
            {"$set": document},
            upsert=True
        )
    
    def get_driver_by_post_code(self, post_code):
        """
        Retrieves a driver from the current MongoDB collection based on the given postcode.

        Parameters:
        - post_code (int or str): The postcode used to find a driver who delivers to that area.

        Returns:
        - dict: The driver document that delivers to the given postcode. If none found, returns None.
        """
        if not self.is_connected():
            self.connect()
        return self.collection.find_one({"delivery_suburbs": {"$in": [post_code]}})
    
    def get_transactions_by_date(self, summary_date):
        """
        Retrieves all transactions from the current MongoDB collection for a given date.

        Parameters:
        - summary_date (str): The date to retrieve transactions for, in the format 'YYYY-MM-DD'.

        Returns:
        - list: A list of transaction documents that occurred on the given date.
        """
        if not self.is_connected():
            self.connect()
        return list(self.collection.find({"order_date": summary_date}))
    
    def get_document_by_order_id(self, order_id):
        """
        Retrieves a document from the current MongoDB collection based on the given order ID.

        Parameters:
        - order_id (int or str): The order ID to search for in the documents.

        Returns:
        - dict: The document corresponding to the given order ID. If none found, returns None.
        """
        if not self.is_connected():
            self.connect()
        return self.collection.find_one({"order_id": order_id})

    def close(self):
        """
        Closes the MongoDB client connection.
        """
        if self.client:
            self.client.close()

class Dockets:
    """
    A small class for interacting with the dockets collection.
    """

    def __init__(self):
        """
        Initializes MongoDB dockets collection.
        """
        self.docket = MongoDB("dockets")

    def create_docket(self, order_id, blob_name, blob_url):
        """
        Creates the docket document and upserts it to the MongoDB dockets collection.
        
        Parameters:
        - order_id (str): The unique identifier for the order.
        - blob_name (str): The name of the blob associated with the docket.
        - blob_url (str): The URL where the blob can be accessed.
        """
        docket = {
            "blob_name": blob_name,
            "blob_url": blob_url,
            "order_id": order_id
        }
        self.docket.upsert_document(docket, "order_id")

class SQLDatabase(metaclass=Singleton):
    """
    A class for reading and writing to SQL Database.
    """

    def __init__(self):
        """
        Initializes SQL Database instance.
        """
        self.connect()
    
    def is_connected(self):
        """
        Determines whether there's a connection to SQL Database.
        
        Returns:
            - bool: True if connected, False otherwise.
        """
        try:
            self.cursor.execute("SELECT 1")
            return True
        except:
            return False
        
    def connect(self):
        """
        Establishes connection and cursor for the SQL Database. 
        """
        #connection_string = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:joes-place-server.database.windows.net,1433;Database=joes-place-db;Uid=student320;Pwd={ICT320_student};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        connection_string = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:ict320-task3d.database.windows.net,1433;Database=joe-pizzeria;Uid=student320;Pwd={ICT320_student};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        self.connection = pyodbc.connect(connection_string)
        self.cursor = self.connection.cursor()


    def get_customer_rows(self, order_date):
        """
        Retrieves customer rows based on the given order date.

        Parameters:
        - order_date (date): The date for which order information is to be fetched.

        Returns:
        - list of tuples: A list of customer information tuples.
        """
        if not self.is_connected():
            self.connect()
        self.cursor.execute(
            "SELECT po.order_id, pc.customer_id, pc.first_name, pc.last_name, pc.phone, pc.address, pc.post_code FROM pizza.orders as po JOIN pizza.customers as pc ON po.customer_id = pc.customer_id WHERE po.order_date = ?", order_date
        )
        return self.cursor.fetchall()
    

    def get_order_item_rows(self, order_date):
        """
        Retrieves item rows based on the given order date.

        Parameters:
        - order_date (date): The date for which order information is to be fetched.

        Returns:
        - list of tuples: A list of item information tuples.
        """
        if not self.is_connected():
            self.connect()
        self.cursor.execute(
            "SELECT po.order_id, poi.order_item_id, poi.product_name, poi.quantity, poi.list_price FROM pizza.orders as po JOIN pizza.order_items as poi ON po.order_id = poi.order_id WHERE po.order_date = ?", order_date
        )
        return self.cursor.fetchall()
    
    def set_summary_row(self, store_id, summary_date, total_sales, total_orders, best_product):
        """
        Inserts a new summary row and returns the generated summary ID.

        Parameters:
        - store_id (int): The store ID for which the summary is to be set.
        - summary_date (date): The date for which the summary is being created.
        - total_sales (decimal): The total sales amount for the given date.
        - total_orders (int): The total number of orders for the given date.
        - best_product (str): The best-selling product for the given date.

        Returns:
        - int: The ID of the newly inserted summary row.
        """
        if not self.is_connected():
            self.connect()
        self.cursor.execute(
            "INSERT INTO pizza.summary (store_id, summary_date, total_sales, total_orders, best_product) VALUES (?, ?, ?, ?, ?)", (store_id, summary_date, total_sales, total_orders, best_product)
        )
        self.connection.commit()
        self.cursor.execute("SELECT @@IDENTITY AS 'Identity'")
        summary_id = self.cursor.fetchone()[0]
        return summary_id

    def summary_exists(self, summary_date):
        """
        Checks whether a summary exists for the given date.

        Parameters:
        - summary_date (date): The date for which the existence of a summary is to be checked.

        Returns:
        - int or None: The ID of the summary row if it exists, otherwise None.
        """
        if not self.is_connected():
            self.connect()
        self.cursor.execute(
            "SELECT summary_id FROM pizza.summary WHERE summary_date = ? AND store_id = ?", (summary_date, 1155231)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_distinct_items(self):
        """
        Retrieves a list of distinct product items along with their list prices.

        Returns:
        - list of tuples: A list containing tuples with distinct product names and their corresponding list prices.
        """
        if not self.is_connected():
            self.connect()
        self.cursor.execute("SELECT DISTINCT product_name, list_price FROM pizza.order_items")
        return self.cursor.fetchall()
    
    def get_distinct_dates(self):
        """
        Retrieves a list of distinct order dates from the pizza.orders table.
        
        Returns:
        - list of tuples: A list containing tuples with distinct order dates.
        """
        if not self.is_connected():
            self.connect()
        self.cursor.execute("SELECT DISTINCT order_date FROM pizza.orders")
        return self.cursor.fetchall()

    def close(self):
        """
        Closes the database connection and cursor if they exist.
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def get_post_codes(self):
        """
        Retrieves a sorted list of unique post codes.

        Returns:
        - list of int: A sorted list containing distinct post codes.
        """
        if not self.is_connected():
            self.connect()
        self.cursor.execute("SELECT post_code from pizza.customers")
        post_codes_tuples = self.cursor.fetchall()
        return sorted(set([int(item[0]) for item in post_codes_tuples]))

    def get_rows(self, order_date):
        """
        Retrieves customer rows and order item rows for the specified order date.

        Parameters:
        - order_date (date): The date for which the rows are to be fetched.

        Returns:
        - tuple of lists: A tuple containing two lists - one for customer rows and one for order item rows.
        """
        customer_rows = self.get_customer_rows(order_date)
        order_item_rows = self.get_order_item_rows(order_date)
        return customer_rows, order_item_rows

class PDF:
    """
    A class to create and handle PDFs, primarily for order dockets.
    """
        
    def __init__(self):
        """
        Initializes the PDF object with an FPDF instance and sets the default configurations.
        """
        self.pdf = FPDF()
        self.pdf.add_page()
        self.pdf.set_font("Courier", size=12)

    def get_customer_lines(self, customer_row):
        """
        Retrieves customer-related lines for the PDF based on the given customer row data.

        Parameters:
        - customer_row (tuple): The row containing customer-related details.

        Returns:
        - list of str: A list of lines that can be printed on the PDF.
        - dict: Driver details assigned based on postcode.
        """
        driver = MongoDB("drivers").get_driver_by_post_code(4556)
        return [
            f"Order #{customer_row[0]} for {customer_row[2]}",
            "",
            "----- Delivery details ------",
            f"Driver: {driver['name']}",
            f"Address: {customer_row[5]}",
            f"Postcode: {customer_row[6]}",
            f"Ph.: {customer_row[4]}",
            "",
            "------- Order details -------"
        ], driver
    
    def get_order_item_lines(self, customer_row, order_item_rows):
        """
        Computes the order item-related lines for the PDF based on the provided data.

        Parameters:
        - customer_row (tuple): The row containing customer-related details.
        - order_item_rows (list of tuples): List containing rows of order items.

        Returns:
        - list of str: A list of lines detailing each order item.
        - float: The calculated subtotal for the order.
        """
        order_item_lines = []
        subtotal = 0
        for order_item_row in order_item_rows:
            if (order_item_row[0] == customer_row[0]):
                line_total = order_item_row[3] * order_item_row[4] # quantity * list_price
                subtotal += line_total
                f_line_total = "{:.2f}".format(line_total)
                spaceLength = 25 - len(order_item_row[2]) - len(str(order_item_row[3])) - len(f_line_total)
                order_item_lines.append(f"{order_item_row[3]} x {order_item_row[2]}{spaceLength * ' '}${f_line_total}")
        return order_item_lines, subtotal
    
    def get_total_lines(self, subtotal, commission_rate):
        """
        Computes the total cost and returns formatted lines to be added to the PDF.

        Parameters:
        - subtotal (float): The computed subtotal of the order without delivery fee.
        - commission_rate (float): The commission rate to calculate the delivery fee.

        Returns:
        - list of str: A list of lines detailing the subtotal, delivery fee, and total.
        - float: The computed total value of the order.
        """
        delivery_fee = subtotal * Decimal(commission_rate) / 100
        total = subtotal + delivery_fee
        f_subtotal = "{:.2f}".format(subtotal)
        f_delivery_fee = "{:.2f}".format(delivery_fee)
        f_total = "{:.2f}".format(total)
        return [
            "                     --------",
            f"Subtotal{(20 - len(f_subtotal)) * ' '}${f_subtotal}",
            f"Delivery Fee{(16 - len(f_delivery_fee)) * ' '}${f_delivery_fee}",
            "                     --------",
            f"Total{(23 - len(f_total)) * ' '}${f_total}"
        ], f_total

    def get_pdf_data_from_lines(self, lines):
        """
        Converts the provided list of lines into PDF format.

        Parameters:
        - lines (list of str): A list of lines to be added to the PDF.

        Returns:
        - bytes: The PDF content encoded in 'latin-1'.
        """
        for line in lines:
            self.pdf.cell(200, 10, txt=line, ln=True)
        return self.pdf.output(dest='S').encode('latin-1')

    def create_pdf(self, customer_row, order_item_rows):
        """
        Creates a PDF for a given order, saves it as a blob, and returns relevant details.

        Parameters:
        - customer_row (tuple): The row containing customer-related details.
        - order_item_rows (list of tuples): List containing rows of order items.

        Returns:
        - int: Order ID.
        - str: Blob name where the PDF was saved.
        - str: URL where the blob can be accessed.
        - dict: Driver details assigned based on postcode.
        - float: The total amount of the order.
        """
        customer_lines, driver = self.get_customer_lines(customer_row)
        order_item_lines, subtotal = self.get_order_item_lines(customer_row, order_item_rows)
        total_lines, total = self.get_total_lines(subtotal, driver["commission_rate"])
        pdf_data = self.get_pdf_data_from_lines(customer_lines + order_item_lines + total_lines)
        blob_name = f"order_{customer_row[0]}_docket.pdf"
        blob_url = AzureBlob().upload_pdf(pdf_data, blob_name)
        return customer_row[0], blob_name, blob_url, driver, total

class Drivers:
    """
    A class to handle and interact with driver details stored in MongoDB.
    """

    def __init__(self):
        """
        Initializes the Drivers object with an instance of MongoDB for the 'drivers' collection.
        """
        self.driver = MongoDB("drivers")

    def split_post_codes(self, post_codes):
        """
        Splits the provided list of postcodes into three approximately equal segments.

        Parameters:
        - post_codes (list of int): A list of postcodes.

        Returns:
        - list of list of int: A list containing three sublists with split postcodes.
        """
        split_1_end = len(post_codes) // 3
        split_2_end = 2 * split_1_end
        return [post_codes[:split_1_end], post_codes[split_1_end:split_2_end], post_codes[split_2_end:]]

    def create_drivers(self):
        """
        Creates driver documents in the MongoDB collection. It splits the postcodes from SQLDatabase 
        into three parts and assigns each part to a driver.
        """
        post_codes = SQLDatabase().get_post_codes()
        post_code_splits = self.split_post_codes(post_codes)
        names = ["Brandon Robles", "Milly Jennings", "Ewan Guerrero"]
        for i in range(0, 3):
            driver_id = i + 1
            driver = {
                "driver_id": driver_id,
                "name": names[i],
                "delivery_suburbs": post_code_splits[i],
                "commission_rate": 10
            }
            self.driver.upsert_document(driver, "driver_id")

class Transactions:
    """
    A class to handle and interact with transaction details stored in MongoDB.
    """
        
    def __init__(self):
        """
        Initializes the Transactions object with an instance of MongoDB for the 'transactions' collection.
        """
        self.transaction = MongoDB("transactions")

    def get_items(self, customer_row, order_item_rows):
        """
        Extracts and organizes item details from given rows.

        Parameters:
        - customer_row (tuple): Tuple containing customer details.
        - order_item_rows (list of tuples): List containing details of order items.

        Returns:
        - list of dict: List of dictionaries containing individual order items.
        """
        items = []
        for order_item_row in order_item_rows:
            if (order_item_row[0] == customer_row[0]):
                items.append({
                    "order_item_id": order_item_row[1],
                    "product_name": order_item_row[2],
                    "quantity": order_item_row[3],
                    "list_price": "{:.2f}".format(order_item_row[4])
                })
        return items

    def create_transaction(self, customer_row, order_item_rows, order_date, driver, total):
        """
        Constructs and stores a transaction document in the MongoDB collection based on provided details.

        Parameters:
        - customer_row (tuple): Tuple containing customer details.
        - order_item_rows (list of tuples): List containing details of order items.
        - order_date (str): Date of the order.
        - driver (dict): Dictionary containing driver details.
        - total (str): Total price of the order.
        """
        items = self.get_items(customer_row, order_item_rows)
        transaction = {
            "order_id": customer_row[0],
            "store_id": 1155231,
            "driver_id": driver["driver_id"],
            "order_date": order_date,
            "customer": {
                "customer_id": customer_row[1],
                "first_name": customer_row[2],
                "last_name": customer_row[3],
                "phone": customer_row[4],
                "address": customer_row[5],
                "post_code": customer_row[6]
            },
            "commission_rate": driver["commission_rate"],
            "order_total": total,
            "items": items
        }
        self.transaction.upsert_document(transaction, "order_id")

    def form_to_transaction(self, form_data):
        """
        Constructs a transaction document from a form's data and stores it in the MongoDB collection.

        Parameters:
        - form_data (dict): Dictionary containing form input data.
        """
        transaction = {}
        if form_data["order-id"] != "":
            transaction["order_id"] = int(form_data["order-id"])
        if form_data["store-id"] != "":
            transaction["store_id"] = int(form_data["store-id"])
        if form_data["driver-id"] != "":
            transaction["driver_id"] = int(form_data["driver-id"])
        if form_data["selected-date"] != "":
            transaction["order_date"] = form_data["selected-date"]
        customer = {}
        if form_data["customer-id"] != "":
            customer["customer_id"] = int(form_data["customer-id"])
        if form_data["first-name"] != "":
            customer["first_name"] = form_data["first-name"]
        if form_data["last-name"] != "":
            customer["last_name"] = form_data["last-name"]
        if form_data["phone-no"] != "":
            customer["phone"] = form_data["phone-no"]
        if form_data["address"] != "":
            customer["address"] = form_data["address"]
        if form_data["postcode"] != "":
            customer["post_code"] = form_data["postcode"]
        transaction["customer"] = customer
        if form_data["commission-rate"] != "":
            transaction["commission_rate"] = int(form_data["commission-rate"])
        if form_data["commission-rate"] != "":
            transaction["commission_rate"] = form_data["commission-rate"]
        if form_data["order-total"] != "":
            transaction["order_total"] = form_data["order-total"]
        items = []
        order_item_ids = form_data.getlist('order-item-id')
        product_names = form_data.getlist('items')
        quantities = form_data.getlist('quantity')
        list_prices = form_data.getlist('item-price')
        for i in range(len(product_names)):
            item = {}
            if i < len(order_item_ids) and order_item_ids[i] != "":
                item["order_item_id"] = int(order_item_ids[i])
            if i < len(product_names) and product_names[i] != "":
                item["product_name"] = product_names[i]
            if i < len(quantities) and quantities[i] != "":
                item["quantity"] = int(quantities[i])
            if i < len(list_prices) and list_prices[i] != "":
                item["list_price"] = list_prices[i]
            items.append(item)
        transaction["items"] = items
        self.transaction.upsert_document(transaction, "order_id")

class FrequencyTable:
    """
    A class to represent a frequency table which keeps track of the frequency of strings.
    """

    def __init__(self):
        """
        Initializes the FrequencyTable object with an empty dictionary to store string frequencies.
        """
        self.table = {}

    def add(self, string, quantity):
        """
        Adds or updates the frequency of a given string by the specified quantity.

        Parameters:
        - string (str): The string whose frequency needs to be added or updated.
        - quantity (int): The quantity to add to the current frequency of the string.
        """
        if string not in self.table:
            self.table[string] = 0
        self.table[string] += quantity

    def most_frequent(self):
        """
        Determines the most frequently occurring string(s) in the table.

        Returns:
        - str: A string containing the most frequent string(s) separated by commas.
        """
        max_value = max(self.table.values())
        most_frequent_items = [k for k, v in self.table.items() if v == max_value]
        return ', '.join(most_frequent_items)

class Main(metaclass=Singleton):
    """
    The central class, Main is designed for instantiation within a Flask application.
    Upon creation, it sets up all necessary connections. It handles errors and provides data to the Flask application.
    """

    def __init__(self):
        """
        Initializes the Main object with connections to SQL Database, MongoDB, and Azure Blob Storage.
        """
        SQLDatabase()
        MongoDB("transactions")
        MongoDB("dockets")
        AzureBlob()
        
    def import_transactions(self, order_date):
        """
        Imports transactions from Joe's Place on a specific order date.

        Parameters:
        - order_date (str): The date of the order to import transactions from.

        Returns:
        - tuple: A tuple containing a list of results and an error message (if any).
        """
        try:
            results = []
            customer_rows, order_item_rows = SQLDatabase().get_rows(order_date)
            for customer_row in customer_rows:
                order_id, blob_name, blob_url, driver, total = PDF().create_pdf(customer_row, order_item_rows)
                Dockets().create_docket(order_id, blob_name, blob_url)
                Transactions().create_transaction(customer_row, order_item_rows, order_date, driver, total)
                results.extend([
                    [order_id, "transactions collection", f"/transactions/{order_id}"], 
                    [order_id, "dockets collection", f"/dockets/{order_id}"], 
                    [order_id, "pdf-dockets container", f"/pdf/{blob_name}"]
                ])
            if (customer_rows == []):
                if order_date:
                    raise ValueError(f"No transactions found on {order_date}.")
                else:
                    raise ValueError("No transactions found.")
            return results, None
        except Exception as e:
            return None, e

    def daily_summary(self, summary_date):
        """
        Generates a daily summary of transactions on a specific date.

        Parameters:
        - summary_date (str): The date to generate the summary for.

        Returns:
        - tuple: A tuple containing a list of results and a message.
        """
        try:
            transactions = MongoDB("transactions").get_transactions_by_date(summary_date)
            if not transactions:
                raise ValueError(f"No data for {summary_date} previously imported from Joe's Place")
            product_table = FrequencyTable()
            total_sales = 0
            total_orders = 0
            for transaction in transactions:
                total_sales += Decimal(transaction["order_total"])
                total_orders += 1
                for item in transaction["items"]:
                    product_table.add(item["product_name"], item["quantity"])
            best_product = product_table.most_frequent()
            return_result = [1155231, summary_date, total_sales, total_orders, best_product]
            existing_summary_id = SQLDatabase().summary_exists(summary_date)
            if existing_summary_id:
                return [existing_summary_id, *return_result], f"NOTE: Not pushed to Joe's Place. Encountered pre-existing summary with date {summary_date}" 
            summary_id = SQLDatabase().set_summary_row(1155231, summary_date, total_sales, total_orders, best_product)
            return [summary_id, *return_result], f"NOTE: Pushed to Joe's Place. No pre-existing summary with date {summary_date}"
        except Exception as e:
            return None, f"Error: {e}"
    
    def get_pdf(self, pdf_name):
        """
        Retrieves a PDF with a specific name from Azure Blob Storage.

        Parameters:
        - pdf_name (str): The name of the PDF to retrieve.

        Returns:
        - bytes or None: PDF content in bytes or None if there's an error.
        """
        try:
            return AzureBlob().get_pdf(pdf_name)
        except Exception as e:
            return None
        
    def get_document(self, collection_name, order_id):
        """
        Retrieves a document from MongoDB based on its order ID.

        Parameters:
        - collection_name (str): The name of the MongoDB collection.
        - order_id (int): The order ID of the document to retrieve.

        Returns:
        - dict or None: The document as a dictionary or None if there's an error.
        """
        try:
            return MongoDB(collection_name).get_document_by_order_id(int(order_id))
        except Exception as e:
            return None
        
    def get_driver_by_post_code(self, post_code):
        """
        Retrieves a driver based on the post code from MongoDB.

        Parameters:
        - post_code (str): The post code to search for.

        Returns:
        - dict or None: The driver as a dictionary or None if there's an error.
        """
        try:
            return MongoDB("drivers").get_driver_by_post_code(post_code)
        except Exception as e:
            return None
        
    def get_distinct_items(self):
        """
        Retrieves a list of distinct items from the SQL Database.

        Returns:
        - list or None: A list of distinct items or None if there's an error.
        """
        try:
            return SQLDatabase().get_distinct_items()
        except Exception as e:
            return None
        
    def submit_input(self, form_data):
        """
        Processes and submits form data to create or update transactions.

        Parameters:
        - form_data (dict): The form data to process.

        Returns:
        - tuple: A tuple containing a URL and an error message (if any).
        """
        try:
            Transactions().form_to_transaction(form_data)
            return f"/transactions/{form_data['order-id']}", None
        except Exception as e:
            return None, e
        
    def import_and_summarise_all_dates(self):
        dates = SQLDatabase().get_distinct_dates()
        for date in dates:
            date_string = date[0].isoformat()
            print (date_string)
            a, b = self.import_transactions(date_string)
            c, d = self.daily_summary(date_string)
            print (a)
            print (b)
            print (c)
            print (d)
        
    def close_connections(self):
        """
        Closes all open connections to the SQL Database and MongoDB.
        """
        SQLDatabase().close()
        MongoDB("transactions").close()
        MongoDB("dockets").close()

if __name__ == "__main__":
    Main().import_and_summarise_all_dates()