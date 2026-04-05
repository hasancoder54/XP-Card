# Dosya: api/index.py
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import io
import os
from PIL import Image, ImageDraw, ImageFont

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. URL Parametrelerini Al
        query = parse_qs(urlparse(self.path).query)
        # Varsayılan değerler: 'Misafir' ve '0'
        isim = query.get("isim", ["Misafir"])[0][:15] # En fazla 15 karakter
        xp = query.get("xp", ["0"])[0]

        # 2. Dosya Yollarını Ayarla (Vercel ortamı için)
        # static klasörü ana dizinde olduğu için yukarı çıkıyoruz
        static_dir = os.path.join(os.getcwd(), 'static')
        bg_path = os.path.join(static_dir, 'bg.png')
        font_path = os.path.join(static_dir, 'font.ttf')

        # 3. Resmi Oluştur
        try:
            # Arka planı aç
            img = Image.open(bg_path).convert("RGBA")
            draw = ImageDraw.Draw(img)

            # Yazı tiplerini yükle (Hata oluşursa varsayılanı kullan)
            try:
                # İsim için büyük font
                font_isim = ImageFont.truetype(font_path, 36)
                # XP için orta font
                font_xp = ImageFont.truetype(font_path, 24)
            except IOError:
                font_isim = font_xp = ImageFont.load_default()

            # Metin Renkleri (Beyaz)
            renk = (255, 255, 255)

            # Yazıları Çiz (Konumları 600x200'e göre ayarlandı)
            # İsim (Soldan 40px, Üstten 40px)
            draw.text((40, 40), f"{isim}", font=font_isim, fill=renk)
            
            # XP Barı (Çizim örneği)
            draw.rectangle([40, 100, 300, 110], fill=(100, 100, 100)) # Gri Bar
            # Basit XP doluluğu: XP'ye göre barı uzat (Max 260px)
            try:
                xp_int = min(int(xp), 1000) # Max 1000 XP varsayalım
                bar_width = int((xp_int / 1000) * 260)
                draw.rectangle([40, 100, 40 + bar_width, 110], fill=(0, 255, 100)) # Yeşil Bar
            except:
                pass # XP sayı değilse bar çizme

            # XP Metni
            draw.text((40, 120), f"XP: {xp}", font=font_xp, fill=renk)

            # 4. Resmi Yanıt Olarak Gönder
            byte_io = io.BytesIO()
            img.save(byte_io, 'PNG')
            byte_io.seek(0)

            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            # Tarayıcının resmi önbelleğe almaması için (İsteğe bağlı)
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(byte_io.read())

        except Exception as e:
            # Bir hata oluşursa hata mesajını dön
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Hata: {str(e)}".encode())

        return
