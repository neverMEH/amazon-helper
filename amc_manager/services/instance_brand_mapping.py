"""Instance to Brand mapping service"""

from typing import List, Optional
import re

def extract_brand_keywords(instance_name: str) -> List[str]:
    """Extract potential brand keywords from instance name
    
    Examples:
    - 'recommercetruegraceus' -> ['truegrace', 'true grace']
    - 'recommerceusurbanDecayus' -> ['urbandecay', 'urban decay']
    """
    # Remove common prefixes/suffixes
    cleaned = instance_name.lower()
    cleaned = re.sub(r'^(recommerce|recom|nevermeh)', '', cleaned)
    cleaned = re.sub(r'(us|ca|eu|uk|au|sandbox)$', '', cleaned)
    cleaned = re.sub(r'^us', '', cleaned)
    
    # Handle camelCase and add space variants
    keywords = [cleaned]
    
    # Add spaced version for multi-word brands
    spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned)
    if spaced != cleaned:
        keywords.append(spaced)
    
    # Add specific known mappings
    brand_mappings = {
        'truegrace': ['Terry Naturally', 'Terry Naturally Canada'],
        'urbandecay': ['Urban Decay'],
        'itcosmetics': ['IT Cosmetics'],
        'irwinnaturals': ['Irwin Naturals'],
        'probulin': ['Probulin'],
        'ridgecrestherbals': ['Ridgecrest Herbals'],
        'bioray': ['Bioray'],
        'drunkelephant': ['Drunk Elephant'],
        'juicebeauty': ['Juice Beauty'],
        'supergoop': ['Supergoop!', 'Supergoop'],
        'beekman1802': ['Beekman 1802'],
        'wolf1834': ['Wolf 1834'],
        'nestneyork': ['NEST New York', 'Nest New York'],
        'isseymiyake': ['Issey Miyake'],
        'cellFood': ['Cell Food'],
        'bruntworkwear': ['Brunt Workwear'],
        'babyen': ['BabyZen'],
        'oofos': ['OOFOS'],
        'sovnightguards': ['SoVa Night Guards'],
        'sisumouthguards': ['Sisu Mouthguards'],
        'mastersupplements': ['Master Supplements'],
        'beastsportsnutrition': ['Beast Sports Nutrition'],
        'lafco': ['LAFCO'],
        'solgar': ['Solgar'],
        'biosil': ['BioSil'],
        'tevita': ['TeVita'],
        'shiseido': ['Shiseido'],
        'tenpoint': ['Ten Point'],
        'naturesplus': ['NaturesPlus', 'Natures Plus'],
        'kneipp': ['Kneipp'],
        'nah': ['NAH'],
        'stokke': ['Stokke'],
        'strider': ['Strider'],
        'triangle': ['Triangle'],
        'finaflex': ['FinaFlex'],
        'drbrandt': ['Dr. Brandt'],
        'skinfix': ['SkinFix'],
        'desertfoxgolf': ['Desert Fox Golf'],
        'emfharmony': ['EMF Harmony'],
        'typhoonhelmets': ['Typhoon Helmets'],
        'dirtylabs': ['Dirty Labs'],
        'fekkai': ['Fekkai'],
        'masimostork': ['Masimo Stork'],
        'dphhue': ['DPHue', 'DPH Hue'],
        'eartlybody': ['Earthly Body'],
        'messermeister': ['Messermeister'],
        'kusmitea': ['Kusmi Tea'],
        'zak': ['Zak'],
        'bioelements': ['Bioelements'],
        'brainmd': ['BrainMD', 'Brain MD'],
        'beautyforreall': ['Beauty For Real'],
        'defender': ['Defender Operations'],
        'ikous': ['iKous'],
        'nelsonus': ['Nelson'],
        'petagus': ['Petagus']
    }
    
    # Check for known mappings
    for key, brands in brand_mappings.items():
        if key in cleaned:
            return brands
    
    return keywords


def get_brands_for_instance(instance_name: str) -> List[str]:
    """Get list of potential brand matches for an instance name"""
    return extract_brand_keywords(instance_name)


def create_instance_brand_filter(instance_name: str) -> Optional[List[str]]:
    """Create a brand filter for campaigns based on instance name
    
    Returns list of brand names to filter by, or None for no filter
    """
    # Handle test/sandbox instances
    if any(x in instance_name.lower() for x in ['test', 'sandbox', 'nevermeh']):
        # For test instances, show all campaigns or none
        return None
    
    return get_brands_for_instance(instance_name)