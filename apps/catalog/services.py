import difflib
from django.db.models import Q
from .models import Product, ProductAlias

def find_product_match(user, raw_name, platform):
    """
    Cari kecocokan nama produk mentah dengan katalog yang ada.
    1. Cek Exact Match di ProductAlias
    2. Cek Fuzzy Match jika tidak ada exact match
    Returns dict: { match_type, product_id, product_name, confidence, candidates }
    """
    # 1. Exact Match di ProductAlias
    exact_alias = ProductAlias.objects.filter(
        product__user=user, 
        alias_name__iexact=raw_name, 
        platform=platform
    ).first()
    
    if exact_alias:
        return {
            'match_type': 'exact',
            'product_id': exact_alias.product.id,
            'product_name': exact_alias.product.canonical_name,
            'confidence': 1.0,
            'candidates': []
        }
        
    # 2. Fuzzy Match
    all_products = Product.objects.filter(user=user)
    candidates = []
    
    for product in all_products:
        # Bandingkan dengan nama kanonikal
        ratio_canon = difflib.SequenceMatcher(None, raw_name.lower(), product.canonical_name.lower()).ratio()
        best_ratio = ratio_canon
        
        # Bandingkan dengan semua alias produk ini
        for alias in product.aliases.all():
            ratio_alias = difflib.SequenceMatcher(None, raw_name.lower(), alias.alias_name.lower()).ratio()
            if ratio_alias > best_ratio:
                best_ratio = ratio_alias
                
        if best_ratio >= 0.5: # Threshold fuzzy (50% kemiripan)
            candidates.append({
                'product_id': product.id,
                'product_name': product.canonical_name,
                'confidence': best_ratio
            })
            
    # Sort candidates by confidence (descending)
    candidates.sort(key=lambda x: x['confidence'], reverse=True)
    
    return {
        'match_type': 'fuzzy' if candidates else 'none',
        'product_id': None,
        'product_name': None,
        'confidence': 0.0,
        'candidates': candidates[:5] # Ambil top 5
    }

def create_new_product(user, canonical_name, alias_name, platform, sku='', category='', cost_price=None, retail_price=None, global_stock=0):
    product = Product.objects.create(
        user=user,
        canonical_name=canonical_name,
        sku=sku,
        category=category,
        cost_price=cost_price,
        retail_price=retail_price,
        global_stock=global_stock
    )
    ProductAlias.objects.create(
        product=product,
        alias_name=alias_name,
        platform=platform,
        created_by_correction=False
    )
    return product

def save_product_alias(product_id, alias_name, platform, is_correction=False):
    alias, created = ProductAlias.objects.get_or_create(
        product_id=product_id,
        alias_name=alias_name,
        platform=platform,
        defaults={'created_by_correction': is_correction}
    )
    return alias
