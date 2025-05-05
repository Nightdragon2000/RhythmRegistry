# Change from package import to direct import
from wikipedia_scraper import add_portraits_and_roles_to_database, add_relationships_to_database, process_date, generate_date_range
import sys

# GLOBAL
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
ROLES = ["actor", "producer"]

def main():
    """
    Main function to process dates and extract person information.
    Processes one day at a time and adds to database immediately.
    
    Command line arguments:
    sys.argv[1]: start_date (format: dd-mm)
    sys.argv[2]: end_date (format: dd-mm)
    sys.argv[3]: section_ids (comma-separated, e.g., "2.3,3.3")
    """
    # Get date parameters from command line arguments
    if len(sys.argv) >= 3:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
    else:
        print("Error: Missing date parameters.")
        return
    
    # Get section IDs from command line arguments
    if len(sys.argv) >= 4:
        section_ids = sys.argv[3].split(',')
    else:
        # Default to both births and deaths
        section_ids = ['2.3', '3.3']
    
    print(f"Processing dates from {start_date} to {end_date}")
    print(f"Processing sections: {', '.join(section_ids)}")
    
    dates_to_process = generate_date_range(start_date, end_date)
    
    for date_str in dates_to_process:
        print(f"\n{'='*50}")
        print(f"PROCESSING DATE: {date_str}")
        print(f"{'='*50}")
        
        # Process a single date - pass section_ids parameter
        people = process_date(date_str, WIKIPEDIA_API_URL, ROLES, section_ids)
        
        # Filter out people with missing required data
        valid_people = []
        for person in people:
            if (person.get('first_name') and 
                person.get('last_name') and 
                person.get('date_of_birth') and 
                person.get('roles') and 
                person.get('image_path')):
                valid_people.append(person)
            else:
                print(f"Skipping portrait with incomplete data: {person.get('first_name', 'Unknown')} {person.get('last_name', 'Unknown')}")
        
        # Extract roles for this day's people
        day_roles = set()
        for person in valid_people:
            if 'roles' in person and person['roles']:
                day_roles.update(person['roles'])
        
        # Only add to database if we have valid people
        if valid_people:
            add_portraits_and_roles_to_database(list(day_roles), valid_people)
            add_relationships_to_database(valid_people)
    
    print(f"\n{'='*50}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

