import google.generativeai as genai
import os
import requests
from io import BytesIO
from PIL import Image

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
"""

# ── Schema JSON ──────────────────────────────────
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "screenshot_readable": {
            "type": "boolean",
            "description": "Apakah screenshot dapat dibaca dengan jelas"
        },
        "platform_detected": {
            "type": "string",
            "enum": ["shopee", "tokopedia", "instagram", "other", "unknown"],
            "description": "Platform yang terdeteksi dari tampilan UI screenshot"
        },
        "screenshot_type": {
            "type": "string",
            "enum": ["order_list", "order_detail", "product_stock", "chat", "content_performance", "other"],
            "description": "Jenis halaman yang di-screenshot"
        },
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "price": {"type": "number"},
                    "status": {
                        "type": "string",
                        "enum": ["perlu_tindakan", "diproses", "selesai", "dikirim", "dibatalkan", "lainnya"]
                    },
                    "order_id": {"type": "string"},
                    "buyer_name": {"type": "string"},
                    "notes": {"type": "string"},
                    "confidence": {
                        "type": "number",
                        "description": "Confidence score 0.0-1.0 seberapa yakin data ini benar"
                    }
                },
                "required": ["product_name", "confidence"]
            }
        },
        "overall_confidence": {
            "type": "number",
            "description": "Confidence keseluruhan untuk seluruh screenshot (0.0-1.0)"
        },
        "failure_reason": {
            "type": "string",
            "description": "Alasan jika screenshot gagal dibaca (opsional)"
        }
    },
    "required": ["screenshot_readable", "platform_detected", "screenshot_type", "items", "overall_confidence"]
}


def process_screenshot(screenshot_instance):
    """
    Memproses satu screenshot menggunakan Gemini Vision API.
    """
    from .models import ExtractionResult, ExtractedItem

    # Pastikan API key sudah dikonfigurasi. Kalau belum, konfigurasi di sini.
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY tidak ditemukan di environment variables")
    genai.configure(api_key=api_key)

    try:
        # 1. Download gambar dari UploadThing URL
        response = requests.get(screenshot_instance.image_url, timeout=30)
        response.raise_for_status()
        image_bytes = BytesIO(response.content)

        # 2. Upload ke Gemini sebagai inline data
        image = Image.open(image_bytes)

        # 3. Konfigurasi model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_INSTRUCTION,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=EXTRACTION_SCHEMA,
                temperature=0.1,  # Rendah → lebih deterministik & konsisten
            )
        )

        # 4. Kirim ke Gemini
        user_prompt = (
            f"Ekstrak semua data order/produk dari screenshot dashboard {screenshot_instance.platform} berikut. "
            f"Screenshot ini diupload oleh seller pada {screenshot_instance.uploaded_at.strftime('%Y-%m-%d %H:%M')}."
        )

        import json
        gemini_response = model.generate_content([user_prompt, image])
        result_data = json.loads(gemini_response.text)

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
                is_verified=item_data.get('confidence', 0.0) >= 0.85,  # Auto-verify jika tinggi
            )

        # 7. Update status screenshot
        if not result_data.get('screenshot_readable', True):
            screenshot_instance.status = 'failed'
        else:
            screenshot_instance.status = 'processed'
        screenshot_instance.save()

        return extraction_result

    except Exception as e:
        # Tandai screenshot sebagai gagal
        screenshot_instance.status = 'failed'
        screenshot_instance.save()
        raise e
