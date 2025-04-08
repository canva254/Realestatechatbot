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
        # Ensure _embed parameter is included for proper image loading
        embed_url = f"{WP_API_URL}?_embed"
        logger.info(f"Fetching properties from {embed_url}")
        
        response = requests.get(embed_url, params=PARAMS)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        properties = response.json()
        logger.info(f"Successfully fetched {len(properties)} properties with embedded data")
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
        return ["Lavington"]  # Return a default location if API fails
    
    # Extract unique locations from the acf.location field
    locations = set()
    for property in properties:
        if 'acf' in property and 'location' in property['acf']:
            location = property['acf']['location']
            # Only add string locations, skip None or other types
            if isinstance(location, str) and location.strip():
                locations.add(location)
            else:
                # Log the warning and try to extract a string representation if possible
                logger.warning(f"Invalid location format in property {property.get('id', 'unknown')}: {type(location)}")
                try:
                    # Try to convert to string if it's something that can be represented as a string
                    str_location = str(location)
                    if str_location and str_location.strip():
                        logger.info(f"Successfully converted location to string: {str_location}")
                        locations.add(str_location)
                except Exception as e:
                    logger.error(f"Could not convert location to string: {e}")
    
    # If no locations found, add a default one
    if not locations:
        logger.warning("No valid locations found, adding default location 'Lavington'")
        locations.add("Lavington")
    
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
    # Validate and convert location to a string if needed
    if not isinstance(location, str):
        logger.warning(f"Invalid location type: {type(location)}. Expected string. Attempting to convert...")
        try:
            location = str(location)
            logger.info(f"Successfully converted location to string: {location}")
        except Exception as e:
            logger.error(f"Failed to convert location to string: {e}")
            return None
        
    if not location.strip():
        logger.error("Empty location string provided")
        return None
        
    try:
        # Use the direct filter endpoint for better performance
        # Include _embed parameter in both URL and params to ensure featured images are included
        filter_url = f"{WP_API_URL}?acf[location]={location}&_embed"
        filter_params = {"_embed": True, "per_page": 100}
        logger.info(f"Fetching properties by location from {filter_url}")
        
        response = requests.get(filter_url, params=filter_params)
        response.raise_for_status()
        
        properties = response.json()
        logger.info(f"Found {len(properties)} properties in {location} with embedded data")
        
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
            if 'acf' in property and 'location' in property['acf']:
                prop_location = property['acf']['location']
                
                # Try to match either string or converted string
                if isinstance(prop_location, str) and prop_location == location:
                    filtered_properties.append(property)
                # Try to convert to string and compare if not already a string
                elif not isinstance(prop_location, str):
                    try:
                        if str(prop_location) == location:
                            logger.info(f"Matched after converting non-string location to string: {prop_location}")
                            filtered_properties.append(property)
                    except Exception as e:
                        logger.error(f"Error comparing location strings: {e}")
        
        logger.info(f"Found {len(filtered_properties)} properties in {location} (fallback)")
        return filtered_properties if filtered_properties else None
