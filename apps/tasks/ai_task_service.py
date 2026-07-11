import os
import json
from groq import Groq
from django.utils import timezone
from ..extraction.models import ExtractedItem
from ..tasks.models import Task

SYSTEM_PROMPT = """Kamu adalah 'SellShoot Operational Manager', asisten cerdas untuk penjual online (seller).
Tugasmu adalah menganalisis data riwayat aktivitas/pesanan hari ini, lalu menyusun DAFTAR TUGAS (To-Do List) yang harus diselesaikan oleh seller.

ATURAN:
1. Kelompokkan pesanan yang sama dari platform yang sama menjadi satu tugas (misal: "Proses 5 pesanan Kemeja Flanel dari Shopee").
2. Berikan prioritas "urgent" untuk pesanan yang perlu segera diproses atau chat keluhan pelanggan.
3. Berikan prioritas "normal" untuk tugas operasional standar.
4. JANGAN membuat tugas untuk pesanan yang statusnya sudah "selesai" atau "dibatalkan", kecuali ada catatan khusus.
5. Wajib mengembalikan respons dalam format JSON murni sesuai skema berikut. JANGAN MENGEMBALIKAN TEKS LAIN.

SKEMA JSON:
{
  "tasks": [
    {
      "title": "string (Singkat, jelas, maks 60 karakter)",
      "description": "string (Penjelasan detail jika perlu)",
      "category": "order" | "restock" | "reply_chat" | "packing" | "other",
      "priority": "urgent" | "normal" | "low",
      "platform": "shopee" | "tokopedia" | "instagram" | "semua"
    }
  ]
}"""

def generate_tasks_from_verified_data(user, date=None):
    if not date:
        date = timezone.now().date()
        
    # 1. Kumpulkan semua extracted item yang sudah diverifikasi hari itu
    items = ExtractedItem.objects.filter(
        extraction_result__screenshot__user=user,
        extraction_result__processed_at__date=date,
        is_verified=True
    ).select_related('extraction_result__screenshot')
    
    if not items.exists():
        return {"success": True, "count": 0, "message": "Tidak ada data terverifikasi untuk diproses."}
        
    # 2. Format data untuk AI
    data_hari_ini = []
    for item in items:
        # Hanya masukkan item yang belum selesai
        if item.status.lower() not in ['selesai', 'dibatalkan']:
            data_hari_ini.append({
                "produk": item.product_name,
                "qty": item.quantity or 1,
                "status": item.status,
                "platform": item.extraction_result.screenshot.platform,
                "catatan": item.notes
            })
            
    if not data_hari_ini:
        return {"success": True, "count": 0, "message": "Semua pesanan sudah selesai/dibatalkan."}
        
    user_prompt = {
        "tanggal": str(date),
        "data_hari_ini": data_hari_ini
    }
    
    # 3. Panggil Groq API
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY tidak ditemukan di environment variables")
        
    client = Groq(api_key=api_key)
    
    model_name = os.getenv('GROQ_TASK_MODEL', 'llama-3.3-70b-versatile')
    
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_prompt)}
        ],
        model=model_name,
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    response_text = chat_completion.choices[0].message.content
    try:
        result_data = json.loads(response_text)
    except Exception as e:
        raise Exception(f"Gagal parse JSON dari Groq: {str(e)}")
        
    tasks_to_create = result_data.get('tasks', [])
    
    # 4. Hapus task yang belum selesai di hari yang sama agar tidak menumpuk duplikat saat di-generate ulang
    Task.objects.filter(user=user, date=date, is_completed=False).delete()
    
    # 5. Simpan ke database
    created_tasks = []
    for task_data in tasks_to_create:
        category = task_data.get('category', 'other')
        if category not in [c[0] for c in Task.CATEGORY_CHOICES]:
            category = 'other'
            
        priority = task_data.get('priority', 'normal')
        if priority not in [p[0] for p in Task.PRIORITY_CHOICES]:
            priority = 'normal'
            
        task = Task.objects.create(
            user=user,
            title=task_data.get('title', 'Tugas Tanpa Judul')[:255],
            description=task_data.get('description', ''),
            category=category,
            priority=priority,
            platform=task_data.get('platform', 'semua')[:50],
            date=date
        )
        created_tasks.append(task)
        
    return {"success": True, "count": len(created_tasks), "tasks": created_tasks}
