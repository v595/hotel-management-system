from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# DATABASE CONNECTION
def connect_db():
    conn = sqlite3.connect('hotel.db')
    conn.row_factory = sqlite3.Row
    return conn

# CREATE DATABASE TABLE
conn = connect_db()

conn.execute('''
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    room_type TEXT NOT NULL,
    checkin TEXT NOT NULL,
    checkout TEXT NOT NULL,
    guests INTEGER NOT NULL
)
''')

conn.commit()
conn.close()

# HOME PAGE
@app.route('/')
def home():
    return render_template('index.html')

# ROOMS PAGE
@app.route('/rooms')
def rooms():
    return render_template('rooms.html')

# BOOKING PAGE
@app.route('/booking', methods=['GET', 'POST'])
def booking():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        room_type = request.form['room_type']
        checkin = request.form['checkin']
        checkout = request.form['checkout']
        guests = request.form['guests']

        conn = connect_db()

        conn.execute('''
        INSERT INTO bookings
        (name, email, phone, room_type, checkin, checkout, guests)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
        (name, email, phone, room_type, checkin, checkout, guests))

        conn.commit()
        conn.close()

        return redirect('/admin')

    return render_template('booking.html')

# ADMIN DASHBOARD
@app.route('/admin')
def admin():

    conn = connect_db()

    bookings = conn.execute('SELECT * FROM bookings').fetchall()

    conn.close()

    return render_template('admin.html', bookings=bookings)

# DELETE BOOKING
@app.route('/delete/<int:id>')
def delete(id):

    conn = connect_db()

    conn.execute('DELETE FROM bookings WHERE id = ?', (id,))

    conn.commit()
    conn.close()

    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)