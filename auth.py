import mysql.connector as mc
import hashlib

# Fungsi untuk meng-hash password
def hash_password(password):
    # Menggunakan algoritma SHA256 untuk hashing
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password

# Fungsi untuk verifikasi login
def verify_user_login(username, password):
    try:
        conn = mc.connect(
            host="localhost",
            user="root",
            password="ivonvp464394",
            database="crops",
            auth_plugin="mysql_native_password"
        )
        cursor = conn.cursor()

        query = "SELECT password FROM user WHERE username = %s"
        cursor.execute(query, (username,))
        stored_password = cursor.fetchone()

        if stored_password and hash_password(password) == stored_password[0]:
            cursor.close()
            conn.close()
            return True
        else:
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print("An error occurred during login:", e)
        return False
