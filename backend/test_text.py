from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGBA', (2000, 2000), (255, 255, 255, 0))
d = ImageDraw.Draw(img)
font_size = 100
font = ImageFont.truetype("LiberationSans-Regular.ttf", font_size)

shadow=True
color="#ff0000"
content="and the traffic"

lines = content.split('\n')
y_offset = int(font_size * 0.2)
x_offset = int(font_size * 0.2)

for line in lines:
    if shadow:
        d.text((x_offset + max(1, int(font_size*0.05)), y_offset + max(1, int(font_size*0.05))), line, font=font, fill=(0,0,0, 200))
    d.text((x_offset, y_offset), line, font=font, fill=color)
    y_offset += int(font_size * 1.2)

bbox = img.getbbox()
if bbox:
    img = img.crop(bbox)

img.save("test_blob.png")
