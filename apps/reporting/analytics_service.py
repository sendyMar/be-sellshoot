from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from ..extraction.models import Screenshot, ExtractedItem
from ..tasks.models import Task

def get_user_analytics(user):
    now = timezone.localtime(timezone.now()).date()
    
    # 1. Performance Trend (Last 7 Days)
    # We will compute total orders from ExtractedItems and completed tasks from Task
    trend_data = []
    for i in range(6, -1, -1):
        target_date = now - timedelta(days=i)
        
        # Orders extracted on this date
        orders_count = ExtractedItem.objects.filter(
            extraction_result__screenshot__user=user,
            extraction_result__processed_at__date=target_date,
            extraction_result__screenshot__tag__in=['order_list', 'order_detail']
        ).count()
        
        # Tasks on this date
        tasks_qs = Task.objects.filter(user=user, date=target_date)
        tasks_total = tasks_qs.count()
        tasks_completed = tasks_qs.filter(is_completed=True).count()
        
        trend_data.append({
            "date": target_date.strftime("%d %b"),
            "full_date": str(target_date),
            "orders": orders_count,
            "tasks_total": tasks_total,
            "tasks_completed": tasks_completed,
        })
        
    # 2. Top Products (Last 30 Days)
    thirty_days_ago = now - timedelta(days=30)
    top_products_qs = ExtractedItem.objects.filter(
        extraction_result__screenshot__user=user,
        extraction_result__processed_at__date__gte=thirty_days_ago,
        extraction_result__screenshot__tag__in=['order_list', 'order_detail']
    ).values('product_name').annotate(total=Count('id')).order_by('-total')[:5]
    
    top_products = []
    for tp in top_products_qs:
        name = tp['product_name'] if tp['product_name'] else "Unknown"
        top_products.append({
            "name": name,
            "value": tp['total']
        })
        
    if not top_products:
        # Dummy fallback for empty state visualization
        top_products = [
            {"name": "Belum Ada Data", "value": 1}
        ]
        
    # 3. Platform Sources (Last 30 Days)
    platforms_qs = Screenshot.objects.filter(
        user=user,
        uploaded_at__date__gte=thirty_days_ago
    ).values('platform').annotate(total=Count('id')).order_by('-total')
    
    platform_data = []
    for p in platforms_qs:
        platform_data.append({
            "platform": p['platform'].capitalize(),
            "count": p['total']
        })
        
    # 4. Task Category Distribution (Last 30 Days)
    categories_qs = Task.objects.filter(
        user=user,
        date__gte=thirty_days_ago
    ).values('category').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(is_completed=True))
    )
    
    category_data = []
    cat_map = dict(Task.CATEGORY_CHOICES)
    for c in categories_qs:
        category_data.append({
            "category": cat_map.get(c['category'], c['category']),
            "total": c['total'],
            "completed": c['completed']
        })
        
    return {
        "trend": trend_data,
        "top_products": top_products,
        "platforms": platform_data,
        "task_categories": category_data
    }
