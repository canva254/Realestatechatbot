import requests
import logging
import time
from functools import lru_cache
from config import WP_API_URL, PARAMS, ERROR_MESSAGES, CACHE_TTL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store cached data with expiration times
_cache = {}

def timed_cache(seconds=CACHE_TTL):
    """
    Create a cache decorator with time-based expiration
    
    Args:
        seconds (int): Time to live for cached results in seconds
        
    Returns:
        function: Decorator for caching function results
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            
            # Check if we have a cached result and it's still valid
            if key in _cache:
                result, timestamp = _cache[key]
                if time.time() - timestamp < seconds:
                    logger.info(f"Cache hit for {func.__name__}: Using cached data")
                    return result
            
            # Get fresh result
            logger.info(f"Cache miss for {func.__name__}: Fetching fresh data")
            result = func(*args, **kwargs)
            _cache[key] = (result, time.time())
            return result
        return wrapper
    return decorator

@timed_cache()
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

@timed_cache()
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
            location = property['acf']['location']
            # Only add string locations, skip None or other types
            if isinstance(location, str) and location.strip():
                locations.add(location)
            else:
                logger.warning(f"Skipping invalid location in property {property.get('id', 'unknown')}: {location}")
    
    locations = sorted(list(locations))
    logger.info(f"Extracted {len(locations)} unique locations: {locations}")
    return locations

@timed_cache()
def get_properties_by_location(location):
    """
    Filter properties by location using direct API filtering
    
    Args:
        location (str): Location to filter by
        
    Returns:
        list: List of filtered property dictionaries or None if there was an error
    """
    # Validate location is a string
    if not isinstance(location, str):
        logger.error(f"Invalid location type: {type(location)}. Expected string.")
        return None
        
    if not location.strip():
        logger.error("Empty location string provided")
        return None
        
    try:
        # Use the direct filter endpoint for better performance
        filter_url = f"{WP_API_URL}?acf[location]={location}&_embed"
        logger.info(f"Fetching properties by location from {filter_url}")
        
        response = requests.get(filter_url)
        response.raise_for_status()
        
        properties = response.json()
        logger.info(f"Found {len(properties)} properties in {location}")
        
        return properties if properties else None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching properties by location: {e}")
        
        # Fallback to local filtering if the API filter fails
        logger.info("Falling back to local filtering")
        properties = fetch_properties()
        if not properties:
            return None
        
        # Filter properties by location
        filtered_properties = []
        for property in properties:
            if ('acf' in property and 
                'location' in property['acf'] and 
                isinstance(property['acf']['location'], str) and
                property['acf']['location'] == location):
                filtered_properties.append(property)
        
        logger.info(f"Found {len(filtered_properties)} properties in {location} (fallback)")
        return filtered_properties if filtered_properties else None
