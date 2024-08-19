from flask import Flask
from threading import Thread
import os

app = Flask('')
@app.route('/')
def home():
    return "Discord bot ok"

def run():
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT is not set
    print(f"Starting Flask app on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
