import os

# Local Database Connection (Commented out)
# DB_SERVER = r'THARUKA\MSSQL'
# DB_NAME = 'DecordiaDB'
# DB_CONNECTION_STRING = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};Trusted_Connection=yes;'

# Azure SQL Database Connection
DB_PASSWORD = 'Dilshan6116'  # REPLACE this with your actual database password
DB_CONNECTION_STRING = (
    'Driver={ODBC Driver 17 for SQL Server};'
    'Server=tcp:tharukatest.database.windows.net,1433;'
    'Database=DECORDIADB;'
    'Uid=tharuka;'
    f'Pwd={DB_PASSWORD};'
    'Encrypt=yes;'
    'TrustServerCertificate=no;'
    'Connection Timeout=30;'
)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "Decodia@123")

OPENAI_URL = "https://api.openai.com/v1/images/edits"
OPENAI_GENERATE_URL = "https://api.openai.com/v1/images/generations"