# Turf Booking System ⚽🏏

A fully functional, lightweight Turf Booking Website built with Python (Flask), SQLite, HTML, CSS, and Bootstrap.

## Features
* **User Authentication:** Secure Signup, Login, and Logout with hashed passwords.
* **Turf Browsing:** View available turfs and search by name or sport (e.g., Football, Cricket).
* **Booking System:** Select a date and time slot to book a turf. The system automatically prevents double-booking.
* **User Dashboard:** View your upcoming bookings and cancel them if needed.
* **Admin Panel:** Add new turfs, manage details, and view all platform bookings.

## Tech Stack
* **Backend:** Python (Flask)
* **Database:** SQLite (Zero-configuration—auto-creates on first run!)
* **Frontend:** HTML, CSS, Bootstrap 5

---

## How to Run Locally

### 1. Prerequisites
Make sure you have [Python](https://www.python.org/downloads/) installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/NikhilChakre310/Turf_Booking_System.git
cd Turf_Booking_System
```

### 3. Create a Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python app.py
```

### 6. Access the Website
Open your web browser and navigate to: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## Admin Access
The database, tables, and sample data are **auto-generated** the very first time you run `app.py`. 

To access the admin panel to add/manage turfs, log in with the default admin credentials:
* **Email:** `admin@turf.com`
* **Password:** `admin123`
