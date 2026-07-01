import os
for f in ["templates/factory_pos.html", "templates/admin.html", "templates/shop.html"]:
    if os.path.exists(f):
        t = open(f, encoding='utf-8').read()
        t = t.replace('src="/photos/{{ p.image_filename }}"', 'src="/photos/{{ p.image_filename }}?v=2"')
        t = t.replace('src="/photos/{{ product.image_filename }}"', 'src="/photos/{{ product.image_filename }}?v=2"')
        open(f, "w", encoding='utf-8').write(t)
print("Done")
