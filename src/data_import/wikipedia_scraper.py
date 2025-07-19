import requests
from bs4 import BeautifulSoup
import re
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import sys
import os
import time

# Add src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RhythmRegistryApp.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Use the imported config to create the DB URI
DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

USER_AGENT = "RhythmRegistryBot/1.0"
DEFAULT_HEADERS = {"User-Agent": USER_AGENT}

# ---------------- HELPER FUNCTION ---------------- #
def get_data(url, params=None, max_retries=5, base_delay=1.0):
    """
    Wrapper for requests.get with retry and exponential backoff on 429 errors.
    """
    for attempt in range(max_retries):
        response = requests.get(url, params=params, headers=DEFAULT_HEADERS)
        
        if response.status_code == 429:
            wait = base_delay * (2 ** attempt)
            print(f"[429] Rate limited. Waiting {wait:.1f} seconds before retry...")
            time.sleep(wait)
        else:
            response.raise_for_status()
            return response

    raise Exception(f"Too many retries for {url}")

# ---------------- WIKIPEDIA API FUNCTIONS ---------------- #

def fetch_wikipedia_sections(page_title, wikipedia_api_url):
    """
    Fetches the sections of a Wikipedia page.
    Returns a list of section titles.
    """
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "sections",
        "format": "json"
    }
    response = get_data(wikipedia_api_url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_section_content(page_title, section_id, wikipedia_api_url):
    """
    Fetches the content of a specific section of a Wikipedia page by section ID.
    Returns a dictionary.
    """
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "text",
        "section": section_id,
        "format": "json",
    }
    response = get_data(wikipedia_api_url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_wikipedia_summary(page_title, wikipedia_api_url):
    """
    Fetches the summary of a Wikipedia page.
    Returns string.
    """    
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'extracts',
        'exintro': True,
        'explaintext': True,
        'titles': page_title
    }
    
    response = get_data(wikipedia_api_url, params=params)
    
    if response.status_code != 200:
        print(f"Error: Status code {response.status_code} for page: {page_title}")
        return None
    
    data = response.json()
    
    if 'query' in data and 'pages' in data['query']:
        page_id = next(iter(data['query']['pages']))
        
        if 'extract' in data['query']['pages'][page_id]:
            extract = data['query']['pages'][page_id]['extract']
            return extract
        else:
            return None
    else:
        return None

# ----------------- DATE HANDLING FUNCTIONS -----------------#

def convert_to_wiki_format(date_str):
    """
    Converts a date string in dd-mm format to Month_day format for Wikipedia page titles.
    Always uses 2020 (leap year) to handle February 29.
    """
    from datetime import datetime
    
    date_parts = date_str.split('-')
    day = int(date_parts[0])
    month = int(date_parts[1])
    date_obj = datetime(2020, month, day) 
    month_name = date_obj.strftime("%B")
    return f"{month_name}_{day}"

def format_date(date_str, person_name, date_type):
    """
    Format date string to datetime.date object.
    """
    if not date_str:
        return None
        
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        try:
            # Try alternative format
            return datetime.strptime(date_str, '%Y/%m/%d').date()
        except ValueError:
            print(f"Invalid {date_type} date format for {person_name}: {date_str}")
            return None

def generate_date_range(start_date, end_date):
    """
    Generate a list of dates between start_date and end_date.
    """
    # Convert to datetime objects for comparison
    start_date_obj = datetime.strptime(start_date, "%d-%m").replace(year=2020)
    end_date_obj = datetime.strptime(end_date, "%d-%m").replace(year=2020)
    
    dates = []
    current_date = start_date_obj
    
    while current_date <= end_date_obj:
        dates.append(current_date.strftime("%d-%m"))
        current_date += timedelta(days=1)
    
    return dates

# --------------------- DATA EXTRACTION FUNCTIONS -------------------- #

def extract_person_info_from_infobox(short_url, fullname):
    """
    Extracts first name, last name, image path, birth date, death date, and roles from the wikitext.
    Returns a dictionary containing the extracted information.
    """
    url = f"https://en.wikipedia.org{short_url}"
    print(f"Processing {url}")
    
    response = get_data(url)
    if response.status_code != 200:
        print(f"Error: Status code {response.status_code}")
        return None 
 
    soup = BeautifulSoup(response.text, 'html.parser')

    person_info = {
        "first_name": "",
        "last_name": "",
        "image_path": "",
        "date_of_birth": "",
        "date_of_death": "",
        "roles": [],
        "short_url": short_url  
    }

    infobox_table = soup.find('table', class_=['infobox', 'vcard', 'biography'])
    if not infobox_table:
        # Try to find infobox with a more general approach
        for table in soup.find_all('table'):
            if table.has_attr('class'):
                for class_name in table['class']:
                    if 'infobox' in class_name.lower():
                        infobox_table = table
                        break
                if infobox_table:
                    break
    
    # Extract name regardless of whether infobox was found
    name_parts = fullname.split()
    if len(name_parts) > 1:
        person_info["first_name"] = ' '.join(name_parts[:-1])
        person_info["last_name"] = name_parts[-1]
    else:
        person_info["first_name"] = name_parts[0] if name_parts else ""
        person_info["last_name"] = ""

    # Only proceed with infobox extraction if infobox was found
    if infobox_table:
        # Extract birth date
        date_of_birth_element = None
        for th in infobox_table.find_all('th'):
            if th.string and 'Born' in th.string:
                date_of_birth_element = th
                break
            
        if date_of_birth_element:
            date_of_birth_td = date_of_birth_element.find_next_sibling('td')
            if date_of_birth_td:
                bday_span = date_of_birth_td.find('span', class_='bday')
                if bday_span:
                    person_info["date_of_birth"] = bday_span.get_text(strip=True)

        # Extract death date
        date_of_death_element = None
        for th in infobox_table.find_all('th'):
            if th.string and 'Died' in th.string:
                date_of_death_element = th
                break
            
        if date_of_death_element:
            date_of_death_td = date_of_death_element.find_next_sibling('td')
            if date_of_death_td:
                hidden_span = date_of_death_td.find('span', style='display:none')
                if hidden_span:
                    person_info["date_of_death"] = hidden_span.get_text(strip=True).strip('()')
                else:
                    person_info["date_of_death"] = None
        else:
            person_info["date_of_death"] = None

        # Extract image
        main_image = infobox_table.find('img')
        if main_image:
            person_info["image_path"] = main_image['src']
        else:
            person_info["image_path"] = None
            
        # Extract roles/occupation
        person_info["roles"] = extract_roles_from_infobox(infobox_table)
    else:
        # Set default values when no infobox is found
        person_info["roles"] = ["Unknown"]

    return person_info

def extract_roles_from_infobox(infobox_table):
    """
    Extracts roles/occupations from the infobox table.
    Returns a list of roles.
    """
    roles = []
    
    # Find occupation element
    occupation_element = None
    for th in infobox_table.find_all('th'):
        if th.string and any(term in th.string for term in ['Occupation', 'Profession', 'Occupations']):
            occupation_element = th
            break
                
    if occupation_element:
        occupation_td = occupation_element.find_next_sibling('td')
        if occupation_td:
            hlist = occupation_td.find(class_='hlist')
            if hlist:
                # Extract all list items 
                list_items = hlist.find_all('li')
                if list_items:
                    for item in list_items:
                        role_text = item.get_text(strip=True)
                        if role_text and role_text not in roles:
                            roles.append(role_text)
            
            if not roles:
                role_elements = occupation_td.find_all(class_='role')
                if role_elements:
                    for role in role_elements:
                        role_text = role.get_text(strip=True)
                        if role_text and role_text not in roles:
                            roles.append(role_text)
            
            # If still no roles found, extract all text and try to split it
            if not roles:
                occupation_text = occupation_td.get_text(strip=True)
                # Check for common separators
                for separator in [',', ';', '•', '·']:
                    if separator in occupation_text:
                        split_roles = [role.strip() for role in occupation_text.split(separator)]
                        for role in split_roles:
                            if role and role not in roles:
                                roles.append(role)
                        break
                else:  
                    # Split by capital letters  like "ActorProducer"
                    if any(c.isupper() for c in occupation_text[1:]):
                        import re
                        # Split by capital letters but keep them
                        split_roles = re.findall('[A-Z][^A-Z]*', occupation_text)
                        for role in split_roles:
                            if role and role not in roles:
                                roles.append(role)
                    else:
                        # Just add the whole text as one role
                        if occupation_text and occupation_text not in roles:
                            roles.append(occupation_text)
    
    return roles

def extract_short_bio(li_text):
    """
    Extract the short bio from the list item text.
    """
    if ',' in li_text:
        start_index = li_text.index(',') + 1
        end_index = li_text.find('(') if '(' in li_text else li_text.find('[')
        if end_index == -1:
            end_index = len(li_text)
        return li_text[start_index:end_index].strip()
    return li_text

# ---------------------- DATA PROCESSING FUNCTIONS ----------------------- #

def process_date(date_str, wikipedia_api_url, roles, section_ids=None):
    """
    Process a single date and extract person information.
    Returns a list of person entries.
    
    Args:
        date_str (str): Date string in dd-mm format
        wikipedia_api_url (str): Wikipedia API URL
        roles (list): List of roles to filter by
        section_ids (list): List of section IDs to process. Default is ['2.3'] (Births)
    """
    page_title = convert_to_wiki_format(date_str)
    
    sections = fetch_wikipedia_sections(page_title, wikipedia_api_url)
    
    # Use provided section IDs or default to '2.3' (Births)
    if section_ids is None:
        section_ids = ['2.3']
    
    filtered_sections = [section['index'] for section in sections['parse']['sections'] 
                         if section['number'] in section_ids]
    
    filtered_li = []  
    
    for section_id in filtered_sections:
        section_content = fetch_section_content(page_title, section_id, wikipedia_api_url)
        html_content = section_content['parse']['text']['*']
        
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        li_items = soup.find_all('li')
        
        for li in li_items:
            li_text = li.get_text()
            short_bio = extract_short_bio(li_text)
            
            # Check if any role is in the short bio
            if any(role.lower() in short_bio.lower() for role in roles):
                anchors = [{'short_url': a['href'], 'name': a.get_text()} 
                          for a in li.find_all('a') 
                          if a['href'].startswith('/wiki/') and a['href'][6].isalpha()]
                
                # Keep only the first link
                if anchors:
                    person_entry = process_person(anchors[0], short_bio, wikipedia_api_url)
                    if person_entry:
                        filtered_li.append(person_entry)
    
    return filtered_li

def process_person(wiki_link, short_bio, wikipedia_api_url):
    """
    Process a single person entry.
    Returns a dictionary with person information.
    """
    # Extract the page title from the short_url for the summary
    page_title = wiki_link['short_url'].split('/wiki/')[1]
    
    # Fetch the summary for this person
    long_bio = fetch_wikipedia_summary(page_title, wikipedia_api_url)
    
    # Get additional person info from infobox
    person_info = extract_person_info_from_infobox(wiki_link['short_url'], wiki_link['name'])
    
    # Create the base entry
    person_entry = {
        'short_bio': short_bio,
        'short_url': wiki_link['short_url'],
        'name': wiki_link['name'],
        'long_bio': long_bio,
        'source': 'WIKI'  
    }
    
    # Add person info from infobox if available
    if person_info:
        person_entry.update({
            'first_name': person_info['first_name'],
            'last_name': person_info['last_name'],
            'image_path': person_info['image_path'],
            'date_of_birth': person_info['date_of_birth'],
            'date_of_death': person_info['date_of_death'],
            'roles': person_info['roles']
        })
    
    return person_entry

# ----------------------- DATABASE OPERATIONS ------------------------ #

def add_portraits_and_roles_to_database(roles_list=None, portraits_list=None):
    """
    Adds roles and portraits to the database.
    """
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    metadata = MetaData()
    role_table = Table("role", metadata, autoload_with=engine)
    portrait_table = Table("portrait", metadata, autoload_with=engine)
    
    try:
        # Add roles to database
        if roles_list:
            print("\nAdding roles to the database...\n")
            for item in roles_list:
                item = item.capitalize()
                stmt = select(role_table).where(role_table.c.role == item)
                result = session.execute(stmt).fetchone()
                
                if not result:
                    insert_stmt = role_table.insert().values(role=item)
                    session.execute(insert_stmt)
                    print(f"Added new role: {item}")
                else:
                    print(f"Role already exists: {item}")
        
        # Add portraits to database
        if portraits_list:
            print("\nAdding portraits to the database...\n")
            for person_info in portraits_list:
                # Skip if no roles or first role is empty
                if not person_info.get('roles') or not person_info['roles']:
                    print(f"Skipping portrait with no roles: {person_info.get('first_name', '')} {person_info.get('last_name', '')}")
                    continue
                    
                main_role = person_info['roles'][0].capitalize()
                stmt = select(role_table).where(role_table.c.role == main_role)
                role_result = session.execute(stmt).fetchone()
                
                if not role_result:
                    print(f"Role not found: {main_role}, adding it first")
                    insert_stmt = role_table.insert().values(role=main_role)
                    session.execute(insert_stmt)
                    # Get the newly inserted role
                    stmt = select(role_table).where(role_table.c.role == main_role)
                    role_result = session.execute(stmt).fetchone()
                    
                role_id = role_result[0]
                
                stmt = select(portrait_table).where(
                    (portrait_table.c.first_name == person_info['first_name']) &
                    (portrait_table.c.last_name == person_info['last_name'])
                )
                portrait_result = session.execute(stmt).fetchone()
                
                # Format dates properly
                birth_date = format_date(person_info.get('date_of_birth'), 
                                        f"{person_info['first_name']} {person_info['last_name']}", 
                                        "birth")
                
                death_date = format_date(person_info.get('date_of_death'), 
                                        f"{person_info['first_name']} {person_info['last_name']}", 
                                        "death")
                
                if not portrait_result:
                    # Add source field if it doesn't exist
                    source = person_info.get('source', f"https://en.wikipedia.org{person_info['short_url']}")
                    
                    insert_stmt = portrait_table.insert().values(
                        first_name=person_info['first_name'],
                        last_name=person_info['last_name'],
                        main_role=role_id,
                        main_photo=person_info['image_path'],
                        date_of_birth=birth_date,
                        date_of_death=death_date,
                        short_bio=person_info.get('short_bio', ''),
                        long_bio=person_info.get('long_bio', ''),
                        source=source
                    )
                    session.execute(insert_stmt)
                    print(f"Added new portrait: {person_info['first_name']} {person_info['last_name']}")
                else:
                    print(f"Portrait already exists: {person_info['first_name']} {person_info['last_name']}")
        
        # Commit changes
        session.commit()
        print("Database changes committed successfully")
    
    except Exception as e:
        session.rollback()
        print(f"Error occurred: {str(e)}")
    
    finally:
        session.close()

def add_relationships_to_database(portraits_list=None):
    """
    Adds relationships between portraits and additional roles to the database.
    """
    if not portraits_list:
        print("No portraits provided for relationship processing")
        return
        
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    metadata = MetaData()
    role_table = Table("role", metadata, autoload_with=engine)
    portrait_table = Table("portrait", metadata, autoload_with=engine)
    portraits_in_roles_table = Table("portraits_in_roles", metadata, autoload_with=engine)
    
    try:
        print("\nAdding relationships to the database...\n")
        for person_info in portraits_list:
            # Skip if no roles or less than 2 roles
            if not person_info.get('roles') or len(person_info['roles']) < 2:
                continue
                
            stmt = select(portrait_table).where(
                (portrait_table.c.first_name == person_info['first_name']) &
                (portrait_table.c.last_name == person_info['last_name'])
            )
            portrait_result = session.execute(stmt).fetchone()
            
            if not portrait_result:
                print(f"Portrait not found: {person_info['first_name']} {person_info['last_name']}, skipping relationships")
                continue
                
            portrait_id = portrait_result[0]
            
            for role in person_info['roles'][1:]: 
                additional_role = role.capitalize()
                stmt = select(role_table).where(role_table.c.role == additional_role)
                role_result = session.execute(stmt).fetchone()
                
                if not role_result:
                    print(f"Role not found: {additional_role}, adding it first")
                    insert_stmt = role_table.insert().values(role=additional_role)
                    session.execute(insert_stmt)
                    # Get the newly inserted role
                    stmt = select(role_table).where(role_table.c.role == additional_role)
                    role_result = session.execute(stmt).fetchone()
                
                additional_role_id = role_result[0]
                
                stmt = select(portraits_in_roles_table).where(
                    (portraits_in_roles_table.c.portrait_id == portrait_id) &
                    (portraits_in_roles_table.c.role_id == additional_role_id)
                )
                portraits_in_roles_result = session.execute(stmt).fetchone()
                
                if not portraits_in_roles_result:                       
                    insert_stmt = portraits_in_roles_table.insert().values(
                        portrait_id=portrait_id,
                        role_id=additional_role_id
                    )
                    session.execute(insert_stmt)
                    print(f"Added relationship: {additional_role} for portrait: {person_info['first_name']} {person_info['last_name']}")
                else:
                    print(f"Existed relationship: {additional_role} for portrait: {person_info['first_name']} {person_info['last_name']}")
        
        # Commit changes
        session.commit()
        print("Relationship changes committed successfully")
    
    except Exception as e:
        session.rollback()
        print(f"Error occurred: {str(e)}")
    
    finally:
        session.close()