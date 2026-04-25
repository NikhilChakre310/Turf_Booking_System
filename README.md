# 🎟️ Book My Arena - Premium Turf Booking System

A fully functional, enterprise-grade turf and sports arena booking platform inspired by BookMyShow. Built with Python and Flask.

## 🌟 Enterprise Features

* **Smart Booking Engine:** Users can select dates, available time slots, and avoid double-bookings. Includes a strict 24-hour cancellation policy.
* **Real UPI Payment Gateway:** Direct PhonePe/GPay UPI integration with dynamic QR code generation and UTR verification.
* **QR Code E-Tickets:** Automatically generates scannable QR codes for every successful booking.
* **Multi-City & Category Filters:** Users can filter arenas by city (e.g., Mumbai, Delhi) and sports categories (Football, Cricket, Tennis, etc.).
* **Loyalty & Rewards Program:** Users automatically earn reward points on every booking.
* **User Reviews & Ratings:** 1-5 star rating system for turfs after a booking is completed.
* **Admin Analytics Dashboard:** Visual revenue charts and turf popularity graphs powered by Chart.js. Admin can also manage inventory and view user contact info.
* **Production Ready:** Configured with `gunicorn` and `.env` environment variables for secure cloud deployment.

## 🛠️ Tech Stack

* **Backend:** Python 3, Flask
* **Database:** SQLite
* **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2 Templates
* **Integrations:** Chart.js (Analytics), Google Chart API (QR Codes)

## 🚀 How to Run Locally

**1. Clone the repository:**
```bash
git clone https://github.com/NikhilChakre310/Turf_Booking_System.git
cd Turf_Booking_System
```

**2. Create a virtual environment (Recommended):**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Set up Environment Variables:**
Rename the `.env.example` file to `.env` and configure your secure keys and Business UPI ID:
```env
SECRET_KEY=your_secure_random_key
ADMIN_PASSWORD=admin123
UPI_ID=yourbusiness@ybl
```

**5. Run the application:**
```bash
python app.py
```
*(Note: The application will automatically create the `turf.db` database and populate it with sample turfs on the first run!)*

**6. Open in Browser:**
Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)

## 👑 Default Admin Credentials

To access the Admin Analytics Dashboard and add new turfs, use the default credentials:
* **Email:** `admin@turf.com`
* **Password:** `admin123` *(Unless changed in your `.env` file)*

## ☁️ Deployment

This application includes a `Procfile` and is fully ready to be deployed on platforms like **Render**, **Heroku**, or **PythonAnywhere**. Just ensure you set your `.env` variables in your hosting provider's dashboard!