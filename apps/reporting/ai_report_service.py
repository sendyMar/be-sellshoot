import os
import json
from groq import Groq
from django.utils import timezone
from ..extraction.models import ExtractionResult
from ..tasks.models import Task
from .models import DailyReport

SYSTEM_PROMPT_REPORT = """Kamu adalah 'SellShoot AI Companion' yang bertugas memberikan rangkuman performa harian untuk penjual online (seller).
ATURAN:
1. Gunakan gaya bahasa SANTAI, SERU, dan berbau GAMIFIKASI (layaknya sistem level-up di dalam game atau achievement). Jangan kaku.
2. Analisa data yang diberikan: berapa banyak pesanan, seberapa banyak tugas yang sudah diselesaikan, dan produk apa yang mendominasi.
3. Berikan apresiasi jika penyelesaian tugas bagus, atau dorongan semangat jika masih banyak tugas menumpuk.
4. Berikan insight singkat mengenai produk terlaris atau tindakan (restock/dll) yang mungkin harus jadi prioritas besok.
5. Balas dalam HANYA 1-2 paragraf saja, langsung intinya tanpa awalan yang bertele-tele. Jangan gunakan markdown yang berlebihan, cukup teks tebal/bold saja jika perlu.
"""

def generate_daily_report_insight(user, target_date=None):
    if not target_date:
        target_date = timezone.now().date()
        
    # Get all extractions for the day to count orders and items
    extractions = ExtractionResult.objects.filter(
        screenshot__user=user,
        processed_at__date=target_date
    )
    
    total_orders = 0
    product_summary = {}
    
    for ext in extractions:
        # Assuming we can get items from narrative or items logic
        # For simplicity, we just count extractions related to orders
        if ext.screenshot.tag in ['order_list', 'order_detail']:
            items_qs = ext.items.all()
            if items_qs.exists():
                total_orders += items_qs.count()
                for item in items_qs:
                    product_name = item.product_name or 'Barang'
                    qty = int(item.quantity) if item.quantity else 1
                    if product_name in product_summary:
                        product_summary[product_name] += qty
                    else:
                        product_summary[product_name] = qty
            else:
                total_orders += 1
    
    # Get all tasks for the day
    tasks = Task.objects.filter(user=user, date=target_date)
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(is_completed=True).count()
    
    # Format data for AI
    ai_context = {
        "tanggal": str(target_date),
        "metrik_performa": {
            "total_order": total_orders,
            "total_tugas": total_tasks,
            "tugas_selesai": completed_tasks
        },
        "produk_terjual_hari_ini": product_summary
    }
    
    # Generate Insight from Groq
    api_key = os.getenv('GROQ_API_KEY')
    ai_insight_text = ""
    
    if api_key and total_tasks > 0:
        try:
            client = Groq(api_key=api_key)
            model_name = os.getenv('GROQ_TASK_MODEL', 'llama-3.3-70b-versatile')
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_REPORT},
                    {"role": "user", "content": json.dumps(ai_context)}
                ],
                model=model_name,
                temperature=0.7, # Higher temperature for more creative/fun tone
                max_tokens=1024,
            )
            ai_insight_text = chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Gagal generate report dari Groq: {str(e)}")
            ai_insight_text = "Sepertinya ada sedikit gangguan sinyal dengan asisten AI-mu hari ini. Tapi tetap semangat, selesaikan task yang ada!"
    else:
        ai_insight_text = "Belum ada misi yang dijalankan hari ini. Yuk, mulai ekstrak data pesananmu dan raih pencapaian baru!"
        
    # Save or update DailyReport
    report, created = DailyReport.objects.update_or_create(
        user=user,
        date=target_date,
        defaults={
            'total_orders': total_orders,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'ai_insight': ai_insight_text
        }
    )
    
    return report
