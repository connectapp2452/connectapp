from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import random
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "connect_app_royal_secret_99")

# --- CONFIGURATION & DATABASE ---
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# Secure Admin Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "@Loginlocal2452"

# --- MIDDLEWARE / HELPERS ---

def get_user_profile(user_id):
    """Fetches the latest user data from Supabase profiles table"""
    try:
        response = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
        return response.data
    except Exception:
        return None

@app.context_processor
def inject_version():
    """Forces mobile browsers to refresh CSS by adding a random version number"""
    return dict(version=random.randint(1, 99999))

# --- STANDARD USER ROUTES ---

@app.route('/health')
def health():
    return "Kingdom is Online", 200

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
        auth_response = supabase.auth.sign_up({
            "email": email, 
            "password": password,
            "options": {"data": {"username": username}}
        })
        
        if auth_response.user:
            user_data = {
                "id": auth_response.user.id,
                "username": username,
                "coin_balance": 50,
                "power_level": 0 
            }
            supabase.table('profiles').insert(user_data).execute()
            return render_template('verify_notice.html', email=email)
            
    except Exception as e:
        flash(f"Registration Error: {str(e)}")
        return redirect(url_for('register'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if response.user:
                if not response.user.email_confirmed_at:
                    return render_template('verify_notice.html', email=email, resend=True)

                session['user_id'] = response.user.id
                profile = get_user_profile(response.user.id)
                session['username'] = profile['username'] if profile else "Citizen"
                return redirect(url_for('dashboard'))
        except Exception:
            flash("Login Failed. Check credentials or verify email.")
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    profile = get_user_profile(session['user_id'])
    return render_template('dashboard.html', profile=profile)

@app.route('/earn', methods=['GET', 'POST'])
def earn():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    profile = get_user_profile(user_id)
    if request.method == 'POST':
        task_id = request.form.get('task_id')
        if task_id == 'daily':
            new_balance = profile['coin_balance'] + 10
            supabase.table('profiles').update({"coin_balance": new_balance}).eq('id', user_id).execute()
            flash("Success! +10 Coins added.")
            return redirect(url_for('dashboard'))
    return render_template('earn.html', profile=profile)

# --- MATURE ADMIN SECURITY SYSTEM ---

@app.route('/admin-gate', methods=['GET', 'POST'])
def admin_gate():
    """Secondary security layer for Admin access"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    profile = get_user_profile(session['user_id'])
    
    # Check 1: User must have Power Level 99 in database
    if not profile or profile.get('power_level', 0) < 99:
        flash("You do not have the Royal bloodline for this area.")
        return redirect(url_for('dashboard'))

    # Check 2: Verify hardcoded Admin Credentials
    if request.method == 'POST':
        user = request.form.get('admin_user')
        password = request.form.get('admin_pass')
        
        if user == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_verified'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Incorrect Master Credentials.")
            
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    """The Protected Command Center"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    profile = get_user_profile(session['user_id'])
    
    # Strict Redirection if conditions aren't met
    if not profile or profile.get('power_level', 0) < 99 or not session.get('admin_verified'):
        return redirect(url_for('admin_gate'))
        
    try:
        users_query = supabase.table('profiles').select('*').order('coin_balance', desc=True).execute()
        users_list = users_query.data
    except Exception as e:
        print(f"Admin Table Error: {e}")
        users_list = []
    
    return render_template('admin.html', users=users_list)

@app.route('/admin-logout')
def admin_logout():
    """Locks the Admin Gate without logging the user out of the main app"""
    session.pop('admin_verified', None)
    flash("Admin Gate Locked.")
    return redirect(url_for('dashboard'))

# --- AUTH SYSTEM LOGOUT ---

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    # Render specifically looks for port 10000 by default or the PORT env var
    port = int(os.environ.get("PORT", 10000))
    # Use '0.0.0.0' to ensure it's accessible externally on the network
    app.run(host='0.0.0.0', port=port, debug=False)