import sqlite3

conn = sqlite3.connect("stayease.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings(

id INTEGER PRIMARY KEY AUTOINCREMENT,

customer_name TEXT,

phone TEXT,

email TEXT,

aadhar TEXT,

checkin TEXT,

checkout TEXT,

room_type TEXT,

guests INTEGER,

address TEXT

)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS rooms (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    room_number TEXT UNIQUE,

    room_type TEXT,

    price REAL,

    status TEXT

)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS billing (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    booking_id INTEGER,

    customer_name TEXT,

    room_number TEXT,

    room_type TEXT,

    price REAL,

    days INTEGER,

    total REAL,

    bill_date TEXT

)
""")
try:
    cursor.execute("""
    ALTER TABLE bookings
    ADD COLUMN room_number TEXT
    """)
except:
    pass
conn.commit()

conn.close()

print("Database Created Successfully")