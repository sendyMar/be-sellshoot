import os
import requests
import base64
import json
from groq import Groq

# ── System Instructions ──────────────
BASE_JSON_SCHEMA = """
{
  "screenshot_readable": boolean,
  "platform_detected": "shopee" | "tokopedia" | "instagram" | "other" | "unknown",
  "overall_confidence": float (0.0-1.0),
  "narrative": "string (Berikan deskripsi detail tentang temuan dari gambar ini secara naratif. Jika ada hal yang perlu ditindaklanjuti seperti stok habis, pesanan urgent, atau komplain, jelaskan di sini.)",
  "items": [
    {
      "product_name": "string",
      "quantity": "integer",
      "price": "float",
      "status": "perlu_tindakan | diproses | selesai | dikirim | dibatalkan | lainnya",
      "order_id": "string",
      "buyer_name": "string",
      "notes": "string",
      "confidence": "float (0.0-1.0)"
    }
  ]
}
"""

PROMPTS = {
    'order_list': f"""Kamu adalah asisten AI untuk SellShoot. Tugasmu mengekstrak data dari screenshot DAFTAR PESANAN.
ATURAN KETAT:
1. Hanya ekstrak data yang BENAR-BENAR terlihat di screenshot. JANGAN mengarang data.
2. Isi atribut 'narrative' dengan analisa menyeluruh tentang daftar pesanan ini.
3. Semua harga dalam Rupiah (tanpa "Rp" prefix).
4. KAMU WAJIB MENGEMBALIKAN OUTPUT DALAM FORMAT JSON STRICT.
SKEMA JSON: {BASE_JSON_SCHEMA}""",

    'order_detail': f"""Kamu adalah asisten AI untuk SellShoot. Tugasmu mengekstrak data dari screenshot DETAIL PESANAN.
ATURAN KETAT:
1. Hanya ekstrak data yang BENAR-BENAR terlihat.
2. Isi atribut 'narrative' dengan detail penting seperti catatan khusus dari pembeli atau status pengiriman.
3. KAMU WAJIB MENGEMBALIKAN OUTPUT DALAM FORMAT JSON STRICT.
SKEMA JSON: {BASE_JSON_SCHEMA}""",

    'product_stock': f"""Kamu adalah asisten AI untuk SellShoot. Tugasmu mengekstrak data dari screenshot STOK PRODUK.
ATURAN KETAT:
1. Hanya ekstrak data yang BENAR-BENAR terlihat.
2. Isi atribut 'narrative' dengan temuan stok (misal: stok mana yang menipis atau habis).
3. KAMU WAJIB MENGEMBALIKAN OUTPUT DALAM FORMAT JSON STRICT.
SKEMA JSON: {BASE_JSON_SCHEMA}""",

    'chat': f"""Kamu adalah asisten AI untuk SellShoot. Tugasmu mengekstrak data dari screenshot CHAT PELANGGAN.
ATURAN KETAT:
1. Hanya ekstrak data yang BENAR-BENAR terlihat.
2. Isi atribut 'narrative' dengan inti percakapan, komplain, atau permintaan pelanggan.
3. KAMU WAJIB MENGEMBALIKAN OUTPUT DALAM FORMAT JSON STRICT.
SKEMA JSON: {BASE_JSON_SCHEMA}"""
}

def process_screenshot(screenshot_instance):
    """
    Memproses satu screenshot menggunakan Groq API (Llama 3.2 90B Vision).
    """
    from .models import ExtractionResult, ExtractedItem

    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY tidak ditemukan di environment variables")
        
    client = Groq(api_key=api_key)

    try:
        # 1. Download gambar dari UploadThing URL
        response = requests.get(screenshot_instance.image_url, timeout=30)
        response.raise_for_status()
        
        # 2. Konversi ke Base64 (Syarat wajib untuk Groq API Vision)
        image_content_type = response.headers.get('Content-Type', 'image/jpeg')
        base64_image = base64.b64encode(response.content).decode('utf-8')
        image_url_data = f"data:{image_content_type};base64,{base64_image}"

        # 3. Kirim ke Groq API
        tag = getattr(screenshot_instance, 'tag', 'order_list')
        system_instruction = PROMPTS.get(tag, PROMPTS['order_list'])

        user_prompt = (
            f"Ekstrak data dari screenshot {screenshot_instance.platform} berikut yang bertipe '{tag}'. "
            f"Screenshot ini diupload pada {screenshot_instance.uploaded_at.strftime('%Y-%m-%d %H:%M')}. "
            "PENTING: Pastikan Anda hanya merespons dengan JSON Object murni."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_instruction
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url_data,
                            },
                        },
                    ],
                }
            ],
            model="qwen/qwen3.6-27b",
            temperature=0.1,
            max_tokens=4096,
            response_format={"type": "json_object"}
        )

        # 4. Ambil dan parse JSON hasil Groq
        response_text = chat_completion.choices[0].message.content
        result_data = json.loads(response_text)

        # Menghandle apabila Llama membungkusnya dalam nested key tambahan (fallback)
        if "items" not in result_data:
            result_data["items"] = []
            for key, val in result_data.items():
                if isinstance(val, list):
                    result_data["items"] = val
                    break

        # 5. Simpan hasil ke database
        extraction_result = ExtractionResult.objects.create(
            screenshot=screenshot_instance,
            raw_ai_response=result_data,
            narrative=result_data.get('narrative', '')
        )

        # 6. Parse items ke ExtractedItem
        for item_data in result_data.get('items', []):
            ExtractedItem.objects.create(
                extraction_result=extraction_result,
                product_name=item_data.get('product_name', ''),
                quantity=item_data.get('quantity'),
                price=item_data.get('price'),
                status=item_data.get('status', 'lainnya'),
                order_id=item_data.get('order_id', ''),
                buyer_name=item_data.get('buyer_name', ''),
                notes=item_data.get('notes', ''),
                confidence=item_data.get('confidence', 0.0),
                is_verified=item_data.get('confidence', 0.0) >= 0.85,
            )

        # 7. Update status screenshot
        if not result_data.get('screenshot_readable', True):
            screenshot_instance.status = 'failed'
        else:
            screenshot_instance.status = 'processed'
        screenshot_instance.save()

        return extraction_result

    except Exception as e:
        screenshot_instance.status = 'failed'
        screenshot_instance.save()
        raise e
