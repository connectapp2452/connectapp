from flask import Flask, render_template, request, redirect, url_for, session
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Supabase God Mode Connection
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

@app.route('/')
def home():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    username = request.form.get('username')

    # 1. Register in Supabase Auth
    user = supabase.auth.sign_up({"email": email, "password": password})
    
    if user:
        # 2. Create Profile with 10 Welcome Coins (Your first Reward Task!)
        data = {
            "id": user.user.id,
            "username": username,
            "coin_balance": 10,  # Reward them for joining!
            "power_level": 0
        }
        supabase.table('profiles').insert(data).execute()
        return "<h1>Success! You earned 10 Welcome Coins!</h1>"
    
    return "Error creating account."

if __name__ == "__main__":
    app.run(debug=True)