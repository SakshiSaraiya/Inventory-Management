import mysql.connector

# Define your Clever Cloud DB credentials
config = {
    "host": "b29irpfxa6i9872pkedp-mysql.services.clever-cloud.com",
    "user": "uolaltmscdu9jy8l",
    "password": "k3bSJkStJHHH9vufjtEc",
    "database": "b29irpfxa6i9872pkedp",
    "port": 3306
}

# Load the SQL file
with open("Inventory Tables.sql", "r") as file:
    sql_commands = file.read()

try:
    # Connect to the database
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    # Split and execute each SQL command
    for command in sql_commands.split(";"):
        command = command.strip()
        if command:
            cursor.execute(command)
    
    conn.commit()
    print("✅ Database initialized successfully.")
except mysql.connector.Error as err:
    print(f"❌ MySQL Error: {err}")
finally:
    cursor.close()
    conn.close()
