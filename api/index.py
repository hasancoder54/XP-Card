# Dosya: api/index.py
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import io
import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. URL Parametrelerini Al
        query = parse_qs(urlparse(self.path).query)
        isim = query.get("isim", ["Misafir"])[0][:15]
        xp = query.get("xp", ["0"])[0]
        avatar_url = query.get("avatar", [""])[0] # Avatar URL'si

        # 2. Dosya Yollarını Ayarla
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bg_path = os.path.join(current_dir, '..', 'static', 'bg.png')
        font_path = os.path.join(current_dir, '..', 'static', 'font.ttf')

        try:
            # 3. Ana Kartı ve Fontları Hazırla
            img = Image.open(bg_path).convert("RGBA")
            # Kart boyutu (varsayılan 600x200 varsayıyorum)
            W, H = img.size 
            draw = ImageDraw.Draw(img)

            try:
                font_isim = ImageFont.truetype(font_path, 30)
                font_xp = ImageFont.truetype(font_path, 20)
            except IOError:
                font_isim = font_xp = ImageFont.load_default()

            # --- A. AVATARI ORTAYA YERLEŞTİRME VE DAİRE YAPMA ---
            avatar_size = 80 # Avatarın çapı
            
            if avatar_url:
                try:
                    # Avatarı indir
                    response = requests.get(avatar_url, stream=True, timeout=5)
                    response.raise_for_status()
                    avatar_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
                    
                    # Avatarı yeniden boyutlandır
                    avatar_img = avatar_img.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
                    
                    # Daire maskesi oluştur
                    mask = Image.new('L', (avatar_size, avatar_size), 0)
                    draw_mask = ImageDraw.Draw(mask)
                    draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                    
                    # Maskeyi uygula
                    output_avatar = ImageOps.fit(avatar_img, mask.size, centering=(0.5, 0.5))
                    output_avatar.putalpha(mask)
                    
                    # Avatarı kartın tam ortasına yapıştır
                    # (Genişlik/2 - Çap/2, Yükseklik/2 - Çap/2 - Biraz yukarı)
                    avatar_x = int((W / 2) - (avatar_size / 2))
                    avatar_y = int((H / 2) - (avatar_size / 2) - 20)
                    img.paste(output_avatar, (avatar_x, avatar_y), output_avatar)
                    
                except Exception as avatar_error:
                    # Avatar yüklenemezse hata logu yaz ama devam et
                    print(f"Avatar Hatası: {avatar_error}")
            # --- AVATAR BİTTİ ---


            # --- B. METİNLERİ ORTALAMA ---
            # İsim (Avatarın hemen altına)
            name_text = f"{isim}"
            
            # Pillow 10+ için metin boyutu hesaplama
            if hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), name_text, font=font_isim)
                name_w = bbox[2] - bbox[0]
            else:
                name_w, _ = draw.textsize(name_text, font=font_isim)

            name_x = int((W / 2) - (name_w / 2))
            name_y = int((H / 2) + (avatar_size / 2) - 10) # Avatarın altında
            draw.text((name_x, name_y), name_text, font=font_isim, fill=(255, 255, 255))
            # --- METİN BİTTİ ---


            # --- C. YUVARLAK KÖŞELİ XP BARI (KAPSÜL) ---
            bar_w, bar_h = 300, 16 # Barın genişliği ve yüksekliği
            bar_x = int((W / 2) - (bar_w / 2)) # Barı ortala
            bar_y = name_y + 40 # İsmin altında

            # XP Hesaplama
            try:
                xp_int = min(int(xp), 1000) # Max 1000
                progress_w = int((xp_int / 1000) * bar_w)
            except:
                progress_w = 0

            # Arka plan barı (Koyu Gri, Yuvarlak)
            # Pillow rounded_rectangle kullanıyoruz (Pillow 8.2+)
            if hasattr(draw, 'rounded_rectangle'):
                # Arka Plan
                draw.rounded_rectangle(
                    [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], 
                    radius=bar_h/2, 
                    fill=(50, 50, 50)
                )
                # İlerleme Barı (Yeşil, Yuvarlak)
                if progress_w > bar_h: # En az yükseklik kadar doluysa yuvarla
                    draw.rounded_rectangle(
                        [bar_x, bar_y, bar_x + progress_w, bar_y + bar_h], 
                        radius=bar_h/2, 
                        fill=(0, 255, 100)
                    )
                elif progress_w > 0: # Çok az doluysa düz çiz (yuvarlama çirkin durur)
                     draw.rectangle(
                        [bar_x, bar_y, bar_x + progress_w, bar_y + bar_h], 
                        fill=(0, 255, 100)
                    )
            else:
                # Pillow eskiyse düz çiz
                draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(50, 50, 50))
                draw.rectangle([bar_x, bar_y, bar_x + progress_w, bar_y + bar_h], fill=(0, 255, 100))

            # XP Metni (Barın yanına veya altına)
            xp_text = f"{xp} XP"
            draw.text((bar_x + bar_w + 10, bar_y - 3), xp_text, font=font_xp, fill=(200, 200, 200))
            # --- XP BAR BİTTİ ---


            # 4. Resmi Yanıt Olarak Gönder
            byte_io = io.BytesIO()
            img.save(byte_io, 'PNG')
            byte_io.seek(0)

            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(byte_io.read())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Hata: {str(e)}".encode())

        return
