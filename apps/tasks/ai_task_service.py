import os
import json
from groq import Groq
from django.utils import timezone
from ..extraction.models import ExtractionResult
from ..tasks.models import Task

SYSTEM_PROMPT_FLOW_1 = """Kamu adalah 'SellShoot Operational Manager'. Tugasmu menganalisis narasi ekstrasi gambar DAFTAR/DETAIL PESANAN lintas platform (Cross-Platform Order Management).
ATURAN:
1. Wajib mengonsolidasikan semua pesanan menjadi sesedikit mungkin task (ideal 1 task utama untuk packing/pengiriman).
2. Di dalam kolom 'description', gunakan format MARKDOWN LIST bersarang (poin dan sub-poin) untuk merinci pesanan.
3. Susun hierarki deskripsi wajib seperti ini:
   - Nama Produk / Kategori
     - Varian (Ukuran/Warna) | Qty | Asal Platform (Shopee, Tokopedia, dll)
       - *Catatan/Pesan Khusus:* (Tampilkan jika ada pesanan khusus dari pembeli)
4. Gabungkan informasi dari Daftar Pesanan dan Detail Pesanan menjadi satu kesatuan (Cross-Platform).
5. Wajib mengembalikan respons dalam format JSON murni.
SKEMA JSON:
{
  "tasks": [
    {
      "title": "Semua barang yang perlu dikirimkan (atau judul relevan lain)",
      "description": "Deskripsi berbasis Markdown point & sub-point yang mengelompokkan produk, varian, kuantitas, platform, dan catatan khusus.",
      "category": "order",
      "priority": "urgent" | "normal" | "low",
      "platform": "semua"
    }
  ]
}"""

SYSTEM_PROMPT_FLOW_2 = """Kamu adalah 'SellShoot Operational Manager'. Tugasmu menganalisis narasi ekstrasi gambar STOK PRODUK dan CHAT PELANGGAN.
ATURAN:
1. Analisa apakah ada stok yang perlu diupdate/restock, atau komplain pelanggan yang perlu segera dibalas.
2. Wajib mengembalikan respons dalam format JSON murni.
SKEMA JSON:
{
  "tasks": [
    {
      "title": "Singkat dan jelas",
      "description": "Deskripsi detail tentang stok yang habis atau keluhan pelanggan",
      "category": "restock" | "reply_chat" | "other",
      "priority": "urgent" | "normal" | "low",
      "platform": "shopee" | "tokopedia" | "instagram" | "semua"
    }
  ]
}"""

def call_groq_for_tasks(system_prompt, user_data_json):
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY tidak ditemukan di environment variables")
        
    client = Groq(api_key=api_key)
    model_name = os.getenv('GROQ_TASK_MODEL', 'llama-3.3-70b-versatile')
    
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_data_json}
        ],
        model=model_name,
        temperature=0.1,
        max_tokens=4096,
        response_format={"type": "json_object"}
    )
    
    response_text = chat_completion.choices[0].message.content
    try:
        return json.loads(response_text).get('tasks', [])
    except Exception as e:
        print(f"Gagal parse JSON dari Groq: {str(e)}")
        return []

def generate_tasks_from_verified_data(user, date=None):
    if not date:
        date = timezone.now().date()
        
    # Ambil SEMUA ExtractionResult hari ini untuk user (bypassing verification per user requirement)
    extractions = ExtractionResult.objects.filter(
        screenshot__user=user,
        processed_at__date=date
    ).select_related('screenshot')
    
    if not extractions.exists():
        return {"success": True, "count": 0, "message": "Tidak ada data ekstraksi hari ini."}
        
    data_flow_1 = []
    data_flow_2 = []
    
    for ext in extractions:
        narrative = ext.narrative or "Tidak ada narasi eksplisit."
        if ext.screenshot.tag in ['order_list', 'order_detail']:
            data_flow_1.append({"platform": ext.screenshot.platform, "narasi": narrative})
        elif ext.screenshot.tag in ['product_stock', 'chat']:
            data_flow_2.append({"platform": ext.screenshot.platform, "narasi": narrative})

    tasks_to_create = []
    
    # Process Flow 1 (Order Management)
    if data_flow_1:
        user_prompt_1 = json.dumps({"tanggal": str(date), "data_pesanan": data_flow_1})
        tasks_to_create.extend(call_groq_for_tasks(SYSTEM_PROMPT_FLOW_1, user_prompt_1))
        
    # Process Flow 2 (Inventory & CS)
    if data_flow_2:
        user_prompt_2 = json.dumps({"tanggal": str(date), "data_operasional": data_flow_2})
        tasks_to_create.extend(call_groq_for_tasks(SYSTEM_PROMPT_FLOW_2, user_prompt_2))
        
    # Hapus task yang belum selesai di hari yang sama agar tidak duplikat
    Task.objects.filter(user=user, date=date, is_completed=False).delete()
    
    # Simpan ke database
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
        
    return {"success": True, "count": len(created_tasks), "tasks": [t.title for t in created_tasks]}
