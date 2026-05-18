import pymysql

passwords = ["QasimNizam123.", "QasimNizam123", "", "root", "admin", "password", "12345678", "1234", "mysql"]
success = None

for p in passwords:
    try:
        conn = pymysql.connect(host='localhost', user='root', password=p)
        success = p
        conn.close()
        break
    except pymysql.err.OperationalError:
        pass

if success is not None:
    print(f"SUCCESS: '{success}'")
else:
    print("FAILED ALL")
