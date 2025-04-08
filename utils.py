def format_property_message(property_data):
    """
    Format property data into a markdown message for Telegram
    
    Args:
        property_data (dict): Property data dictionary
        
    Returns:
        str: Formatted markdown message
    """
    # Extract property name from title
    property_name = property_data['title']['rendered'] if 'title' in property_data and 'rendered' in property_data['title'] else "Unnamed Property"
    
    # Extract ACF fields (Advanced Custom Fields)
    acf = property_data.get('acf', {})
    price = acf.get('price', 'N/A')
    location = acf.get('location', 'N/A')
    bedrooms = acf.get('bedrooms', 'N/A')
    bathrooms = acf.get('bathrooms', 'N/A')
    
    # Format the message using markdown
    message = (
        f"🏠 *{property_name}*\n"
        f"💰 Price: {price}\n"
        f"🛏 Bedrooms: {bedrooms}\n"
        f"🚽 Bathrooms: {bathrooms}\n"
        f"📍 Location: {location}"
    )
    
    return message

def get_property_image_url(property_data):
    """
    Extract the featured image URL from property data
    
    Args:
        property_data (dict): Property data dictionary
        
    Returns:
        str: Image URL or None if not found
    """
    try:
        # Navigate through the nested structure to get the featured image URL
        if '_embedded' in property_data and 'wp:featuredmedia' in property_data['_embedded']:
            featured_media = property_data['_embedded']['wp:featuredmedia']
            if featured_media and len(featured_media) > 0 and 'source_url' in featured_media[0]:
                return featured_media[0]['source_url']
    except (KeyError, IndexError) as e:
        # If any key is missing, return None
        return None
    
    return None
