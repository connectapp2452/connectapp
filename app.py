from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# This uses the secure key we added to Render/ENV
app.secret_key = os.getenv("SECRET_KEY")

# Supabase Connection (Backend 'God Mode' using Service Role Key)
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# --- ROUTES ---

@app.route('/')
def home():
    # This now points to your animated, professional landing page
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    email = request.form.get('email')
    password = request.form.get('password')
    username = request.form.get('username')

    try:
        # 1. Sign up the user in Supabase Auth
        auth_response = supabase.auth.sign_up({"email": email, "password": password})
        
        if auth_response.user:
            # 2. Create their Kingdom Profile with 50 Welcome Coins
            user_data = {
                "id": auth_response.user.id,
                "username": username,
                "coin_balance": 50,  # The "New King" welcome bonus
                "power_level": 0     # 0 = Citizen, 99 = Admin
            }
            supabase.table('profiles').insert(user_data).execute()
            
            # Store session info
            session['user_id'] = auth_response.user.id
            session['username'] = username
            
            return redirect(url_for('dashboard'))
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    email = request.form.get('email')
    password = request.form.get('password')
    
    try:
        # Authenticate user
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            session['user_id'] = response.user.id
            # Fetch username from our profiles table
            profile = supabase.table('profiles').select('username').eq('id', response.user.id).single().execute()
            session['username'] = profile.data['username']
            return redirect(url_for('dashboard'))
    except Exception as e:
        return "Login Failed. Check your credentials."

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Fetch real-time coin balance for the user
    user_id = session['user_id']
    profile = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
    
    return f"""
    <h1>Welcome to the Kingdom, {session['username']}!</h1>
    <p>Your Balance: 💰 {profile.data['coin_balance']} ConnectCoins</p>
    <a href='/logout'>Logout</a>
    """

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)