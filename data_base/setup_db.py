# setup_db.py
import sqlite3
import random

def init_mock_db():
    conn = sqlite3.connect("company_sales.db")
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS sales")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            product_id INTEGER,
            product_name TEXT,
            category TEXT,
            revenue REAL,
            units_sold INTEGER
        )
    """)

    products = {
        'Infrastructure': [
            ('Cloud Server Alpha', 10000, 30000, 10, 60),
            ('Cloud Server Beta', 12000, 28000, 8, 50),
            ('Storage Bucket Standard', 5000, 15000, 50, 200),
            ('Storage Bucket Premium', 8000, 20000, 30, 150),
            ('Load Balancer Pro', 3000, 9000, 20, 80),
            ('VPN Gateway', 4000, 12000, 15, 70),
            ('CDN Accelerator', 6000, 18000, 25, 100),
            ('Firewall Shield', 7000, 16000, 20, 90),
        ],
        'Data Analytics': [
            ('Data Pipeline Pro', 18000, 35000, 5, 20),
            ('Analytics Dashboard', 9000, 22000, 10, 40),
            ('Real-Time Stream Engine', 15000, 40000, 6, 25),
            ('Data Warehouse Lite', 20000, 50000, 4, 18),
            ('ETL Toolkit', 8000, 18000, 12, 45),
            ('BI Connector Suite', 11000, 28000, 8, 35),
            ('Query Optimizer', 7000, 16000, 15, 55),
        ],
        'AI/ML Services': [
            ('ML Vision API', 30000, 60000, 40, 120),
            ('NLP Inference Engine', 25000, 55000, 35, 100),
            ('AutoML Platform', 40000, 80000, 20, 70),
            ('Recommendation Engine', 22000, 48000, 30, 90),
            ('Fraud Detection API', 28000, 58000, 25, 80),
            ('Speech-to-Text Pro', 18000, 38000, 40, 110),
            ('Predictive Analytics SDK', 35000, 70000, 15, 60),
        ],
        'Security': [
            ('Identity Manager', 12000, 25000, 20, 75),
            ('Zero Trust Gateway', 15000, 32000, 15, 60),
            ('Secret Vault Pro', 9000, 20000, 25, 85),
            ('Compliance Scanner', 7000, 16000, 30, 90),
            ('SIEM Lite', 18000, 40000, 10, 45),
            ('DDoS Protection Shield', 14000, 30000, 18, 70),
        ],
        'DevOps': [
            ('CI/CD Pipeline Suite', 10000, 22000, 20, 80),
            ('Container Registry Pro', 6000, 14000, 30, 100),
            ('Kubernetes Operator', 12000, 26000, 15, 60),
            ('Log Aggregator', 5000, 12000, 40, 120),
            ('Monitoring Stack', 8000, 18000, 25, 90),
            ('Artifact Manager', 4000, 10000, 35, 110),
        ],
    }

    random.seed(42)
    mock_data = []
    product_id = 101

    category_list = list(products.keys())
    for i in range(150):
        category = random.choice(category_list)
        name, rev_min, rev_max, units_min, units_max = random.choice(products[category])
        revenue = round(random.uniform(rev_min, rev_max), 2)
        units_sold = random.randint(units_min, units_max)
        mock_data.append((product_id + i, name, category, revenue, units_sold))

    cursor.executemany("INSERT INTO sales VALUES (?, ?, ?, ?, ?)", mock_data)
    conn.commit()
    conn.close()
    print(f"Mock database 'company_sales.db' initialized with {len(mock_data)} rows!")

if __name__ == "__main__":
    init_mock_db()