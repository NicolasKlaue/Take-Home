import sqlite3
import random
from faker import Faker
from datetime import timedelta

DB_PATH = "Take-home.db"
NUM_RECORDS = 100

fake = Faker()

EQUIPMENT_TYPES = ["Dry Van", "Reefer", "Flatbed", "Step Deck"]
COMMODITIES = ["Electronics", "Food", "Furniture", "Steel", "Clothing", "Machinery"]

def random_datetime_pair():
    pickup = fake.date_time_between(start_date="-10d", end_date="now")
    delivery = pickup + timedelta(hours=random.randint(5, 72))
    return pickup, delivery

def generate_load(load_id):
    pickup, delivery = random_datetime_pair()

    return (
        load_id,
        fake.city(),
        fake.city(),
        pickup.strftime("%Y-%m-%d %H:%M:%S"),
        delivery.strftime("%Y-%m-%d %H:%M:%S"),
        random.choice(EQUIPMENT_TYPES),
        round(random.uniform(300, 5000), 2),
        fake.sentence(nb_words=6),
        round(random.uniform(1000, 40000), 2),
        random.choice(COMMODITIES),
        random.randint(1, 50),
        round(random.uniform(50, 3000), 2),
        f"{random.randint(50, 200)}x{random.randint(50, 200)}x{random.randint(50, 200)} cm"
    )

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    loads = [generate_load(f"L{str(i).zfill(5)}") for i in range(1, NUM_RECORDS + 1)]

    cursor.executemany("""
        INSERT INTO loads (
            load_id,
            origin,
            destination,
            pickup_datetime,
            delivery_datetime,
            equipment_type,
            loadboard_rate,
            notes,
            weight,
            commodity_type,
            num_of_pieces,
            miles,
            dimensions
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, loads)

    conn.commit()
    conn.close()

    print(f"Inserted {NUM_RECORDS} fake records into the database.")

if __name__ == "__main__":
    main()