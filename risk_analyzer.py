"""
Risk Analysis Module
Analyzes clauses and assigns risk levels: Low, Medium, High
"""

import re
from typing import Dict, List, Tuple
from textblob import TextBlob

# High risk indicators
HIGH_RISK_KEYWORDS = [
    'unlimited liability', 'uncapped liability', 'sole discretion',
    'terminate without cause', 'immediately terminate', 'without notice',
    'non-compete', 'non-solicitation', 'exclusive rights', 'perpetual license',
    'irrevocable', 'waive all rights', 'indemnify and hold harmless',
    'consequential damages', 'punitive damages', 'penalty', 'liquidated damages',
    'automatic renewal', 'binding arbitration', 'class action waiver'
]

# Medium risk indicators
MEDIUM_RISK_KEYWORDS = [
    'limitation of liability', 'cap on damages', 'maximum liability',
    'confidentiality obligations', 'non-disclosure', 'proprietary information',
    'assign', 'transfer', 'sublicense', 'amendment', 'modification',
    'governing law', 'jurisdiction', 'venue', 'notice period',
    'termination fee', 'early termination', 'renewal'
]

# Low risk / Standard clauses
LOW_RISK_KEYWORDS = [
    'standard terms', 'mutual agreement', 'written consent',
    'reasonable efforts', 'good faith', 'commercially reasonable',
    'warranty', 'representation', 'compliance with laws'
]


def analyze_risk(text: str) -> Dict[str, any]:
    """
    Analyze risk levels in the document.
    
    Args:
        text: The document text to analyze
        
    Returns:
        Dictionary with overall risk assessment and detailed findings
    """
    text_lower = text.lower()
    
    findings = {
        'high_risk': [],
        'medium_risk': [],
        'low_risk': [],
        'overall_score': 0,
        'overall_level': 'Low'
    }
    
    # Check for high risk indicators
    for keyword in HIGH_RISK_KEYWORDS:
        if keyword in text_lower:
            # Find the sentence containing this keyword
            pattern = rf'[^.]*{re.escape(keyword)}[^.]*\.'
            matches = re.findall(pattern, text_lower)
            if matches:
                findings['high_risk'].append({
                    'keyword': keyword,
                    'context': matches[0][:150].strip()
                })
    
    # Check for medium risk indicators
    for keyword in MEDIUM_RISK_KEYWORDS:
        if keyword in text_lower:
            pattern = rf'[^.]*{re.escape(keyword)}[^.]*\.'
            matches = re.findall(pattern, text_lower)
            if matches:
                findings['medium_risk'].append({
                    'keyword': keyword,
                    'context': matches[0][:150].strip()
                })
    
    # Check for low risk / positive indicators
    for keyword in LOW_RISK_KEYWORDS:
        if keyword in text_lower:
            findings['low_risk'].append({'keyword': keyword})
    
    # Calculate overall risk score
    high_count = len(findings['high_risk'])
    medium_count = len(findings['medium_risk'])
    low_count = len(findings['low_risk'])
    
    # Weighted scoring
    risk_score = (high_count * 3) + (medium_count * 1) - (low_count * 0.5)
    
    # Normalize to 0-100
    findings['overall_score'] = min(max(int(risk_score * 10), 0), 100)
    
    # Determine overall level
    if high_count >= 3 or findings['overall_score'] >= 60:
        findings['overall_level'] = 'High'
    elif high_count >= 1 or medium_count >= 3 or findings['overall_score'] >= 30:
        findings['overall_level'] = 'Medium'
    else:
        findings['overall_level'] = 'Low'
    
    # Add sentiment analysis for additional context
    blob = TextBlob(text)
    findings['sentiment'] = {
        'polarity': round(blob.sentiment.polarity, 2),
        'subjectivity': round(blob.sentiment.subjectivity, 2)
    }
    
    return findings


def format_risk_for_display(risk_data: Dict) -> str:
    """Format risk analysis for UI display."""
    output = []
    
    # Overall risk level with emoji
    level_emoji = {
        'High': '🔴',
        'Medium': '🟡', 
        'Low': '🟢'
    }
    
    emoji = level_emoji.get(risk_data['overall_level'], '⚪')
    output.append(f"## {emoji} Overall Risk Level: **{risk_data['overall_level']}**")
    output.append(f"Risk Score: {risk_data['overall_score']}/100")
    output.append("")
    
    # High risk findings
    if risk_data['high_risk']:
        output.append("### 🔴 High Risk Items")
        for item in risk_data['high_risk'][:5]:
            output.append(f"- **{item['keyword'].title()}**")
            output.append(f"  > _{item['context']}_")
        output.append("")
    
    # Medium risk findings
    if risk_data['medium_risk']:
        output.append("### 🟡 Medium Risk Items")
        for item in risk_data['medium_risk'][:5]:
            output.append(f"- {item['keyword'].title()}")
        output.append("")
    
    # Positive indicators
    if risk_data['low_risk']:
        output.append("### 🟢 Positive Indicators")
        keywords = [item['keyword'].title() for item in risk_data['low_risk'][:5]]
        output.append(f"Found: {', '.join(keywords)}")
        output.append("")
    
    # Sentiment note
    if risk_data['sentiment']['polarity'] < -0.1:
        output.append("⚠️ *Document language has a negative tone overall.*")
    elif risk_data['sentiment']['polarity'] > 0.1:
        output.append("✅ *Document language has a positive/neutral tone.*")
    
    return "\n".join(output)


def get_risk_color(level: str) -> str:
    """Get color code for risk level."""
    colors = {
        'High': '#ef4444',
        'Medium': '#f59e0b',
        'Low': '#22c55e'
    }
    return colors.get(level, '#6b7280')
