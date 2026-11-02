
# 🏥 Appointment Booking System

A web-based appointment booking application built using Python, Flask, and MySQL. The system allows patients to register, log in, book appointments, and view their booking history. Administrators can manage and monitor appointments through a dedicated dashboard.

## ✨ Features

### 👤 Patient
- Patient registration and login
- Book appointments by providing personal and appointment details
- View personal appointment history
- Dedicated patient dashboard

### 🛡️ Administrator
- Separate admin login
- Admin dashboard to view all appointments
- View total bookings and appointment details
- Manage appointment records through a centralized dashboard

### ⚙️ General
- Responsive web interface
- MySQL database integration
- Session-based authentication
- Organized Flask templates and static CSS

## 🛠️ Technologies Used

- **Backend:** Python, Flask
- **Database:** MySQL
- **Database Connector:** PyMySQL
- **Frontend:** HTML, CSS
- **Templating:** Jinja2
- **Version Control:** Git and GitHub

## 📁 Project Structure

```text
appointment-booking-system/
├── app.py
├── requirements.txt
├── .gitignore
├── test_db.py
├── static/
│   └── style.css
└── templates/
    ├── admin_dashboard.html
    ├── admin_login.html
    ├── appointments.html
    ├── booking_success.html
    ├── index.html
    ├── patient_dashboard.html
    ├── patient_login.html
    └── register.html
```

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/ayanashalet05/appointment-booking-system.git
cd appointment-booking-system
```

### 2. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root directory. Add your local configuration using the variable names expected by `app.py`.

Example only — replace the placeholder values and match the variable names in your application:

```env
SECRET_KEY=replace_with_a_secure_random_secret
DB_HOST=localhost
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=appointment_booking
```

**Important:** The variable names above are examples. Check your `app.py` to confirm the exact names your application reads. Never commit `.env` or share real passwords and secret keys.

### 5. Create the MySQL database

Open MySQL Workbench and execute:

```sql
CREATE DATABASE appointment_booking;
```

Make sure your application's database tables are created using the setup expected by `app.py`.

### 6. Run the application

```bash
python app.py
```

Open the local address shown in the terminal, commonly:

http://127.0.0.1:5000/

## 🔐 Security Notes

- Keep passwords, secret keys, and database credentials out of source control.
- Store local configuration in `.env`.
- Use a strong, unique Flask secret key.
- Use secure password hashing for user passwords.
- For production deployment, configure HTTPS, secure cookies, and production-ready database credentials.

## 🖼️ Screenshots

Screenshots of the application can be added here to demonstrate the booking page, patient dashboard, and admin dashboard.

## 👩‍💻 Author

**Ayana Shalet**

- GitHub: [@ayanashalet05](https://github.com/ayanashalet05)

## 📄 License

No license has been specified yet.
