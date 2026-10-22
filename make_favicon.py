from PIL import Image, ImageChops, ImageDraw

SIZE = 256
BORDER = 10
OFFSET = 14
RADIUS = 36
YELLOW = (255, 210, 63, 255)
BLACK = (16, 16, 16, 255)

logo = Image.open('static/logo.png').convert('RGBA')

canvas = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(canvas)

left, top = 6, 6
right, bottom = SIZE - 6 - OFFSET, SIZE - 6 - OFFSET

# hard shadow, then black outline, then yellow fill
draw.rounded_rectangle((left + OFFSET, top + OFFSET, right + OFFSET, bottom + OFFSET), RADIUS, fill=BLACK)
draw.rounded_rectangle((left, top, right, bottom), RADIUS, fill=BLACK)
inner = (left + BORDER, top + BORDER, right - BORDER, bottom - BORDER)
draw.rounded_rectangle(inner, RADIUS - BORDER, fill=YELLOW)

# icon, slightly enlarged and clipped to the yellow square
inner_width = inner[2] - inner[0]
art_size = int(inner_width * 1.08)
art = logo.resize((art_size, art_size), Image.LANCZOS)
layer = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
x = (inner[0] + inner[2]) // 2 - art_size // 2
y = (inner[1] + inner[3]) // 2 - art_size // 2
layer.paste(art, (x, y), art)

mask = Image.new('L', (SIZE, SIZE), 0)
ImageDraw.Draw(mask).rounded_rectangle(inner, RADIUS - BORDER, fill=255)
layer.putalpha(ImageChops.multiply(layer.getchannel('A'), mask))

canvas = Image.alpha_composite(canvas, layer)
canvas.save('static/favicon.png')
print('Saved static/favicon.png')

