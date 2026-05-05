from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'secret123'

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  price REAL,
                  quantity INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS sales
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_id INTEGER,
                  quantity INTEGER,
                  total_price REAL)''')

    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        default_products = [
            ("Apple", 50, 100),
            ("Banana", 10, 150),
            ("Milk", 30, 50),
            ("Bread", 25, 40),
            ("Rice", 60, 80),
            ("Eggs", 6, 200)
        ]
        c.executemany("INSERT INTO products VALUES (NULL, ?, ?, ?)", default_products)

    conn.commit()
    conn.close()

init_db()

# ---------- LOGIN ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form['username']
        return redirect('/home')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------- HOME ----------
@app.route('/home')
def home():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()

    return render_template('index.html', products=products)

# ---------- ADD ----------
@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)",
                  (request.form['name'], request.form['price'], request.form['quantity']))

        conn.commit()
        conn.close()
        return redirect('/home')

    return render_template('add_product.html')

# ---------- SELL ----------
@app.route('/sell', methods=['GET', 'POST'])
def sell():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()

    error = None

    if request.method == 'POST':
        pid = request.form['product_id']
        qty = int(request.form['quantity'])

        c.execute("SELECT name, price, quantity FROM products WHERE id=?", (pid,))
        p = c.fetchone()

        if p:
            name, price, stock = p

            if stock >= qty:
                total = price * qty

                c.execute("UPDATE products SET quantity=? WHERE id=?", (stock - qty, pid))
                c.execute("INSERT INTO sales (product_id, quantity, total_price) VALUES (?, ?, ?)",
                          (pid, qty, total))

                conn.commit()
                conn.close()

                return render_template('bill.html',
                                       name=name,
                                       price=price,
                                       quantity=qty,
                                       total=total)

            else:
                error = f"Only {stock} items available! Cannot sell {qty}"

    conn.close()
    return render_template('sell.html', products=products, error=error)
# ---------- SALES ----------
@app.route('/sales')
def sales():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
        SELECT products.name, sales.quantity, sales.total_price
        FROM sales JOIN products ON sales.product_id = products.id
    ''')

    data = c.fetchall()
    conn.close()

    return render_template('sales.html', sales=data)

# ---------- DELETE ----------
@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM sales WHERE product_id=?", (id,))
    c.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/home')

if __name__ == '__main__':
    app.run(debug=True)