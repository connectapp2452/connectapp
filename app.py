from flask import Flask, render_template
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

@app.route('/')
def home():
    return "<h1>The Connect_App Kingdom is Rising!</h1><p>Python Engine: Active ✅</p>"

if __name__ == "__main__":
    app.run(debug=True)