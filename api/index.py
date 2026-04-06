# Dosya: api/index.py
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import io
import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

class handler(BaseHTTPRequestHandler):
    def hex_to_rgb(self, hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        isim = query.get("isim", ["Misafir"])[0][:15]
        xp = query.get("xp", ["0"])[0]
        avatar_url = query.get("avatar", [""])[0]
        user_color_hex = query.get("renk", ["00ff6a"])[0] # Varsayılan neon yeşil
        
        try:
            user_color = self.hex_to_rgb(user_color_hex)
        except:
            user_color = (0, 255, 106)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        bg_path = os.path.join(current_dir, '..', 'static', 'bg.png')
        font_path = os.path.join(current_dir, '..', 'static', 'font.ttf')

        try:
            img = Image.open(bg_path).convert("RGBA")
            W, H = img.size 
            draw = ImageDraw.Draw(img)

            try:
                font_isim = ImageFont.truetype(font_path, 30)
                font_xp = ImageFont.truetype(font_path, 18)
            except:
                font_isim = font_xp = ImageFont.load_default()

            # 1. AVATAR (Daire ve Kenarlık)
            avatar_size = 80
            if avatar_url:
                try:
                    res = requests.get(avatar_url, timeout=5)
                    av_img = Image.open(io.BytesIO(res.content)).convert("RGBA").resize((avatar_size, avatar_size))
                    mask = Image.new('L', (avatar_size, avatar_size), 0)
                    ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
                    av_img.putalpha(mask)
                    
                    av_x, av_y = int((W/2)-(avatar_size/2)), 30
                    # Avatarın etrafına ince bir renkli halka
                    draw.ellipse((av_x-3, av_y-3, av_x+avatar_size+3, av_y+avatar_size+3), outline=user_color, width=2)
                    img.paste(av_img, (av_x, av_y), av_img)
                except: pass

            # 2. İSİM
            name_y = 120
            draw.text((W/2, name_y), isim, font=font_isim, fill=(255,255,255), anchor="mm")

            # 3. YUVARLAK XP BARI VE GLOW
            bar_w, bar_h = 300, 14
            bx, by = int((W/2)-(bar_w/2)), 150
            
            try:
                xp_val = min(int(xp), 1000)
                p_w = int((xp_val / 1000) * bar_w)
            except: p_w = 0

            # Arka Plan Barı
            draw.rounded_rectangle([bx, by, bx+bar_w, by+bar_h], radius=7, fill=(30, 30, 30))

            if p_w > 5:
                # --- GLOW EFEKTİ ---
                # Parlama için ayrı bir katman oluşturuyoruz
                glow_layer = Image.new("RGBA", img.size, (0,0,0,0))
                glow_draw = ImageDraw.Draw(glow_layer)
                # Barın olduğu yere rengi çiz ve bulandır (blur)
                glow_draw.rounded_rectangle([bx, by, bx+p_w, by+bar_h], radius=7, fill=user_color + (100,))
                glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=4))
                img = Image.alpha_composite(img, glow_layer)
                
                # Asıl Renkli Bar
                draw.rounded_rectangle([bx, by, bx+p_w, by+bar_h], radius=7, fill=user_color)

            # XP Yazısı
            draw.text((bx + bar_w/2, by + 25), f"{xp} / 1000 XP", font=font_xp, fill=(200,200,200), anchor="mm")

            # YANIT GÖNDERME
            buf = io.BytesIO()
            img.save(buf, 'PNG')
            buf.seek(0)
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            self.wfile.write(buf.read())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
