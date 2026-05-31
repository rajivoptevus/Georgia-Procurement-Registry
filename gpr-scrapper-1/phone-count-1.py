# Phone and Address 
#Working
# import json
# from typing import Any, Dict, List


# #file_path = r'C:\Scraping\gpr_complete_scraper\Phone-Details-1\3-April-2026-3.15AM\checkpoint_details_progress.json'
# file_path = r'C:\Scraping\gpr_complete_scraper\checkpoint_details_progress.json'

# def is_non_empty(value: Any) -> bool:
#     """Check if a value is non-empty after converting to string."""
#     return bool(str(value).strip()) if value is not None else False


# def load_records(path: str) -> List[Dict]:
#     """Load JSON and normalize into a list of records."""
#     with open(path, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     if isinstance(data, list):
#         return data
#     elif isinstance(data, dict):
#         # handle cases like {"data": [...]}
#         if "data" in data and isinstance(data["data"], list):
#             return data["data"]
#         return [data]

#     return []


# def count_json_fields(path: str):
#     contact_count = 0
#     phone_count = 0
#     fax_count = 0
#     address_count = 0

#     try:
#         records = load_records(path)
#         total_records = len(records)

#         for entry in records:
#             # Address (single field)
#             if is_non_empty(entry.get('address')):
#                 address_count += 1

#             # Contacts loop
#             for i in range(1, 4):  # 1 to 3
#                 if is_non_empty(entry.get(f'contact_name_{i}')):
#                     contact_count += 1

#                 if is_non_empty(entry.get(f'phone_{i}')):
#                     phone_count += 1

#                 if is_non_empty(entry.get(f'fax_{i}')):
#                     fax_count += 1

#         #Output
#         print(f"\nFile processed: {path}")
#         print(f"Total Records: {total_records}")
#         print("-" * 40)
#         print(f"Total Contact Names : {contact_count}")
#         print(f"Total Phone Numbers : {phone_count}")
#         print(f"Total Fax Numbers   : {fax_count}")
#         print(f"Total Addresses     : {address_count}")

#     except FileNotFoundError:
#         print("Error: File not found.")
#     except json.JSONDecodeError:
#         print("Error: Invalid JSON format.")
#     except Exception as e:
#         print(f"Unexpected error: {e}")


# if __name__ == "__main__":
#     count_json_fields(file_path)
    
# #### ALL Fields

# import json
# from collections import defaultdict
# from typing import Any, Dict, List


# file_path = r'C:\Scraping\gpr_complete_scraper\checkpoint_details_progress.json'


# def is_non_empty(value: Any) -> bool:
#     """Check if value is non-empty."""
#     if value is None:
#         return False
#     return bool(str(value).strip())


# def load_records(path: str) -> List[Dict]:
#     """Load JSON and normalize to list."""
#     with open(path, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     if isinstance(data, list):
#         return data
#     elif isinstance(data, dict):
#         if "data" in data and isinstance(data["data"], list):
#             return data["data"]
#         return [data]

#     return []


# def analyze_all_fields(path: str):
#     try:
#         records = load_records(path)
#         total_records = len(records)

#         field_stats = defaultdict(lambda: {
#             "non_empty": 0,
#             "empty": 0
#         })

#         # Analyze all fields
#         for entry in records:
#             for key in entry.keys():
#                 value = entry.get(key)

#                 if is_non_empty(value):
#                     field_stats[key]["non_empty"] += 1
#                 else:
#                     field_stats[key]["empty"] += 1

#         #Print report
#         print(f"\nFile: {path}")
#         print(f"Total Records: {total_records}")
#         print("=" * 60)

#         for field, stats in sorted(field_stats.items()):
#             non_empty = stats["non_empty"]
#             empty = stats["empty"]
#             total = non_empty + empty

#             fill_rate = (non_empty / total * 100) if total > 0 else 0

#             print(f"{field:25} | Filled: {non_empty:6} | Empty: {empty:6} | Fill %: {fill_rate:6.2f}")

#     except FileNotFoundError:
#         print("File not found")
#     except json.JSONDecodeError:
#         print("Invalid JSON")
#     except Exception as e:
#         print(f"Error: {e}")


# if __name__ == "__main__":
#     analyze_all_fields(file_path)


# import json
# from typing import Any, Dict, List

# file_path = r'C:\Scraping\gpr_complete_scraper\checkpoint_details_progress.json'


# def is_non_empty(value: Any) -> bool:
#     if value is None:
#         return False
#     return bool(str(value).strip())


# def load_records(path: str) -> List[Dict]:
#     with open(path, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     if isinstance(data, list):
#         return data
#     elif isinstance(data, dict):
#         if "data" in data and isinstance(data["data"], list):
#             return data["data"]
#         return [data]

#     return []


# def simple_summary(path: str):
#     records = load_records(path)

#     total_records = len(records)

#     contact_names = 0
#     phone_numbers = 0
#     fax_numbers = 0
#     addresses = 0

#     for entry in records:
#         if is_non_empty(entry.get("contact_name")):
#             contact_names += 1

#         if is_non_empty(entry.get("phone")):
#             phone_numbers += 1

#         if is_non_empty(entry.get("fax")):
#             fax_numbers += 1

#         if is_non_empty(entry.get("address")):
#             addresses += 1

#     # Clean Output
#     print(f"Total Records: {total_records}")
#     print("-" * 40)
#     print(f"Total Contact Names : {contact_names}")
#     print(f"Total Phone Numbers : {phone_numbers}")
#     print(f"Total Fax Numbers   : {fax_numbers}")
#     print(f"Total Addresses     : {addresses}")


# if __name__ == "__main__":
#     simple_summary(file_path)

### NGIP-Codes fields

import json
from typing import Any, Dict, List

file_path =r'C:\Users\User\Desktop\Original_Source_Websites\gpr-scrapper-1\checkpoint_details_progress.json' # current 
#file_path =r'C:\Users\User\Desktop\Original_Source_Websites\gpr-scrapper-1\checkpoint_list_all.json' # current 

def is_non_empty(value: Any) -> bool:
    return bool(str(value).strip()) if value is not None else False


def load_records(path: str) -> List[Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list):
            return data["data"]
        return [data]

    return []


def count_json_fields(path: str):
    contact_count = 0
    phone_count = 0
    fax_count = 0
    address_count = 0
    nigp_record_count = 0

    last_nigp_record = None  # track last record

    try:
        records = load_records(path)
        total_records = len(records)

        for entry in records:
            # Address
            if is_non_empty(entry.get('address')):
                address_count += 1

            # NIGP check
            nigp = entry.get('nigp_codes')

            has_nigp = False

            if isinstance(nigp, list):
                if any(is_non_empty(x) for x in nigp):
                    has_nigp = True
            elif is_non_empty(nigp):
                has_nigp = True

            if has_nigp:
                nigp_record_count += 1
                last_nigp_record = entry  # update last match

            # Contacts loop
            for i in range(1, 4):
                if is_non_empty(entry.get(f'contact_name_{i}')):
                    contact_count += 1

                if is_non_empty(entry.get(f'phone_{i}')):
                    phone_count += 1

                if is_non_empty(entry.get(f'fax_{i}')):
                    fax_count += 1

        # Output summary
        print(f"\nFile processed: {path}")
        print(f"Total Records: {total_records}")
        print("-" * 40)
        print(f"Total Contact Names : {contact_count}")
        print(f"Total Phone Numbers : {phone_count}")
        print(f"Total Fax Numbers   : {fax_count}")
        print(f"Total Addresses     : {address_count}")
        print(f"Records with NIGP   : {nigp_record_count}")

        # Print last NIGP record
        if last_nigp_record:
            print("\nLast record with NIGP codes:\n")
            print(json.dumps(last_nigp_record, indent=2))
        else:
            print("\nNo records found with NIGP codes.")

    except FileNotFoundError:
        print("Error: File not found.")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format.")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    count_json_fields(file_path)