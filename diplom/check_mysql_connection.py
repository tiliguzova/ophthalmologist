import mysql.connector
from mysql.connector import Error

try:
   connection = mysql.connector.connect(
       host='localhost',
       database='db',
       user='admin',
       password='admin'
   )

   if connection.is_connected():
       print("Подключение успешно!")
   else:
       print("Не удалось подключиться.")

except Error as e:
   print(f"Ошибка: {e}")
finally:
   if 'connection' in locals() and connection.is_connected():
       connection.close()
       print("Соединение закрыто.")