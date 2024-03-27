import pandas as pd
import mysql.connector as mc
from sqlalchemy import create_engine
import pymysql
import os
import hashlib

#------------------------IMPORT DATA PER KOMODITAS---------------------------------------
# List nama file CSV dan nama tabel MySQL yang sesuai
file_names = ['jagung.csv', 'padi.csv', 'kedelai.csv', 'kacang_tanah.csv', 'kacang_hijau.csv', 'ubi_kayu.csv', 'ubi_jalar.csv']
table_names = ['jagung', 'padi', 'kedelai', 'kacang_tanah', 'kacang_hijau', 'ubi_kayu', 'ubi_jalar']

# Koneksi ke database MySQL
username = "root"
password = "ivonvp464394"
database = "crops"
host = "localhost"
engine = create_engine("mysql+pymysql://" + username + ":" + password + "@" + host + "/" + database)

# Loop melalui setiap file CSV dan tabel MySQL yang sesuai
for file_name, table_name in zip(file_names, table_names):
    # Baca file CSV
    df = pd.read_csv('data/' + file_name, encoding='unicode_escape', sep=';')

    # Simpan dataframe ke dalam tabel MySQL
    df.to_sql(table_name, engine, if_exists='replace')
    print(f'Data imported successfully into {table_name}')

    # Koneksi ke database MySQL
    conn = mc.connect(
        host="localhost",
        user="root",
        password="ivonvp464394",
        database="crops",
        auth_plugin="mysql_native_password"
        
    )

    # Query untuk melakukan update nilai kolom
    update_query = f"""
    UPDATE {table_name}
    SET 
    `Luas Panen` = REPLACE(`Luas Panen`, ',', '.'),
    `Produksi` = REPLACE(`Produksi`, ',', '.'),
    `Prediksi Luas Panen` = REPLACE(`Prediksi Luas Panen`, ',', '.'),
    `Prediksi Produksi` = REPLACE(`Prediksi Produksi`, ',', '.')
    """
    
    # Eksekusi query update
    cursor = conn.cursor()
    cursor.execute(update_query)
    conn.commit()
    print(f'Data in {table_name} updated successfully')

    # Query untuk mengubah tipe data kolom
    alter_query = f"""
    ALTER TABLE {table_name}
    MODIFY `Tahun` INT(4),
    MODIFY `KMeans` INT(1),
    MODIFY `Luas Panen` FLOAT(12, 2),
    MODIFY `Produksi` FLOAT(12, 2),
    MODIFY `Prediksi Luas Panen` FLOAT(12, 2),
    MODIFY `Prediksi Produksi` FLOAT(12, 2)
    """

    # Eksekusi query alter
    cursor.execute(alter_query)
    conn.commit()
    print(f'Data columns in {table_name} updated successfully')

    # Tutup kursor dan koneksi
    cursor.close()
    conn.close()

#-------------------------IMPORT DATA GABUNGAN TANAMAN PANGAN--------------------------------

# Nama file CSV dan nama tabel MySQL yang sesuai
file_name = 'tanaman_pangan.csv'
table_name = 'tanaman_pangan'

# Koneksi ke database MySQL
username = "root"
password = "ivonvp464394"
database = "crops"
host = "localhost"
auth_plugin="mysql_native_password"
engine = create_engine("mysql+pymysql://" + username + ":" + password + "@" + host + "/" + database)

# Baca file CSV
df = pd.read_csv('data/' + file_name, encoding='unicode_escape', sep=',')

# Simpan dataframe ke dalam tabel MySQL
df.to_sql(table_name, engine, if_exists='replace')
print(f'Data imported successfully into {table_name}')

# Koneksi ke database MySQL
conn = mc.connect(
    host="localhost",
    user="root",
    password="ivonvp464394",
    database="crops",
    auth_plugin="mysql_native_password"
)

# Query untuk melakukan update nilai kolom
update_query = f"""
UPDATE {table_name}
SET 
`Luas Panen` = REPLACE(`Luas Panen`, '.', '.'),
`Produksi` = REPLACE(`Produksi`, '.', '.')
"""

# Eksekusi query update
cursor = conn.cursor()
cursor.execute(update_query)
conn.commit()
print(f'Data in {table_name} updated successfully')

# Query untuk mengubah tipe data kolom
alter_query = f"""
ALTER TABLE {table_name}
MODIFY `Tahun` INT(4),
MODIFY `Luas Panen` FLOAT(12, 2),
MODIFY `Produksi` FLOAT(12, 2)
"""

# Eksekusi query alter
cursor.execute(alter_query)
conn.commit()
print(f'Data columns in {table_name} updated successfully')

# Tutup kursor dan koneksi
cursor.close()
conn.close()


def fetch_data(query):
    connection = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="ivonvp464394",
        db="crops",
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    connection.close()
    return data



# Koneksi ke database MySQL untuk membuat tabel 'user'
conn = mc.connect(
    host="localhost",
    user="root",
    password="ivonvp464394",
    database="crops",
    auth_plugin="mysql_native_password"
)
cursor = conn.cursor()

# Query untuk membuat tabel 'user'
create_user_table_query = """
CREATE TABLE IF NOT EXISTS `user` (
  `names` varchar(255) NOT NULL,
  `username` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL
)
"""

# Eksekusi query untuk membuat tabel 'user' 
cursor.execute(create_user_table_query)
conn.commit()

# Tutup kursor dan koneksi
cursor.close()
conn.close()


def hash_password(password):
    # Menggunakan algoritma SHA256 untuk hashing
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password

def add_users(names, usernames, passwords):
    try:
        conn = mc.connect(
            host="localhost",
            user="root",
            password="ivonvp464394",
            database="crops",
            auth_plugin="mysql_native_password"
        )
        cursor = conn.cursor()

        check_user_query = "SELECT COUNT(*) FROM user WHERE username = %s"
        add_user_query = "INSERT INTO user (names, username, password) VALUES (%s, %s, %s)"

        for name, username, password in zip(names, usernames, passwords):
            # Hash password sebelum menyimpannya
            hashed_password = hash_password(password)
            
            cursor.execute(check_user_query, (username,))
            result = cursor.fetchone()[0]
            
            if result == 0:
                cursor.execute(add_user_query, (name, username, hashed_password))
                print(f"User {username} added successfully.")
            else:
                print(f"User {username} already exists. Skipping...")

        conn.commit()
        cursor.close()
        conn.close()
        print("User data added successfully.")
    except Exception as e:
        print("An error occurred while adding users:", e)

# Example data to add users
names = ["Admin 1", "Admin 2"]
usernames = ["admin1", "admin2"]
passwords = ["admin1", "admin2"]

add_users(names, usernames, passwords)
