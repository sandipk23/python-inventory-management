from flask import Flask, render_template, request, redirect, url_for, make_response
import json
import os
import csv
import io

app = Flask(__name__)
DATA_FILE = "inventory_data.json"

# --- DATABASE HELPERS ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- ROUTES ---
@app.route('/')
def index():
    inventory = load_data()
    # Grand Total Calculation
    total_val = sum(item['price'] * item['quantity'] for item in inventory.values())
    return render_template('index.html', inventory=inventory, total_val=total_val)

@app.route('/add', methods=['POST'])
def add_item():
    inventory = load_data()
    name = request.form['name'].strip().capitalize()
    price = float(request.form['price'])
    # Float supports weights like 0.5 kg
    quantity = float(request.form['quantity'])
    category = request.form.get('category', 'General').strip().capitalize()
    unit = request.form.get('unit', 'Pcs')

    if name in inventory:
        inventory[name]['quantity'] += quantity
        inventory[name]['price'] = price
        inventory[name]['category'] = category
        inventory[name]['unit'] = unit
    else:
        inventory[name] = {
            "price": price,
            "quantity": quantity,
            "category": category,
            "unit": unit
        }

    save_data(inventory)
    return redirect(url_for('index'))

@app.route('/sell/<name>', methods=['POST'])
def sell_item(name):
    inventory = load_data()
    qty_to_sell = float(request.form.get("quantity", 0))
    
    if name in inventory:
        if inventory[name]['quantity'] >= qty_to_sell:
            inventory[name]['quantity'] -= qty_to_sell
            
    save_data(inventory)
    return redirect(url_for('index'))

@app.route('/delete/<name>', methods=['POST'])
def delete_item(name):
    inventory = load_data()
    if name in inventory:
        del inventory[name]
        save_data(inventory)
    return redirect(url_for('index'))

@app.route('/download')
def download_csv():
    inventory = load_data()
    si = io.StringIO()
    writer = csv.writer(si)
    
    # Professional CSV Headers
    writer.writerow(['Item Name', 'Category', 'Price (₹)', 'Stock', 'Unit', 'Subtotal Value (₹)'])
    
    for name, d in inventory.items():
        subtotal = d['price'] * d['quantity']
        writer.writerow([
            name, 
            d.get('category', 'General'), 
            d['price'], 
            d['quantity'], 
            d.get('unit', 'Pcs'), 
            f"{subtotal:.2f}"
        ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=shop_inventory_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output

if __name__ == '__main__':
    app.run(debug=True)