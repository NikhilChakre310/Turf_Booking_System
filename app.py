from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_dev_secret_key_123")
DB_NAME = "turf.db"
BUSINESS_UPI_ID = os.environ.get("UPI_ID", "your-business-upi@ybl")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    phone TEXT,
                    loyalty_points INTEGER DEFAULT 0,
                    is_admin INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS turfs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    city TEXT DEFAULT 'Mumbai',
                    price INTEGER NOT NULL,
                    image TEXT NOT NULL,
                    description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    turf_id INTEGER,
                    date TEXT NOT NULL,
                    time_slot TEXT NOT NULL,
                    total_amount INTEGER DEFAULT 0,
                    qr_data TEXT,
                    utr_number TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(turf_id) REFERENCES turfs(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    turf_id INTEGER,
                    rating INTEGER,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
                    
    c.execute("SELECT * FROM users WHERE email='admin@turf.com'")
    if not c.fetchone():
        hashed_pw = generate_password_hash(os.environ.get("ADMIN_PASSWORD", "admin123"))
        c.execute("INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, ?)", 
                  ("Admin", "admin@turf.com", hashed_pw, 1))
        
    c.execute("SELECT * FROM turfs")
    if not c.fetchone():
        sample_turfs = [
            ("Green Arena", "Football", "Mumbai", 1000, "https://images.unsplash.com/photo-1529900845347-1510af14c552?auto=format&fit=crop&w=600&q=80", "Premium 5v5 football turf with artificial grass."),
            ("Smashers Ground", "Cricket", "Delhi", 800, "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=600&q=80", "Box cricket turf with high nets and bright lighting.")
        ]
        c.executemany("INSERT INTO turfs (name, sport, city, price, image, description) VALUES (?, ?, ?, ?, ?, ?)", sample_turfs)
        
    conn.commit()
    conn.close()

def upgrade_db():
    conn = sqlite3.connect(DB_NAME)
    try: conn.execute("ALTER TABLE turfs ADD COLUMN city TEXT DEFAULT 'Mumbai'")
    except: pass
    try: conn.execute("ALTER TABLE users ADD COLUMN phone TEXT")
    except: pass
    try: conn.execute("ALTER TABLE users ADD COLUMN loyalty_points INTEGER DEFAULT 0")
    except: pass
    try: conn.execute("ALTER TABLE bookings ADD COLUMN total_amount INTEGER DEFAULT 0")
    except: pass
    try: conn.execute("ALTER TABLE bookings ADD COLUMN qr_data TEXT")
    except: pass
    try: conn.execute("ALTER TABLE bookings ADD COLUMN utr_number TEXT")
    except: pass
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

with app.app_context():
    init_db()
    upgrade_db()

@app.context_processor
def inject_cities():
    try:
        conn = get_db()
        cities = [row['city'] for row in conn.execute("SELECT DISTINCT city FROM turfs WHERE city IS NOT NULL").fetchall()]
        conn.close()
    except:
        cities = []
    return dict(available_cities=cities)

@app.route('/')
def index():
    conn = get_db()
    search = request.args.get('search', '')
    city = request.args.get('city', '')
    category = request.args.get('category', '')
    
    query = "SELECT * FROM turfs WHERE 1=1"
    params = []
    
    if search:
        query += " AND (name LIKE ? OR sport LIKE ?)"
        params.extend(['%'+search+'%', '%'+search+'%'])
    if city:
        query += " AND city = ?"
        params.append(city)
    if category:
        query += " AND sport = ?"
        params.append(category)
        
    turfs = conn.execute(query, params).fetchall()
        
    # Get average ratings
    turfs_with_ratings = []
    for t in turfs:
        t_dict = dict(t)
        avg = conn.execute("SELECT AVG(rating) as avg_rating FROM reviews WHERE turf_id=?", (t['id'],)).fetchone()['avg_rating']
        t_dict['rating'] = round(avg, 1) if avg else "New"
        turfs_with_ratings.append(t_dict)
        
    conn.close()
    return render_template('index.html', turfs=turfs_with_ratings, current_city=city, current_category=category)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = generate_password_hash(request.form['password'])
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)", (name, email, phone, password))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['is_admin'] = user['is_admin']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    if request.method == 'POST':
        phone = request.form['phone']
        name = request.form['name']
        conn.execute("UPDATE users SET name=?, phone=? WHERE id=?", (name, phone, session['user_id']))
        conn.commit()
        session['name'] = name
        flash('Profile updated successfully!', 'success')
        
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/turf/<int:id>', methods=['GET', 'POST'])
def turf(id):
    conn = get_db()
    turf = conn.execute("SELECT * FROM turfs WHERE id = ?", (id,)).fetchone()
    reviews = conn.execute('''SELECT r.*, u.name as user_name FROM reviews r 
                              JOIN users u ON r.user_id = u.id 
                              WHERE turf_id = ? ORDER BY created_at DESC''', (id,)).fetchall()
    
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please login to book a turf.', 'warning')
            return redirect(url_for('login'))
            
        date = request.form['date']
        time_slot = request.form['time_slot']
        
        existing = conn.execute("SELECT * FROM bookings WHERE turf_id=? AND date=? AND time_slot=?", (id, date, time_slot)).fetchone()
        if existing:
            flash('This time slot is already booked!', 'danger')
            return redirect(url_for('turf', id=id))
            
        # Store in session and go to checkout
        session['pending_booking'] = {
            'turf_id': id,
            'turf_name': turf['name'],
            'price': turf['price'],
            'date': date,
            'time_slot': time_slot
        }
        return redirect(url_for('checkout'))
            
    today = datetime.today().strftime('%Y-%m-%d')
    bookings = conn.execute("SELECT time_slot FROM bookings WHERE turf_id = ? AND date = ?", (id, today)).fetchall()
    booked_slots = [b['time_slot'] for b in bookings]
    conn.close()
    
    time_slots = ["08:00 AM", "10:00 AM", "12:00 PM", "02:00 PM", "04:00 PM", "06:00 PM", "08:00 PM", "10:00 PM"]
    return render_template('turf.html', turf=turf, time_slots=time_slots, booked_slots=booked_slots, today=today, reviews=reviews)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session or 'pending_booking' not in session:
        return redirect(url_for('index'))
        
    booking = session['pending_booking']
    final_price = booking['price']
    discount = 0
    promo = request.args.get('promo', '').upper()
    
    if promo == 'WELCOME50':
        discount = final_price // 2
        final_price -= discount
        flash('WELCOME50 Promo applied! 50% off.', 'success')

    merchant_name = "BookMyArena"
    upi_url = f"upi://pay?pa={BUSINESS_UPI_ID}&pn={merchant_name}&am={final_price}&cu=INR"

    if request.method == 'POST':
        utr_number = request.form.get('utr_number', '')
        if not utr_number or len(utr_number) < 8:
            flash('Please enter a valid UTR / Transaction ID from your payment app.', 'danger')
            return redirect(request.url)

        conn = get_db()
        qr_data = f"BMA-{session['user_id']}-{booking['turf_id']}-{booking['date']}-{booking['time_slot'].replace(' ', '')}"
        
        # Insert booking
        conn.execute('''INSERT INTO bookings (user_id, turf_id, date, time_slot, total_amount, qr_data, utr_number) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (session['user_id'], booking['turf_id'], booking['date'], booking['time_slot'], final_price, qr_data, utr_number))
                     
        # Add loyalty points (5% of final price)
        points_earned = max(1, final_price // 20)
        conn.execute("UPDATE users SET loyalty_points = loyalty_points + ? WHERE id = ?", (points_earned, session['user_id']))
        
        conn.commit()
        conn.close()
        
        session.pop('pending_booking', None)
        flash(f'Payment Successful! Ticket generated. You earned {points_earned} reward points!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('checkout.html', booking=booking, final_price=final_price, discount=discount, promo=promo, upi_url=upi_url, business_upi=BUSINESS_UPI_ID)

@app.route('/review/<int:turf_id>', methods=['POST'])
def add_review(turf_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    rating = int(request.form['rating'])
    comment = request.form['comment']
    
    conn = get_db()
    conn.execute("INSERT INTO reviews (user_id, turf_id, rating, comment) VALUES (?, ?, ?, ?)", 
                 (session['user_id'], turf_id, rating, comment))
    conn.commit()
    conn.close()
    
    flash('Thank you for your review!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    bookings = conn.execute('''SELECT b.id, b.turf_id, t.name, t.sport, t.city, b.date, b.time_slot, b.total_amount, b.qr_data, t.price 
                               FROM bookings b 
                               JOIN turfs t ON b.turf_id = t.id 
                               WHERE b.user_id = ? ORDER BY b.date DESC''', (session['user_id'],)).fetchall()
    conn.close()
    
    now = datetime.now()
    bookings_with_status = []
    for b in bookings:
        b_dict = dict(b)
        try:
            booking_dt = datetime.strptime(f"{b['date']} {b['time_slot']}", '%Y-%m-%d %I:%M %p')
            b_dict['is_past'] = booking_dt < now
            b_dict['can_cancel'] = (booking_dt - now).total_seconds() >= 24 * 3600
        except Exception:
            b_dict['is_past'] = False
            b_dict['can_cancel'] = False
            
        if not b_dict.get('total_amount'):
            b_dict['total_amount'] = b_dict['price']
            
        bookings_with_status.append(b_dict)

    return render_template('dashboard.html', bookings=bookings_with_status)

@app.route('/cancel_booking/<int:id>')
def cancel_booking(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    booking = conn.execute("SELECT * FROM bookings WHERE id = ? AND user_id = ?", (id, session['user_id'])).fetchone()
    
    if not booking:
        flash('Booking not found.', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))
        
    try:
        booking_dt = datetime.strptime(f"{booking['date']} {booking['time_slot']}", '%Y-%m-%d %I:%M %p')
        now = datetime.now()
        
        if booking_dt < now:
            flash('Cancellation Failed: This booking is already in the past.', 'danger')
        elif (booking_dt - now).total_seconds() < 24 * 3600:
            flash('Cancellation Failed: You cannot cancel a booking within 24 hours of the slot time.', 'danger')
        else:
            # Deduct loyalty points
            points_to_deduct = max(1, booking['total_amount'] // 20) if booking['total_amount'] else 0
            conn.execute("UPDATE users SET loyalty_points = MAX(0, loyalty_points - ?) WHERE id = ?", (points_to_deduct, session['user_id']))
            conn.execute("DELETE FROM bookings WHERE id = ?", (id,))
            conn.commit()
            flash('Booking cancelled successfully. Refund initiated.', 'success')
    except Exception as e:
        flash('Error processing cancellation.', 'danger')

    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('is_admin'):
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
        
    conn = get_db()
    if request.method == 'POST':
        name = request.form['name']
        sport = request.form['sport']
        city = request.form['city']
        price = request.form['price']
        image = request.form['image']
        desc = request.form['description']
        conn.execute("INSERT INTO turfs (name, sport, city, price, image, description) VALUES (?, ?, ?, ?, ?, ?)",
                     (name, sport, city, price, image, desc))
        conn.commit()
        flash('Turf added successfully!', 'success')
        
    all_bookings = conn.execute('''SELECT b.id, u.name as user_name, u.phone as user_phone, t.name as turf_name, b.date, b.time_slot, b.total_amount, b.utr_number 
                                   FROM bookings b
                                   JOIN users u ON b.user_id = u.id
                                   JOIN turfs t ON b.turf_id = t.id ORDER BY b.date DESC''').fetchall()
    turfs = conn.execute("SELECT * FROM turfs").fetchall()
    
    total_revenue = conn.execute("SELECT SUM(total_amount) as total FROM bookings").fetchone()['total'] or 0
    
    turf_stats = conn.execute('''SELECT t.name, COUNT(b.id) as count 
                                 FROM turfs t LEFT JOIN bookings b ON t.id = b.turf_id 
                                 GROUP BY t.id''').fetchall()
    chart_labels = [row['name'] for row in turf_stats]
    chart_data = [row['count'] for row in turf_stats]
    
    conn.close()
    return render_template('admin.html', bookings=all_bookings, turfs=turfs, 
                           total_revenue=total_revenue, chart_labels=json.dumps(chart_labels), chart_data=json.dumps(chart_data))

if __name__ == '__main__':
    app.run(debug=os.environ.get("FLASK_DEBUG", "False").lower() == "true")
