from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Supabase Connection
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# --- MIDDLEWARE / HELPERS ---
def get_user_profile(user_id):
    """Fetch the profile from the database"""
    try:
        response = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
        return response.data
    except:
        return None

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    email = request.form.get('email')
    password = request.form.get('password')
    username = request.form.get('username')

    try:
        # 1. Sign up in Supabase Auth (This triggers the verification email)
        # We pass the username as 'display_name' or metadata
        auth_response = supabase.auth.sign_up({
            "email": email, 
            "password": password,
            "options": {"data": {"username": username}}
        })
        
        if auth_response.user:
            # 2. Initialize the profile in the database
            # Note: The user won't be able to log in until they click the email link
            user_data = {
                "id": auth_response.user.id,
                "username": username,
                "coin_balance": 50,
                "power_level": 0 # Default citizen
            }
            supabase.table('profiles').insert(user_data).execute()
            
            return render_template('verify_notice.html', email=email)
            
    except Exception as e:
        return f"Registration Error: {str(e)}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    email = request.form.get('email')
    password = request.form.get('password')
    
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        if response.user:
            # Check if email is confirmed
            if not response.user.email_confirmed_at:
                return "<h1>Please verify your email first!</h1><p>Check your inbox for the confirmation link.</p>"

            session['user_id'] = response.user.id
            profile = get_user_profile(response.user.id)
            session['username'] = profile['username'] if profile else "Citizen"
            
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        return "Login Failed. Ensure your email is verified and credentials are correct."

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    profile = get_user_profile(session['user_id'])
    
    if not profile:
        return "Profile not found. Please contact Admin."

    return render_template('dashboard.html', profile=profile)

# --- ADMIN SECTION ---
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    profile = get_user_profile(session['user_id'])
    
    # Only allow access if Power Level is 99 (The King)
    if not profile or profile.get('power_level') < 99:
        return "<h1>Access Denied</h1><p>You do not have Royal permissions.</p>", 403
        
    # Fetch all users for the admin to see
    users_list = supabase.table('profiles').select('*').execute()
    
    return render_template('admin.html', users=users_list.data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    # FIX: This port binding prevents the infinite loading on Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)