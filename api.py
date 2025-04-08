import requests
import logging
from config import WP_API_URL, PARAMS, ERROR_MESSAGES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_properties():
    """
    Fetch all properties from the WordPress API
    
    Returns:
        list: List of property dictionaries or None if there was an error
    """
    try:
        logger.info(f"Fetching properties from {WP_API_URL}")
        response = requests.get(WP_API_URL, params=PARAMS)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        properties = response.json()
        logger.info(f"Successfully fetched {len(properties)} properties")
        return properties
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching properties: {e}")
        return None

def get_locations():
    """
    Extract unique locations from all properties
    
    Returns:
        list: List of unique locations or None if there was an error
    """
    properties = fetch_properties()
    if not properties:
        return None
    
    # Extract unique locations from the acf.location field
    locations = set()
    for property in properties:
        if 'acf' in property and 'location' in property['acf']:
            locations.add(property['acf']['location'])
    
    locations = sorted(list(locations))
    logger.info(f"Extracted {len(locations)} unique locations: {locations}")
    return locations

def get_properties_by_location(location):
    """
    Filter properties by location
    
    Args:
        location (str): Location to filter by
        
    Returns:
        list: List of filtered property dictionaries or None if there was an error
    """
    properties = fetch_properties()
    if not properties:
        return None
    
    # Filter properties by location
    filtered_properties = []
    for property in properties:
        if ('acf' in property and 
            'location' in property['acf'] and 
            property['acf']['location'] == location):
            filtered_properties.append(property)
    
    logger.info(f"Found {len(filtered_properties)} properties in {location}")
    return filtered_properties if filtered_properties else None
