from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
import redis
import json

load_dotenv()  

app = Flask(__name__)
CORS(app)
redis_client = redis.StrictRedis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=0)

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

@app.route('/be', methods=['GET'])
def get_products():
    
    cached_data = redis_client.get('graphics_cards')
    if cached_data:
        
        print("from cache")
        return jsonify(data=json.loads(cached_data.decode('utf-8')))
       
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
        return jsonify(data=products)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
