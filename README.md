Overview:-
There are two scripts which work together as a complete pipeline for scraping Georgia Procurement Registry (GPR) supplier data and loading it into a PostgreSQL database.

I.phase2_only.py - Web Scraper
Purpose:-
Scrapes all approx. 32,641 suppliers from the Georgia GPR website and extracts detailed information.
Key Components:-
solve_captcha():         	 	Handles reCAPTCHA challenges using seleniumbase's 
                          		  	UC (Undetected Chrome) mode
wait_for_table():	  	Waits for the DataTable to load with supplier rows
get_ids_from_datatable(): 	Extracts supplier IDs from JavaScript DataTable API
parse_list_page():	  	Parses the search results table for supplier list data
click_next_page():        		Navigates through paginated search results
parse_detail_page():	  	Extracts full supplier details 
                          			(contacts, NIGP codes, addresses, ethnicity)
save_final():             		Saves results to CSV and JSON files
What It Scrapes:-
•	List page: Supplier ID, company name, city, state, GA resident status, 
small business status
•	Detail page: Owner ethnicity, company status/class, address, 
up to 3 contacts, NIGP codes
Checkpoint System:-
•	checkpoint_list_all.json - Saves all supplier IDs collected (prevents re-scraping list)
•	checkpoint_details_progress.json - Saves detail page results incrementally

II .import_suppliers_1.py - Database Importer
Purpose:-
Loads the scraped JSON data into an Azure PostgreSQL database with upsert logic.
Key Functions
create_connection():	Establishes PostgreSQL connection to Azure
convert_to_boolean():	Converts 'Y'/'N' strings to Python booleans
clean():			Converts empty strings to None (NULL in DB)
transform():		Maps JSON fields to database columns
deduplicate_records():	Removes duplicate supplier_id entries (keeps latest)
insert_batch():		Bulk inserts with ON CONFLICT for upsert


Database Table Structure
Target table: suppliers_ga
