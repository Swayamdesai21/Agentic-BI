"""
SQLite database setup with sample e-commerce business data.
Auto-seeds realistic data on first run for immediate demo.
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta
from pathlib import Path


DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/business.db")


def get_db() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def execute_query(sql: str) -> tuple[list[dict], list[str]]:
    """Execute a SQL query and return results as list of dicts + column names."""
    conn = get_db()
    try:
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return rows, columns
    except Exception as e:
        raise e
    finally:
        conn.close()


def validate_sql(sql: str) -> tuple[bool, str]:
    """Validate SQL syntax using EXPLAIN."""
    conn = get_db()
    try:
        conn.execute(f"EXPLAIN {sql}")
        return True, "Valid SQL"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_schema_info() -> list[dict]:
    """Get full database schema info for RAG indexing."""
    conn = get_db()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()

    schema_info = []
    for table in tables:
        table_name = table[0]
        columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

        col_details = []
        for col in columns:
            col_details.append({
                "name": col[1],
                "type": col[2],
                "nullable": not col[3],
                "primary_key": bool(col[5])
            })

        # Get sample data
        sample_rows = conn.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
        sample_data = []
        if sample_rows:
            col_names = [c[1] for c in columns]
            for row in sample_rows:
                sample_data.append(dict(zip(col_names, row)))

        schema_info.append({
            "table_name": table_name,
            "columns": col_details,
            "row_count": row_count,
            "sample_data": sample_data
        })

    conn.close()
    return schema_info


def init_db():
    """Initialize database and seed with sample e-commerce data."""
    Path(os.path.dirname(DATABASE_PATH)).mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Check if already seeded
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='orders'"
    ).fetchall()
    if tables:
        conn.close()
        return

    print("🌱 Seeding database with sample e-commerce data...")

    # ── Create Tables ───────────────────────────────────────────────

    cursor.executescript("""
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER REFERENCES categories(id),
            price REAL NOT NULL,
            cost REAL NOT NULL,
            stock_quantity INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            city TEXT,
            country TEXT DEFAULT 'US',
            segment TEXT DEFAULT 'Consumer',
            joined_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER REFERENCES customers(id),
            order_date TEXT NOT NULL,
            status TEXT DEFAULT 'completed',
            total_amount REAL DEFAULT 0,
            shipping_cost REAL DEFAULT 0,
            region TEXT
        );

        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER REFERENCES orders(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            discount REAL DEFAULT 0
        );
    """)

    # ── Seed Categories ─────────────────────────────────────────────

    categories = [
        ("Electronics", "Phones, laptops, tablets, accessories"),
        ("Clothing", "Apparel, shoes, fashion accessories"),
        ("Home & Kitchen", "Furniture, appliances, decor"),
        ("Books", "Physical and digital books"),
        ("Sports & Outdoors", "Fitness equipment, outdoor gear"),
        ("Beauty & Health", "Skincare, supplements, wellness"),
    ]
    cursor.executemany("INSERT INTO categories (name, description) VALUES (?, ?)", categories)

    # ── Seed Products ───────────────────────────────────────────────

    products_data = [
        # Electronics
        ("iPhone 15 Pro", 1, 999.99, 650.00, 150),
        ("MacBook Air M3", 1, 1299.99, 850.00, 80),
        ("AirPods Pro", 1, 249.99, 120.00, 300),
        ("Samsung Galaxy S24", 1, 849.99, 550.00, 120),
        ("iPad Air", 1, 599.99, 380.00, 100),
        ("Sony WH-1000XM5", 1, 349.99, 180.00, 200),
        # Clothing
        ("Nike Air Max 90", 2, 129.99, 55.00, 400),
        ("Levi's 501 Jeans", 2, 69.99, 25.00, 500),
        ("North Face Jacket", 2, 199.99, 80.00, 150),
        ("Adidas Ultraboost", 2, 189.99, 70.00, 250),
        # Home & Kitchen
        ("Dyson V15 Vacuum", 3, 749.99, 350.00, 60),
        ("Instant Pot Duo", 3, 89.99, 35.00, 300),
        ("KitchenAid Mixer", 3, 449.99, 200.00, 80),
        ("Philips Air Fryer", 3, 199.99, 85.00, 180),
        # Books
        ("Atomic Habits", 4, 16.99, 5.00, 800),
        ("The Pragmatic Programmer", 4, 49.99, 15.00, 200),
        ("Designing Data-Intensive Apps", 4, 44.99, 14.00, 150),
        # Sports
        ("Peloton Bike", 5, 1445.00, 800.00, 30),
        ("Yoga Mat Premium", 5, 69.99, 15.00, 500),
        ("Fitbit Charge 6", 5, 159.99, 70.00, 250),
        # Beauty
        ("CeraVe Moisturizer", 6, 18.99, 6.00, 600),
        ("Vitamin D3 Supplements", 6, 24.99, 8.00, 400),
        ("Olaplex Hair Kit", 6, 99.99, 35.00, 200),
    ]
    cursor.executemany(
        "INSERT INTO products (name, category_id, price, cost, stock_quantity) VALUES (?, ?, ?, ?, ?)",
        products_data
    )

    # ── Seed Customers ──────────────────────────────────────────────

    cities = [
        ("New York", "US"), ("Los Angeles", "US"), ("Chicago", "US"),
        ("Houston", "US"), ("San Francisco", "US"), ("Seattle", "US"),
        ("Austin", "US"), ("Denver", "US"), ("Miami", "US"), ("Boston", "US"),
        ("Portland", "US"), ("Atlanta", "US"), ("Dallas", "US"),
        ("London", "UK"), ("Toronto", "CA"),
    ]
    segments = ["Consumer", "Corporate", "Small Business"]
    first_names = ["Emma", "Liam", "Olivia", "Noah", "Ava", "James", "Sophia", "William",
                    "Isabella", "Oliver", "Mia", "Benjamin", "Charlotte", "Elijah", "Amelia",
                    "Lucas", "Harper", "Mason", "Evelyn", "Logan", "Luna", "Alexander",
                    "Chloe", "Ethan", "Penelope", "Daniel", "Layla", "Henry", "Riley", "Sebastian"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
                  "Davis", "Rodriguez", "Martinez", "Wilson", "Anderson", "Taylor", "Thomas",
                  "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson"]

    random.seed(42)  # For reproducibility

    customers_data = []
    for i in range(100):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        city, country = random.choice(cities)
        segment = random.choice(segments)
        joined = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 700))
        customers_data.append((
            f"{fname} {lname}",
            f"{fname.lower()}.{lname.lower()}{i}@email.com",
            city, country, segment, joined.strftime("%Y-%m-%d")
        ))
    cursor.executemany(
        "INSERT INTO customers (name, email, city, country, segment, joined_at) VALUES (?, ?, ?, ?, ?, ?)",
        customers_data
    )

    # ── Seed Orders & Items ─────────────────────────────────────────

    regions = ["North", "South", "East", "West"]
    statuses = ["completed", "completed", "completed", "completed", "shipped", "processing", "cancelled"]

    for _ in range(500):
        customer_id = random.randint(1, 100)
        order_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 450))
        status = random.choice(statuses)
        region = random.choice(regions)
        shipping = round(random.uniform(0, 25), 2)

        cursor.execute(
            "INSERT INTO orders (customer_id, order_date, status, shipping_cost, region) VALUES (?, ?, ?, ?, ?)",
            (customer_id, order_date.strftime("%Y-%m-%d"), status, shipping, region)
        )
        order_id = cursor.lastrowid

        # 1-4 items per order
        total = 0
        for _ in range(random.randint(1, 4)):
            product_id = random.randint(1, len(products_data))
            quantity = random.randint(1, 3)
            price = products_data[product_id - 1][2]
            discount = random.choice([0, 0, 0, 0.05, 0.1, 0.15, 0.2])
            unit_price = round(price * (1 - discount), 2)
            total += unit_price * quantity

            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount) VALUES (?, ?, ?, ?, ?)",
                (order_id, product_id, quantity, unit_price, discount)
            )

        cursor.execute("UPDATE orders SET total_amount = ? WHERE id = ?", (round(total, 2), order_id))

    conn.commit()
    conn.close()
    print(f"✅ Database seeded: 100 customers, 500 orders, {len(products_data)} products")


if __name__ == "__main__":
    init_db()
    info = get_schema_info()
    for table in info:
        print(f"\n📊 {table['table_name']} ({table['row_count']} rows)")
        for col in table['columns']:
            pk = " 🔑" if col['primary_key'] else ""
            print(f"   {col['name']}: {col['type']}{pk}")
