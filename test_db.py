
import pymysql
from getpass import getpass

password = getpass("Enter MySQL root password: ")

try:
    connection = pymysql.connect(
        host="localhost",
        user="root",
        password=password,
        database="appointment_booking",
        port=3306
    )

    print("MySQL database connected successfully!")

    connection.close()

except Exception as e:
    print("Database connection failed:", e)
