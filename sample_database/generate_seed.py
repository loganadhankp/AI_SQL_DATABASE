"""
Generator script to build sample_database/ecommerce.sql with 100+ customers, 30+ products,
200+ orders, multiple items per order, payments, and read-only user setup.
"""

import random
from datetime import datetime, timedelta

random.seed(42)

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin",
    "Seattle", "Denver", "Boston", "Miami", "Atlanta", "San Francisco"
]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna",
    "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Gregory", "Christine", "Frank", "Debra",
    "Alexander", "Rachel", "Raymond", "Catherine", "Patrick", "Carolyn", "Jack", "Janet",
    "Dennis", "Ruth", "Jerry", "Maria", "Tyler", "Heather", "Aaron", "Diane"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson", "Watson",
    "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes",
    "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross", "Foster"
]

PRODUCTS_DATA = [
    # Electronics & Computers
    ("MacBook Pro 16", "Computers", 2499.99, 15),
    ("Dell XPS 15", "Computers", 1799.00, 22),
    ("ThinkPad X1 Carbon", "Computers", 1450.00, 8),   # Stock < 10
    ("ASUS ROG Zephyrus", "Computers", 1899.50, 12),
    ("HP Spectre x360", "Computers", 1299.99, 5),     # Stock < 10
    ("iPad Air M2", "Tablets", 599.00, 35),
    ("Samsung Galaxy Tab S9", "Tablets", 699.99, 18),
    ("iPhone 15 Pro", "Phones", 999.00, 4),           # Stock < 10
    ("Samsung Galaxy S24 Ultra", "Phones", 1199.99, 25),
    ("Google Pixel 8 Pro", "Phones", 899.00, 14),
    ("Sony WH-1000XM5 Headphones", "Audio", 399.99, 45),
    ("Bose QuietComfort Ultra", "Audio", 429.00, 7),   # Stock < 10
    ("AirPods Pro 2nd Gen", "Audio", 249.00, 60),
    ("JBL Flip 6 Bluetooth Speaker", "Audio", 129.95, 80),
    ("Logitech MX Master 3S Mouse", "Accessories", 99.99, 55),
    ("Keychron Q1 Mechanical Keyboard", "Accessories", 169.00, 30),
    ("LG UltraFine 27 Monitor 4K", "Displays", 549.99, 16),
    ("Dell UltraSharp 34 Curved", "Displays", 789.00, 2), # Stock < 10
    
    # Wearables & Smart Home
    ("Apple Watch Series 9", "Wearables", 399.00, 28),
    ("Garmin Fenix 7 Pro", "Wearables", 799.99, 9),    # Stock < 10
    ("Fitbit Charge 6", "Wearables", 159.95, 40),
    ("Amazon Echo Show 10", "Smart Home", 249.99, 32),
    ("Google Nest Learning Thermostat", "Smart Home", 199.00, 24),
    ("Philips Hue Starter Kit", "Smart Home", 179.99, 19),
    
    # Office & Ergonomics
    ("Herman Miller Aeron Chair", "Office", 1250.00, 6), # Stock < 10
    ("Autonomous SmartDesk Pro", "Office", 599.00, 11),
    ("BenQ ScreenBar Monitor Light", "Office", 109.00, 48),
    ("Anker 737 Power Bank 24000mAh", "Accessories", 149.99, 70),
    ("CalDigit TS4 Thunderbolt Dock", "Accessories", 399.95, 3), # Stock < 10
    ("SanDisk 2TB Extreme Portable SSD", "Storage", 179.99, 65),
    ("Samsung T7 Shield 1TB", "Storage", 119.99, 50),
    ("Sony Alpha a7 IV Camera", "Cameras", 2498.00, 1), # Stock < 10
    ("Fujifilm X-T5 Mirrorless", "Cameras", 1699.00, 8), # Stock < 10
    ("Rode NT-USB Mini Microphone", "Audio", 99.00, 42),
    ("Elgato Stream Deck MK.2", "Accessories", 149.99, 36)
]

def generate_sql():
    sql = []
    sql.append("-- ============================================================================")
    sql.append("-- E-COMMERCE SAMPLE DATABASE FOR AI SQL DATABASE ANALYST")
    sql.append("-- Schema: ecommerce_db")
    sql.append("-- Contains: 100 Customers, 35 Products, 220 Orders, 500+ Items, 220 Payments")
    sql.append("-- ============================================================================\n")
    sql.append("CREATE DATABASE IF NOT EXISTS ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    sql.append("USE ecommerce_db;\n")
    
    # Drop tables if exist in reverse order
    sql.append("DROP TABLE IF EXISTS payments;")
    sql.append("DROP TABLE IF EXISTS order_items;")
    sql.append("DROP TABLE IF EXISTS orders;")
    sql.append("DROP TABLE IF EXISTS products;")
    sql.append("DROP TABLE IF EXISTS customers;\n")
    
    # Customers Table
    sql.append("-- 1. CUSTOMERS TABLE")
    sql.append("""CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    city VARCHAR(80) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_customers_city (city),
    INDEX idx_customers_created_at (created_at)
) ENGINE=InnoDB;
""")

    # Products Table
    sql.append("-- 2. PRODUCTS TABLE")
    sql.append("""CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(80) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    INDEX idx_products_category (category),
    INDEX idx_products_price (price),
    INDEX idx_products_stock (stock)
) ENGINE=InnoDB;
""")

    # Orders Table
    sql.append("-- 3. ORDERS TABLE")
    sql.append("""CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATETIME NOT NULL,
    status ENUM('pending', 'processing', 'shipped', 'completed', 'cancelled') NOT NULL DEFAULT 'completed',
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    INDEX idx_orders_customer (customer_id),
    INDEX idx_orders_date (order_date),
    INDEX idx_orders_status (status)
) ENGINE=InnoDB;
""")

    # Order Items Table
    sql.append("-- 4. ORDER ITEMS TABLE")
    sql.append("""CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_items_order (order_id),
    INDEX idx_items_product (product_id)
) ENGINE=InnoDB;
""")

    # Payments Table
    sql.append("-- 5. PAYMENTS TABLE")
    sql.append("""CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_status ENUM('success', 'pending', 'failed', 'refunded') NOT NULL DEFAULT 'success',
    payment_date DATETIME NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_payments_order (order_id),
    INDEX idx_payments_status (payment_status),
    INDEX idx_payments_date (payment_date)
) ENGINE=InnoDB;
""")

    # Populate Customers (100 customers)
    sql.append("-- ============================================================================")
    sql.append("-- SEED DATA: CUSTOMERS (100 Records)")
    sql.append("-- ============================================================================")
    
    customer_rows = []
    base_date = datetime(2025, 1, 15, 10, 0, 0)
    for i in range(1, 101):
        fname = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
        lname = LAST_NAMES[(i - 1) % len(LAST_NAMES)]
        name = f"{fname} {lname}"
        email = f"{fname.lower()}.{lname.lower()}{i}@example.com"
        city = CITIES[(i * 3 + 7) % len(CITIES)]
        cust_created = base_date + timedelta(days=(i * 3) % 360, hours=(i * 7) % 24)
        customer_rows.append(f"({i}, '{name}', '{email}', '{city}', '{cust_created.strftime('%Y-%m-%d %H:%M:%S')}')")
    
    sql.append("INSERT INTO customers (id, name, email, city, created_at) VALUES\n" + ",\n".join(customer_rows) + ";\n")

    # Populate Products (35 products)
    sql.append("-- ============================================================================")
    sql.append("-- SEED DATA: PRODUCTS (35 Records)")
    sql.append("-- ============================================================================")
    product_rows = []
    for i, (pname, cat, price, stock) in enumerate(PRODUCTS_DATA, start=1):
        product_rows.append(f"({i}, '{pname}', '{cat}', {price:.2f}, {stock})")
    sql.append("INSERT INTO products (id, name, category, price, stock) VALUES\n" + ",\n".join(product_rows) + ";\n")

    # Populate Orders (220 orders)
    # Notice: Customers 1 to 85 will place orders. Customers 86 to 100 will place NO orders!
    # This specifically satisfies query: "Find customers who have never placed an order"
    sql.append("-- ============================================================================")
    sql.append("-- SEED DATA: ORDERS (220 Records)")
    sql.append("-- Note: Customers 1-85 have orders, and Customers 86-100 have NO orders (for testing)")
    sql.append("-- ============================================================================")
    
    order_rows = []
    item_rows = []
    payment_rows = []
    
    order_statuses = ['completed', 'completed', 'completed', 'shipped', 'processing', 'cancelled', 'pending']
    item_id_counter = 1
    
    # Generate 220 orders across the past 14 months (e.g. Feb 2025 - Mar 2026)
    order_start_date = datetime(2025, 2, 1, 9, 30, 0)
    
    for order_id in range(1, 221):
        # Pick customer from 1 to 85 (frequently repeated top buyers)
        # Give top customers (1 to 10) more orders
        if order_id <= 60:
            cust_id = (order_id % 10) + 1  # Customer 1..10 get many orders (Top customers)
        else:
            cust_id = (order_id % 75) + 11 # Customers 11..85
            
        # Order date distribution across 400 days
        day_offset = int((order_id / 220.0) * 400) + random.randint(-2, 3)
        order_date = order_start_date + timedelta(days=max(0, day_offset), hours=random.randint(8, 20), minutes=random.randint(0, 59))
        status = random.choice(order_statuses)
        order_rows.append(f"({order_id}, {cust_id}, '{order_date.strftime('%Y-%m-%d %H:%M:%S')}', '{status}')")
        
        # Order items (1 to 4 items per order)
        num_items = random.choices([1, 2, 3, 4], weights=[45, 35, 15, 5])[0]
        selected_prods = random.sample(range(1, len(PRODUCTS_DATA) + 1), num_items)
        
        order_total = 0.0
        for pid in selected_prods:
            prod_name, prod_cat, prod_price, _ = PRODUCTS_DATA[pid - 1]
            qty = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
            item_price = prod_price
            order_total += item_price * qty
            item_rows.append(f"({item_id_counter}, {order_id}, {pid}, {qty}, {item_price:.2f})")
            item_id_counter += 1
            
        # Payment for this order
        pay_date = order_date + timedelta(minutes=random.randint(2, 45))
        if status == 'cancelled':
            pay_status = random.choice(['failed', 'refunded'])
        elif status == 'pending':
            pay_status = 'pending'
        else:
            pay_status = 'success'
            
        payment_rows.append(f"({order_id}, {order_id}, {order_total:.2f}, '{pay_status}', '{pay_date.strftime('%Y-%m-%d %H:%M:%S')}')")
        
    sql.append("INSERT INTO orders (id, customer_id, order_date, status) VALUES\n" + ",\n".join(order_rows) + ";\n")
    
    sql.append("-- ============================================================================")
    sql.append(f"-- SEED DATA: ORDER ITEMS ({len(item_rows)} Records)")
    sql.append("-- ============================================================================")
    sql.append("INSERT INTO order_items (id, order_id, product_id, quantity, price) VALUES\n" + ",\n".join(item_rows) + ";\n")
    
    sql.append("-- ============================================================================")
    sql.append("-- SEED DATA: PAYMENTS (220 Records)")
    sql.append("-- ============================================================================")
    sql.append("INSERT INTO payments (id, order_id, amount, payment_status, payment_date) VALUES\n" + ",\n".join(payment_rows) + ";\n")

    # Read-only user creation
    sql.append("-- ============================================================================")
    sql.append("-- DEDICATED READ-ONLY USER FOR SAFE QUERY EXECUTION")
    sql.append("-- ============================================================================")
    sql.append("CREATE USER IF NOT EXISTS 'analyst_readonly'@'%' IDENTIFIED BY 'ReadOnlyPass123!';")
    sql.append("GRANT SELECT ON ecommerce_db.* TO 'analyst_readonly'@'%';")
    sql.append("FLUSH PRIVILEGES;\n")

    return "\n".join(sql)

if __name__ == "__main__":
    content = generate_sql()
    with open(r"d:\AI_SQL_DATABASE\sample_database\ecommerce.sql", "w", encoding="utf-8") as f:
        f.write(content)
    print("Generated sample_database/ecommerce.sql successfully!")
