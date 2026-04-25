from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "super_secret_turf_key"
DB_NAME = "turf.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS turfs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    image TEXT NOT NULL,
                    description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    turf_id INTEGER,
                    date TEXT NOT NULL,
                    time_slot TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(turf_id) REFERENCES turfs(id))''')
    
    c.execute("SELECT * FROM users WHERE email='admin@turf.com'")
    if not c.fetchone():
        hashed_pw = generate_password_hash("admin123")
        c.execute("INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, ?)", 
                  ("Admin", "admin@turf.com", hashed_pw, 1))
        
    c.execute("SELECT * FROM turfs")
    if not c.fetchone():
        sample_turfs = [
            ("Green Arena", "Football", 1000, "https://images.unsplash.com/photo-1529900845347-1510af14c552?auto=format&fit=crop&w=600&q=80", "Premium 5v5 football turf with artificial grass."),
            ("Smashers Ground", "Cricket", 800, "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=600&q=80", "Box cricket turf with high nets and bright lighting.")
        ]
        c.executemany("INSERT INTO turfs (name, sport, price, image, description) VALUES (?, ?, ?, ?, ?)", sample_turfs)
        
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db()
    search = request.args.get('search', '')
    if search:
        turfs = conn.execute("SELECT * FROM turfs WHERE name LIKE ? OR sport LIKE ?", ('%'+search+'%', '%'+search+'%')).fetchall()
    else:
        turfs = conn.execute("SELECT * FROM turfs").fetchall()
    conn.close()
    return render_template('index.html', turfs=turfs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
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

@app.route('/turf/<int:id>', methods=['GET', 'POST'])
def turf(id):
    conn = get_db()
    turf = conn.execute("SELECT * FROM turfs WHERE id = ?", (id,)).fetchone()
    
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please login to book a turf.', 'warning')
            return redirect(url_for('login'))
            
        date = request.form['date']
        time_slot = request.form['time_slot']
        
        existing = conn.execute("SELECT * FROM bookings WHERE turf_id=? AND date=? AND time_slot=?", (id, date, time_slot)).fetchone()
        if existing:
            flash('This time slot is already booked!', 'danger')
        else:
            conn.execute("INSERT INTO bookings (user_id, turf_id, date, time_slot) VALUES (?, ?, ?, ?)",
                         (session['user_id'], id, date, time_slot))
            conn.commit()
            flash('Booking confirmed! Payment to be collected at the venue.', 'success')
            return redirect(url_for('dashboard'))
            
    today = datetime.today().strftime('%Y-%m-%d')
    bookings = conn.execute("SELECT time_slot FROM bookings WHERE turf_id = ? AND date = ?", (id, today)).fetchall()
    booked_slots = [b['time_slot'] for b in bookings]
    conn.close()
    
    time_slots = ["08:00 AM", "10:00 AM", "12:00 PM", "02:00 PM", "04:00 PM", "06:00 PM", "08:00 PM", "10:00 PM"]
    return render_template('turf.html', turf=turf, time_slots=time_slots, booked_slots=booked_slots, today=today)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    bookings = conn.execute('''SELECT b.id, t.name, t.sport, b.date, b.time_slot, t.price 
                               FROM bookings b 
                               JOIN turfs t ON b.turf_id = t.id 
                               WHERE b.user_id = ? ORDER BY b.date DESC''', (session['user_id'],)).fetchall()
    conn.close()
    
    # Calculate if cancellable (more than 24 hrs away)
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
            conn.execute("DELETE FROM bookings WHERE id = ?", (id,))
            conn.commit()
            flash('Booking cancelled successfully.', 'success')
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
        price = request.form['price']
        image = request.form['image']
        desc = request.form['description']
        conn.execute("INSERT INTO turfs (name, sport, price, image, description) VALUES (?, ?, ?, ?, ?)",
                     (name, sport, price, image, desc))
        conn.commit()
        flash('Turf added successfully!', 'success')
        
    all_bookings = conn.execute('''SELECT b.id, u.name as user_name, t.name as turf_name, b.date, b.time_slot 
                                   FROM bookings b
                                   JOIN users u ON b.user_id = u.id
                                   JOIN turfs t ON b.turf_id = t.id ORDER BY b.date DESC''').fetchall()
    turfs = conn.execute("SELECT * FROM turfs").fetchall()
    conn.close()
    return render_template('admin.html', bookings=all_bookings, turfs=turfs)

if __name__ == '__main__':
    if not os.path.exists(DB_NAME):
        init_db()
    app.run(debug=True)
