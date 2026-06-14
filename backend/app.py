from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
import redis
import json
import socket

load_dotenv()

app = Flask(__name__)
CORS(app)
redis_client = redis.StrictRedis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=0)



@app.route('/be', methods=['GET'])
def get_products():
    container_name = socket.gethostname()
    cached_data = redis_client.get('graphics_cards')
    
    if cached_data:
        print("from cache")
        return jsonify(
            source="Redis Cache",
            backend_node=container_name,
            data=json.loads(cached_data.decode('utf-8'))
        )
    else:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        print("from SQL")
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM graphics_cards")
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        
        redis_client.set('graphics_cards', json.dumps(products))
        return jsonify(
            source="Docker MySQL",
            backend_node=container_name,
            data=products
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)