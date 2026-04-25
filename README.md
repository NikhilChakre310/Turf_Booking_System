# Turf Booking System ⚽🏏

A fully functional, responsive Turf Booking Website built with Python (Flask) and SQLite. This project allows users to browse turfs, book time slots, and manage their bookings, while providing an admin panel to add and manage turfs.

## Features 🌟
- **User Authentication:** Sign up, log in, and secure sessions.
- **Dashboard:** Users can view and cancel their upcoming bookings.
- **Booking System:** Select dates and time slots with double-booking prevention.
- **Admin Panel:** Add new turfs, view all system bookings.
- **Zero-Config Database:** Uses SQLite (auto-generates the database and dummy data on the first run).
- **Responsive UI:** Built with Bootstrap 5 for seamless mobile and desktop experience.

## Tech Stack 🛠️
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, Bootstrap 5
- **Database:** SQLite

## How to Run Locally 🚀

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NikhilChakre310/Turf_Booking_System.git
   cd Turf_Booking_System
   ```

2. **Install the required dependencies:**
   *(Optional but recommended: Create a virtual environment first)*
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the website:**
   Open your web browser and go to `http://127.0.0.1:5000/`

## Admin Access 🔑
Upon running the app for the first time, an admin account is automatically created:
- **Email:** `admin@turf.com`
- **Password:** `admin123`

Log in with these credentials to access the **Admin Panel** where you can add new turfs to the system!
