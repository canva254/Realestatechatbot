import logging
from api import get_locations, get_properties_by_location

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_locations():
    # Get all locations
    locations = get_locations()
    print(f"Locations: {locations}")
    
    # Test each location to see if we can get properties
    for location in locations:
        print(f"\nTesting location: {location}")
        properties = get_properties_by_location(location)
        if properties:
            print(f"SUCCESS: Found {len(properties)} properties in {location}")
            # Check the location of the first property
            first_property = properties[0]
            if 'acf' in first_property and 'location' in first_property['acf']:
                print(f"First property location: {first_property['acf']['location']}")
                print(f"First property location type: {type(first_property['acf']['location'])}")
            else:
                print("Location data missing in first property")
        else:
            print(f"FAILED: No properties found for {location}")

if __name__ == "__main__":
    test_locations()