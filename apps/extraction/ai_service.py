import os
import requests
import base64
import json
from groq import Groq

# ── System Instruction ──────────────
SYSTEM_INSTRUCTION = """
Kamu adalah asisten AI untuk aplikasi SellShoot, sebuah operational co-pilot untuk
seller marketplace Indonesia. Tugasmu adalah mengekstrak informasi dari screenshot
dashboard seller marketplace (Shopee, Tokopedia, Instagram, dll).

ATURAN KETAT:
1. Hanya ekstrak data yang BENAR-BENAR terlihat di screenshot. JANGAN mengarang data.
2. Jika sebagian teks tidak terbaca jelas, tandai dengan confidence rendah (< 0.5).
3. Jika screenshot tidak berisi data order/produk yang relevan, kembalikan items kosong
   dan set screenshot_readable = false.
4. Semua harga dalam Rupiah (tanpa "Rp" prefix, hanya angka).
5. Nama produk ditulis PERSIS seperti yang terlihat di screenshot, jangan disingkat/ubah.
6. KAMU WAJIB MENGEMBALIKAN OUTPUT DALAM FORMAT JSON STRICT BERDASARKAN SKEMA BERIKUT.
   JANGAN MENGEMBALIKAN APAPUN SELAIN JSON OBJECT (TANPA MARKDOWN ```json).

SKEMA JSON YANG DIHARAPKAN:
{
  "screenshot_readable": boolean,
  "platform_detected": "shopee" | "tokopedia" | "instagram" | "other" | "unknown",
  "screenshot_type": "order_list" | "order_detail" | "product_stock" | "chat" | "content_performance" | "other",
  "overall_confidence": float (0.0-1.0),
  "items": [
    {
      "product_name": string,
      "quantity": integer,
      "price": float,
      "status": "perlu_tindakan" | "diproses" | "selesai" | "dikirim" | "dibatalkan" | "lainnya",
      "order_id": string,
      "buyer_name": string,
      "notes": string,
      "confidence": float (0.0-1.0)
    }
  ]
}
"""

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
        user_prompt = (
            f"Ekstrak semua data order/produk dari screenshot dashboard {screenshot_instance.platform} berikut. "
            f"Screenshot ini diupload pada {screenshot_instance.uploaded_at.strftime('%Y-%m-%d %H:%M')}. "
            "PENTING: Pastikan Anda hanya merespons dengan JSON Object murni."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_INSTRUCTION
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
