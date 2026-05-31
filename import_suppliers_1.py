import json
import psycopg2
from psycopg2 import extras
from datetime import datetime
import os
import sys

# ==============================
# CONFIG
# ==============================
DB_PARAMS = {
    "host": "rfpwyer-postgresql.postgres.database.azure.com",
    "port": "5432",
    "database": "masterwyber",
    "user": "rfppgadmin",
    "password": "H@Sh1CoR3!",
    "options": "-c timezone=UTC"
}

SOURCE_URL = "https://ssl.doas.state.ga.us/gpr/loadSupplierSearch"


# ==============================
# HELPERS
# ==============================
def create_connection():
    try:
        return psycopg2.connect(**DB_PARAMS)
    except Exception as e:
        print(f"DB Connection Error: {e}")
        sys.exit(1)


def convert_to_boolean(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.upper() == 'Y'
    return False


def clean(value):
    return None if value == "" else value


def transform(record):
    return {
        "supplier_id": record.get("supplier_id", "")[:50],
        "company": record.get("company", ""),
        "city": clean(record.get("city", "")),
        "state": clean(record.get("state", "")),
        "ga_resident": convert_to_boolean(record.get("ga_resident", "N")),
        "small_business": convert_to_boolean(record.get("small_business", "N")),
        "owner_ethnicity": clean(record.get("owner_ethnicity", "")),
        "company_status": clean(record.get("company_status", "")),
        "company_class": clean(record.get("company_class", "")),
        "address": clean(record.get("address", "")),
        "contact_name_1": clean(record.get("contact_name_1", "")),
        "phone_1": clean(record.get("phone_1", "")),
        "fax_1": clean(record.get("fax_1", "")),
        "contact_name_2": clean(record.get("contact_name_2", "")),
        "phone_2": clean(record.get("phone_2", "")),
        "fax_2": clean(record.get("fax_2", "")),
        "contact_name_3": clean(record.get("contact_name_3", "")),
        "phone_3": clean(record.get("phone_3", "")),
        "fax_3": clean(record.get("fax_3", "")),
        "nigp_codes": clean(record.get("nigp_codes", "")),
        "nigp_descriptions": clean(record.get("nigp_descriptions", "")),
        "nigp_count": record.get("nigp_count", 0),
        "created_on": datetime.now(),
        "created_by_id": None,
        "modified_on": None,
        "modified_by_id": None,
        "source_url": record.get("source_url") or SOURCE_URL
    }


def deduplicate_records(records):
    """Keep only the latest record for each supplier_id"""
    unique_records = {}
    
    for record in records:
        supplier_id = record["supplier_id"]
        
        # If this supplier_id already exists, keep the record
        # (you can add logic here to determine which record to keep)
        # For now, later records overwrite earlier ones
        unique_records[supplier_id] = record
    
    print(f"Deduplicated from {len(records)} to {len(unique_records)} records")
    return list(unique_records.values())


# ==============================
# INSERT FUNCTION
# ==============================
def insert_batch(conn, records, batch_size=1000):
    cursor = conn.cursor()

    query = """
    INSERT INTO suppliers_ga (
        supplier_id, company, city, state, ga_resident, small_business,
        owner_ethnicity, company_status, company_class, address,
        contact_name_1, phone_1, fax_1, contact_name_2, phone_2, fax_2,
        contact_name_3, phone_3, fax_3, nigp_codes, nigp_descriptions,
        nigp_count, created_on, created_by_id, modified_on, modified_by_id,
        source_url
    ) VALUES %s
    ON CONFLICT (supplier_id) DO UPDATE SET
        company = EXCLUDED.company,
        city = EXCLUDED.city,
        state = EXCLUDED.state,
        ga_resident = EXCLUDED.ga_resident,
        small_business = EXCLUDED.small_business,
        owner_ethnicity = EXCLUDED.owner_ethnicity,
        company_status = EXCLUDED.company_status,
        company_class = EXCLUDED.company_class,
        address = EXCLUDED.address,
        contact_name_1 = EXCLUDED.contact_name_1,
        phone_1 = EXCLUDED.phone_1,
        fax_1 = EXCLUDED.fax_1,
        contact_name_2 = EXCLUDED.contact_name_2,
        phone_2 = EXCLUDED.phone_2,
        fax_2 = EXCLUDED.fax_2,
        contact_name_3 = EXCLUDED.contact_name_3,
        phone_3 = EXCLUDED.phone_3,
        fax_3 = EXCLUDED.fax_3,
        nigp_codes = EXCLUDED.nigp_codes,
        nigp_descriptions = EXCLUDED.nigp_descriptions,
        nigp_count = EXCLUDED.nigp_count,
        modified_on = NOW(),
        modified_by_id = EXCLUDED.created_by_id,
        source_url = EXCLUDED.source_url
    """

    total = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        
        # Check for duplicates within the batch
        batch_supplier_ids = [r["supplier_id"] for r in batch]
        if len(batch_supplier_ids) != len(set(batch_supplier_ids)):
            print(f"WARNING: Batch {i//batch_size + 1} has duplicates within it!")
            # Further deduplicate the batch
            batch = deduplicate_records(batch)
        
        values = [tuple(r.values()) for r in batch]

        try:
            extras.execute_values(cursor, query, values)
            total += len(batch)
            print(f"Inserted: {total}")
        except Exception as e:
            print(f"Error in batch {i//batch_size + 1}: {e}")
            # Fall back to one-by-one insertion for this batch
            print("Falling back to individual inserts for this batch...")
            for record in batch:
                try:
                    # Single insert statement
                    single_query = query.replace("VALUES %s", "VALUES %s")
                    extras.execute_values(cursor, single_query, [tuple(record.values())])
                    total += 1
                except Exception as inner_e:
                    print(f"Failed to insert supplier {record['supplier_id']}: {inner_e}")
            conn.commit()
            print(f"Progress after fallback: {total}")

    conn.commit()
    cursor.close()


# ==============================
# MAIN
# ==============================
def main():
    #json_path = r"C:\Scraping\gpr_complete_scraper\checkpoint_details_progress.json"
    #json_path = r"C:\Users\User\Desktop\Original_Source_Websites\gpr-scrapper\checkpoint_details_progress 2.json"
    #json_path = r"C:\Users\User\Desktop\Original_Source_Websites\gpr-scrapper\checkpoint_details_progress.json"
    json_path = r"C:\Users\User\Desktop\Original_Source_Websites\gpr-scrapper-1\checkpoint_details_progress.json"
    if not os.path.exists(json_path):
        print("JSON file not found")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    print(f"Loaded {len(raw)} records")

    transformed = [transform(r) for r in raw]
    
    # Remove duplicates from the entire dataset first
    unique_records = deduplicate_records(transformed)

    conn = create_connection()

    try:
        insert_batch(conn, unique_records)
        print("Done")

    finally:
        conn.close()


if __name__ == "__main__":
    main()