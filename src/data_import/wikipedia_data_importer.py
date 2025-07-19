from wikipedia_scraper import add_portraits_and_roles_to_database, add_relationships_to_database, process_date, generate_date_range
import sys
import time

# Constants
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
ROLES = ["actor", "producer"]

def main():
    # Parse start and end dates from command-line arguments
    if len(sys.argv) >= 3:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
    else:
        print("Error: Please provide both start and end dates (format: dd-mm).")
        return

    # Parse section IDs
    if len(sys.argv) >= 4:
        section_ids = sys.argv[3].split(',')
    else:
        section_ids = ['2.3', '3.3']  # Default sections

    # Convert section IDs to readable names
    readable_sections = []
    for section in section_ids:
        if section == '2.3':
            readable_sections.append('births')
        elif section == '3.3':
            readable_sections.append('deaths')
        else:
            readable_sections.append(section)

    # Display processing summary
    if start_date == end_date:
        print("Processing date:", start_date)
    else:
        print(f"Processing range: {start_date} to {end_date}")
    print("Sections:", ", ".join(readable_sections))

    dates = generate_date_range(start_date, end_date)

    for date in dates:
        print("\n" + "="*50)
        print("PROCESSING DATE:", date)
        print("="*50)

        people = process_date(date, WIKIPEDIA_API_URL, ROLES, section_ids)

        # Filter entries with all required fields
        valid_people = []
        for person in people:
            if (person.get("first_name") and
                person.get("last_name") and
                person.get("date_of_birth") and
                person.get("roles") and
                person.get("image_path")):
                valid_people.append(person)
            else:
                fname = person.get("first_name", "Unknown")
                lname = person.get("last_name", "Unknown")
                print("Skipping incomplete entry:", fname, lname)

        # Collect unique roles from valid entries
        roles_today = set()
        for p in valid_people:
            if "roles" in p:
                roles_today.update(p["roles"])

        # Insert data into the database
        if valid_people:
            add_portraits_and_roles_to_database(list(roles_today), valid_people)
            add_relationships_to_database(valid_people)

    print("\n" + "="*50)
    print("PROCESSING COMPLETE")
    print("="*50)

if __name__ == "__main__":
    main()
