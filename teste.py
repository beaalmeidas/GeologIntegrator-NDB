import sqlite3

conn = sqlite3.connect("logitech.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM motoristas")

resultados = cursor.fetchall()

print(resultados)