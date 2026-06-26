"""
Clause Classification Module
Classifies legal clauses into categories: Termination, Confidentiality, Payment, etc.
"""

import re
from typing import Dict, List, Tuple

# Clause category keywords
CLAUSE_KEYWORDS = {
    'termination': [
        'terminate', 'termination', 'cancel', 'cancellation', 'end of agreement',
        'expiration', 'expire', 'cease', 'dissolution'
    ],
    'confidentiality': [
        'confidential', 'confidentiality', 'non-disclosure', 'nda', 'proprietary',
        'trade secret', 'private information', 'sensitive information'
    ],
    'payment': [
        'payment', 'pay', 'fee', 'cost', 'price', 'compensation', 'invoice',
        'billing', 'remuneration', 'salary', 'wage'
    ],
    'liability': [
        'liability', 'liable', 'indemnify', 'indemnification', 'hold harmless',
        'damages', 'limitation of liability', 'cap on liability'
    ],
    'intellectual_property': [
        'intellectual property', 'ip rights', 'copyright', 'patent', 'trademark',
        'license', 'licensing', 'proprietary rights', 'ownership'
    ],
    'non_compete': [
        'non-compete', 'non compete', 'competition', 'competitive restriction',
        'covenant not to compete', 'exclusivity'
    ],
    'governing_law': [
        'governing law', 'jurisdiction', 'governed by', 'laws of', 'venue',
        'applicable law', 'choice of law'
    ],
    'warranty': [
        'warranty', 'warranties', 'guarantee', 'representation', 'warrant',
        'as is', 'merchantability', 'fitness for purpose'
    ],
    'force_majeure': [
        'force majeure', 'act of god', 'natural disaster', 'pandemic',
        'unforeseeable', 'beyond control'
    ],
    'assignment': [
        'assignment', 'assign', 'transfer', 'delegate', 'succession',
        'assignable', 'transferable'
    ],
    'ownership': [
        'ownership', 'owner', 'retain ownership', 'sole owner', 'title to',
        'property of', 'exclusive property'
    ],
    'transfer': [
        'transfer', 'transfer of title', 'convey', 'conveyance', 'assign and transfer',
        'sell and transfer', 'transferability'
    ]
}


def classify_clauses(text: str) -> List[Dict[str, any]]:
    """
    Classify clauses in the document text.
    
    Args:
        text: The document text to analyze
        
    Returns:
        List of dicts with clause type, excerpt, and confidence
    """
    clauses = []
    
    # Split by common section delimiters
    paragraphs = re.split(r'\n\s*\n|\n(?=\d+\.|\([a-z]\))', text)
    
    for para in paragraphs:
        para = para.strip()
        if len(para) < 20:  # Skip very short segments
            continue
        
        para_lower = para.lower()
        
        # Check each clause category
        for clause_type, keywords in CLAUSE_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in para_lower)
            if matches > 0:
                confidence = min(matches / 3 * 100, 100)  # Cap at 100%
                
                # Get a clean excerpt
                excerpt = para[:200] + "..." if len(para) > 200 else para
                
                clauses.append({
                    'type': clause_type.replace('_', ' ').title(),
                    'excerpt': excerpt,
                    'confidence': round(confidence, 1),
                    'keyword_matches': matches
                })
    
    # Sort by confidence and remove duplicates
    clauses.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Keep only top clause per type
    seen_types = set()
    unique_clauses = []
    for clause in clauses:
        if clause['type'] not in seen_types:
            seen_types.add(clause['type'])
            unique_clauses.append(clause)
    
    return unique_clauses


def format_clauses_for_display(clauses: List[Dict]) -> str:
    """Format classified clauses for UI display."""
    if not clauses:
        return "No specific clauses identified."
    
    output = []
    for clause in clauses:
        emoji = get_clause_emoji(clause['type'])
        output.append(f"### {emoji} {clause['type']}")
        output.append(f"*Confidence: {clause['confidence']}%*")
        output.append(f"> {clause['excerpt']}")
        output.append("")
    
    return "\n".join(output)


def get_clause_emoji(clause_type: str) -> str:
    """Get emoji for clause type."""
    emojis = {
        'Termination': '🔚',
        'Confidentiality': '🔒',
        'Payment': '💳',
        'Liability': '⚠️',
        'Intellectual Property': '💡',
        'Non Compete': '🚫',
        'Governing Law': '⚖️',
        'Warranty': '✅',
        'Force Majeure': '🌪️',
        'Assignment': '📝',
        'Ownership': '🏰',
        'Transfer': '📦'
    }
    return emojis.get(clause_type, '📄')
