import time
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def sync_database_from_host():
    print(" [Init Container] Starting database sync process...")
    docker_conn = None
    
    # 1. รอให้ MySQL ใน Docker พร้อมทำงาน
    for i in range(15):
        try:
            docker_conn = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'db'),
                port=int(os.getenv('DATABASE_PORT', 3306)),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME')
            )
            if docker_conn.is_connected():
                print(" [Docker DB] MySQL is ready!")
                break
        except Exception as e:
            print(f" Waiting for MySQL... Retrying {i+1}/15 (wait 3s)")
            time.sleep(3)
            
    if not docker_conn or not docker_conn.is_connected():
        print(" [Sync Error] Cannot connect to Docker MySQL.")
        return

    try:
        docker_cursor = docker_conn.cursor()
        
        # 2. เชื่อมต่อไปหาคอมพิวเตอร์หลัก (Host DB)
        host_conn = mysql.connector.connect(
            host=os.getenv('HOST_DB_HOST'),
            port=int(os.getenv('HOST_DB_PORT', 3307)),
            user=os.getenv('HOST_DB_USER'),
            password=os.getenv('HOST_DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        host_cursor = host_conn.cursor()
        
        host_cursor.execute("SHOW TABLES")
        host_tables = [row[0] for row in host_cursor.fetchall()]
        
        if not host_tables:
            print(" [Host DB] No tables found in host machine.")
            return

        # 3. เริ่มโคลนตารางและข้อมูล
        for table_name in host_tables:
            print(f"   Cloning: {table_name} ...")
            
            host_cursor.execute(f"SHOW CREATE TABLE {table_name}")
            create_table_sql = host_cursor.fetchone()[1]
            
            try:
                docker_cursor.execute(create_table_sql)
            except mysql.connector.Error as err:
                if err.errno == 1050:
                    print(f"      [Notice] Table '{table_name}' already exists.")
                else:
                    raise err
            
            host_cursor.execute(f"SELECT * FROM {table_name}")
            rows = host_cursor.fetchall()
            
            if rows:
                column_names = [desc[0] for desc in host_cursor.description]
                placeholders = ', '.join(['%s'] * len(column_names))
                columns_str = ', '.join(column_names)
                
                insert_query = f"INSERT IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                docker_cursor.executemany(insert_query, rows)
                print(f"       Synced {len(rows)} rows.")
                
        docker_conn.commit()
        print(" [Success] Database sync completed. Init Container will now exit!")

    except Exception as e:
        print(f" [Sync Error]: {e}")
    finally:
        if 'host_cursor' in locals() and host_cursor: host_cursor.close()
        if 'host_conn' in locals() and host_conn and host_conn.is_connected(): host_conn.close()
        if 'docker_cursor' in locals() and docker_cursor: docker_cursor.close()
        if docker_conn and docker_conn.is_connected(): docker_conn.close()

# สั่งให้ทำงานทันทีเมื่อไฟล์นี้ถูกรัน
if __name__ == '__main__':
    sync_database_from_host()