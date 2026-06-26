"""
Named Entity Recognition (NER) Module
Extracts legal entities: Parties, Dates, Monetary Values, Governing Laws
"""

import re
from dateutil import parser as date_parser
from typing import Dict, List, Any

# Patterns for legal entity extraction
PATTERNS = {
    'parties': [
        r'(?:between|by and between|among)\s+([A-Z][A-Za-z\s,\.]+?)(?:\s+and\s+|\s*,\s*)',
        r'(?:BORROWER|LENDER|LICENSOR|LICENSEE|SELLER|BUYER|LANDLORD|TENANT|EMPLOYER|EMPLOYEE|CLIENT|CONTRACTOR)[\s:]+([A-Z][A-Za-z\s,\.]+?)(?:\.|,|\n)',
        r'([A-Z][A-Za-z\s]+(?:Inc\.|Corp\.|LLC|Ltd\.|Company|Corporation))',
    ],
    'dates': [
        r'(?:dated|effective|as of|on)\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        r'(?:dated|effective|as of|on)\s+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
    ],
    'monetary_values': [
        r'\$[\d,]+(?:\.\d{2})?',
        r'(?:USD|EUR|GBP)\s*[\d,]+(?:\.\d{2})?',
        r'[\d,]+(?:\.\d{2})?\s*(?:dollars|euros|pounds)',
    ],
    'governing_law': [
        r'(?:governed by|laws of|jurisdiction of)\s+(?:the\s+)?(?:State of\s+)?([A-Za-z\s]+)',
        r'(?:State of|Commonwealth of)\s+([A-Za-z\s]+)',
    ],
    'percentages': [
        r'(\d+(?:\.\d+)?)\s*(?:%|percent|per cent)',
    ],
    'durations': [
        r'(\d+)\s*(?:months?|years?|days?|weeks?)',
        r'(?:term of|period of)\s+(\d+)\s*(?:months?|years?|days?)',
    ],
    'past_owners': [
        r'(?:Owner(?:s)?|Seller|Grantor|Landlord|Lessor|Seller\s*\(Grantor\)|Seller/Grantor)[\s:]+([A-Z][A-Za-z\s,\.]+?)(?:\.|,|\n|\r|\[|\()',
        r'(?:property(?: is)? owned by|title held by|previously owned by)\s+([A-Z][A-Za-z\s,\.]+?)(?:\.|,|\n|\r)',
    ],
    'current_owners': [
        r'(?:Buyer|Grantee|Purchaser|Tenant|Lessee|Buyer\s*\(Grantee\)|Purchaser/Grantee)[\s:]+([A-Z][A-Za-z\s,\.]+?)(?:\.|,|\n|\r|\[|\()',
    ],
    'properties': [
        r'(?:property located at|address(?:ed)? at|situate[d]? at)(?:[:\s]+)([A-Za-z0-9\s,\.]+?)(?:\.|,|\n)',
        r'(?:real property|premises)\s+(?:commonly known as|located at)(?:[:\s]+)([A-Za-z0-9\s,\.]+?)(?:\.|,|\n)',
    ]
}


def extract_entities(text: str) -> Dict[str, List[Any]]:
    """
    Extract named entities from legal document text.
    
    Args:
        text: The document text to analyze
        
    Returns:
        Dictionary with entity types as keys and lists of found entities as values
    """
    entities = {
        'parties': [],
        'past_owners': [],
        'current_owners': [],
        'properties': [],
        'dates': [],
        'monetary_values': [],
        'governing_law': [],
        'percentages': [],
        'durations': []
    }
    
    # Extract parties
    for pattern in PATTERNS['parties']:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean = match.strip().strip(',').strip('.')
            if clean and len(clean) > 2 and clean not in entities['parties']:
                entities['parties'].append(clean)
    
    # Extract dates
    for pattern in PATTERNS['dates']:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                parsed_date = date_parser.parse(match, fuzzy=True)
                formatted = parsed_date.strftime('%B %d, %Y')
                if formatted not in entities['dates']:
                    entities['dates'].append(formatted)
            except:
                if match not in entities['dates']:
                    entities['dates'].append(match)
    
    # Extract monetary values
    for pattern in PATTERNS['monetary_values']:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if match not in entities['monetary_values']:
                entities['monetary_values'].append(match)
    
    # Extract governing law
    for pattern in PATTERNS['governing_law']:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean = match.strip()
            if clean and len(clean) > 2 and clean not in entities['governing_law']:
                entities['governing_law'].append(clean)
    
    # Extract percentages
    for pattern in PATTERNS['percentages']:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            formatted = f"{match}%"
            if formatted not in entities['percentages']:
                entities['percentages'].append(formatted)
    
    # Extract durations
    for pattern in PATTERNS['durations']:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if match not in entities['durations']:
                entities['durations'].append(match)
                
    # Extract past_owners
    for pattern in PATTERNS.get('past_owners', []):
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean = match.strip().strip(',').strip('.')
            if clean and len(clean) > 2 and clean not in entities['past_owners'] and "Signature" not in clean:
                entities['past_owners'].append(clean)
                
    # Extract current_owners
    for pattern in PATTERNS.get('current_owners', []):
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean = match.strip().strip(',').strip('.')
            if clean and len(clean) > 2 and clean not in entities['current_owners'] and "Signature" not in clean:
                entities['current_owners'].append(clean)
                
    # Extract properties
    for pattern in PATTERNS['properties']:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean = match.strip().strip(',').strip('.')
            if clean and len(clean) > 5 and clean not in entities['properties']:
                entities['properties'].append(clean)
    
    return entities


def format_entities_for_display(entities: Dict[str, List[Any]]) -> str:
    """Format extracted entities for UI display."""
    output = []
    
    if entities['parties']:
        output.append("**📋 Parties Involved:**")
        for party in entities['parties'][:5]:  # Limit to 5
            output.append(f"- {party}")
            
    if entities.get('past_owners'):
        output.append("\n**⬅️ Past Owners / Sellers (Grantor):**")
        for owner in entities['past_owners'][:5]:
            output.append(f"- {owner}")
            
    if entities.get('current_owners'):
        output.append("\n**➡️ Current Owners / Buyers (Grantee):**")
        for owner in entities['current_owners'][:5]:
            output.append(f"- {owner}")
            
    if entities.get('properties'):
        output.append("\n**🏠 Properties / Addresses:**")
        for prop in entities['properties'][:5]:
            output.append(f"- {prop}")
    
    if entities['dates']:
        output.append("\n**📅 Key Dates:**")
        for date in entities['dates'][:5]:
            output.append(f"- {date}")
    
    if entities['monetary_values']:
        output.append("\n**💰 Monetary Values:**")
        for value in entities['monetary_values'][:5]:
            output.append(f"- {value}")
    
    if entities['governing_law']:
        output.append("\n**⚖️ Governing Law:**")
        for law in entities['governing_law'][:3]:
            output.append(f"- {law}")
    
    if entities['percentages']:
        output.append("\n**📊 Percentages/Rates:**")
        for pct in entities['percentages'][:5]:
            output.append(f"- {pct}")
    
    if entities['durations']:
        output.append("\n**⏱️ Time Periods:**")
        for dur in entities['durations'][:5]:
            output.append(f"- {dur}")
    
    return "\n".join(output) if output else "No entities detected."
