# Dosya adı: api/index.py
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import io
import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

class handler(BaseHTTPRequestHandler):
    def hex_to_rgb(self, hex_str):
        hex_str = hex_str.lstrip('#')
        try:
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        except:
            return (0, 255, 106) # Hata olursa varsayılan yeşil

    def do_GET(self):
        # 1. PARAMETRELERİ AL
        query = parse_qs(urlparse(self.path).query)
        isim = query.get("isim", ["Misafir"])[0][:15]
        xp_str = query.get("xp", ["0"])[0]
        avatar_url = query.get("avatar", [""])[0]
        user_color_hex = query.get("renk", ["00ff6a"])[0]
        
        user_color = self.hex_to_rgb(user_color_hex)

        # 2. DOSYA YOLLARI
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bg_path = os.path.join(current_dir, '..', 'static', 'bg.png')
        font_path = os.path.join(current_dir, '..', 'static', 'font.ttf')

        try:
            # 3. ANA RESMİ VE ÇİZİMİ HAZIRLA
            img = Image.open(bg_path).convert("RGBA")
            W, H = img.size 
            draw = ImageDraw.Draw(img)

            try:
                font_isim = ImageFont.truetype(font_path, 30)
                font_xp = ImageFont.truetype(font_path, 18)
            except:
                font_isim = font_xp = ImageFont.load_default()

            # --- A. AVATAR ÇİZİMİ ---
            avatar_size = 80
            av_x, av_y = int((W/2)-(avatar_size/2)), 30
            
            if avatar_url:
                try:
                    res = requests.get(avatar_url, timeout=5)
                    av_img = Image.open(io.BytesIO(res.content)).convert("RGBA").resize((avatar_size, avatar_size))
                    mask = Image.new('L', (avatar_size, avatar_size), 0)
                    ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
                    av_img.putalpha(mask)
                    
                    # Avatar çerçevesi (Seçilen renkte)
                    draw.ellipse((av_x-3, av_y-3, av_x+avatar_size+3, av_y+avatar_size+3), outline=user_color, width=3)
                    img.paste(av_img, (av_x, av_y), av_img)
                except:
                    pass

            # --- B. İSİM ÇİZİMİ ---
            name_y = 120
            draw.text((W/2, name_y), isim, font=font_isim, fill=(255,255,255), anchor="mm")

            # --- C. XP BARI VE GLOW (KATMANLI SİSTEM) ---
            bar_w, bar_h = 300, 16
            bx, by = int((W/2)-(bar_w/2)), 150
            radius = bar_h // 2
            
            try:
                xp_val = int(xp_str)
                p_w = int((min(xp_val, 1000) / 1000) * bar_w)
            except:
                xp_val = 0
                p_w = 0

            # 1. Arka Plan Barı (Koyu Gri)
            draw.rounded_rectangle([bx, by, bx+bar_w, by+bar_h], radius=radius, fill=(20, 20, 20, 180))

            # 2. Glow ve Renkli Bar Katmanı (Ayrı Şeffaf Katman)
            if p_w > 0:
                # Parlama ve net bar için yeni katman
                bar_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                bar_draw = ImageDraw.Draw(bar_layer)
                
                # Glow (Bulanık kısım)
                # Genişlik radius*2'den küçükse hata vermemesi için min genişlik ayarı
                actual_p_w = max(p_w, radius * 2)
                bar_draw.rounded_rectangle([bx, by, bx+actual_p_w, by+bar_h], radius=radius, fill=user_color + (100,))
                bar_layer = bar_layer.filter(ImageFilter.GaussianBlur(radius=4))
                
                # Net Renkli Barı bulanık katmanın üstüne çiz
                bar_draw = ImageDraw.Draw(bar_layer)
                bar_draw.rounded_rectangle([bx, by, bx+p_w, by+bar_h], radius=radius, fill=user_color)
                
                # Katmanları Birleştir
                img = Image.alpha_composite(img, bar_layer)
                # Draw nesnesini ana resim için güncelle (yazı en üstte kalsın diye)
                draw = ImageDraw.Draw(img)

            # 3. XP Yazısı (En Üstte)
            xp_text = f"{xp_val} / 1000 XP"
            draw.text((W/2, by + bar_h/2), xp_text, font=font_xp, fill=(255, 255, 255), anchor="mm")

            # 4. YANIT GÖNDERME
            buf = io.BytesIO()
            img.save(buf, 'PNG')
            buf.seek(0)
            
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(buf.read())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Hata oluştu: {str(e)}".encode())

        return
