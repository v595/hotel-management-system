from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'grandaurum2026secretkey'

UPI_ID = '9079296316@kotakbank'

COUPONS = {
    'AURUM10': 10,
    'GRAND15': 15,
    'LUXURY20': 20,
    'WELCOME5': 5,
    'VIP25': 25
}

ROOM_PRICES = {
    'Classic Single Room': 2500,
    'Superior Double Room': 4500,
    'Deluxe Pool-View Room': 7500,
    'Junior Suite': 12000,
    'Grand Penthouse Suite': 35000,
}

def connect_db():
    conn = sqlite3.connect('hotel.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create tables
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
    guests INTEGER NOT NULL,
    meal TEXT DEFAULT 'Room Only',
    requests TEXT DEFAULT '',
    arrival TEXT DEFAULT '12:00 PM - 3:00 PM',
    nights INTEGER DEFAULT 1,
    price_per_night INTEGER DEFAULT 0,
    subtotal INTEGER DEFAULT 0,
    tax INTEGER DEFAULT 0,
    discount_pct INTEGER DEFAULT 0,
    discount_code TEXT DEFAULT '',
    discount_amt INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    status TEXT DEFAULT 'confirmed',
    upi_id TEXT DEFAULT '9079296316@kotakbank',
    booked_on TEXT DEFAULT ''
)
''')
conn.commit()
conn.close()

# ── HOME ──
@app.route('/')
def home():
    return render_template('index.html')

# ── ROOMS ──
@app.route('/rooms')
def rooms():
    return render_template('rooms.html')

# ── BOOKING ──
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip()
        phone   = request.form.get('phone', '').strip()
        room    = request.form.get('room_type', 'Classic Single Room')
        checkin = request.form.get('checkin', '')
        checkout= request.form.get('checkout', '')
        guests  = int(request.form.get('guests', 1))
        meal    = request.form.get('meal', 'Room Only')
        reqs    = request.form.get('requests', '')
        arrival = request.form.get('arrival', '12:00 PM – 3:00 PM')

        # Calculate nights
        try:
            ci = datetime.strptime(checkin, '%Y-%m-%d')
            co = datetime.strptime(checkout, '%Y-%m-%d')
            nights = max((co - ci).days, 1)
        except:
            nights = 1

        price = ROOM_PRICES.get(room, 2500)
        subtotal = nights * price
        tax = round(subtotal * 0.18)
        base_total = subtotal + tax

        # Discount
        coupon = request.form.get('coupon', '').strip().upper()
        discount_pct = COUPONS.get(coupon, 0)
        discount_amt = round(base_total * discount_pct / 100) if discount_pct else 0
        total = base_total - discount_amt

        booked_on = datetime.now().strftime('%d %b %Y, %I:%M %p')

        conn = connect_db()
        conn.execute('''
            INSERT INTO bookings
            (name, email, phone, room_type, checkin, checkout, guests,
             meal, requests, arrival, nights, price_per_night, subtotal, tax,
             discount_pct, discount_code, discount_amt, total, status, upi_id, booked_on)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (name, email, phone, room, checkin, checkout, guests,
              meal, reqs, arrival, nights, price, subtotal, tax,
              discount_pct, coupon, discount_amt, total, 'confirmed', UPI_ID, booked_on))
        conn.commit()
        booking_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()

        session['last_booking_id'] = booking_id
        return redirect(url_for('success'))

    selected_room = request.args.get('room', '')
    return render_template('booking.html', room_prices=ROOM_PRICES, selected_room=selected_room, upi_id=UPI_ID, coupons=COUPONS)

# ── SUCCESS ──
@app.route('/success')
def success():
    bid = session.get('last_booking_id')
    if not bid:
        return redirect(url_for('home'))
    conn = connect_db()
    booking = conn.execute('SELECT * FROM bookings WHERE id=?', (bid,)).fetchone()
    conn.close()
    return render_template('success.html', booking=booking, upi_id=UPI_ID)

# ── ADMIN ──
@app.route('/admin')
def admin():
    conn = connect_db()
    bookings = conn.execute('SELECT * FROM bookings ORDER BY id DESC').fetchall()
    total_revenue = sum(b['total'] for b in bookings)
    total_guests = sum(b['guests'] for b in bookings)
    conn.close()
    return render_template('admin.html', bookings=bookings,
                           total_revenue=total_revenue,
                           total_guests=total_guests,
                           upi_id=UPI_ID)

# ── DELETE ──
@app.route('/delete/<int:id>')
def delete(id):
    conn = connect_db()
    conn.execute('DELETE FROM bookings WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# ── VALIDATE COUPON (AJAX) ──
@app.route('/validate-coupon', methods=['POST'])
def validate_coupon():
    from flask import jsonify
    code = request.json.get('code', '').strip().upper()
    pct = COUPONS.get(code, 0)
    if pct:
        return jsonify({'valid': True, 'discount': pct, 'message': f'{pct}% discount applied!'})
    return jsonify({'valid': False, 'message': 'Invalid coupon code.'})

if __name__ == '__main__':
    app.run(debug=True)
