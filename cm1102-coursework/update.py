'''import sqlite3

conn = sqlite3.connect('instance/vinyls.db')
cursor = conn.cursor()

cursor.execute("ALTER TABLE VinylsDb ADD COLUMN vinyl_price FLOAT;")

conn.commit()
conn.close()

print("Column added ✅")'''
print("DID NOTHING EDIT FILE!")