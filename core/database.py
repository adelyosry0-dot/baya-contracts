import sqlite3

def init_db():
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS archive (id INTEGER PRIMARY KEY AUTOINCREMENT, contract_date TEXT, seller_name TEXT, buyer_name TEXT, raw_data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password) VALUES ('admin', '12345')")
    conn.commit()
    conn.close()

def save_to_db(date_val, seller, buyer, raw_json):
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute('INSERT INTO archive (contract_date, seller_name, buyer_name, raw_data) VALUES (?, ?, ?, ?)', (date_val, seller, buyer, raw_json))
    conn.commit()
    conn.close()

def update_in_db(record_id, date_val, seller, buyer, raw_json):
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute('UPDATE archive SET contract_date=?, seller_name=?, buyer_name=?, raw_data=? WHERE id=?', (date_val, seller, buyer, raw_json, record_id))
    conn.commit()
    conn.close()

def delete_from_db(record_id):
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute('DELETE FROM archive WHERE id=?', (record_id,))
    conn.commit()
    conn.close()

def check_login(username, password):
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def update_credentials(new_user, new_pass):
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET username=?, password=? WHERE id=1", (new_user, new_pass))
    conn.commit()
    conn.close()