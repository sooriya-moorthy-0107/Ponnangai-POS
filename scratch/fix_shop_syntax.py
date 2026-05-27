with open("templates/shop.html", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace(r'onclick=\"addToCart(', 'onclick="addToCart(')
c = c.replace(r"')\"", r"')\"")  # This doesn't seem right
# Actually, the string ends with `')\"`. Let's just fix the whole string.

import re
# The broken string looks like:
# onclick=\"addToCart({{ product.id }}, '{{ product.name | replace(\"'\", \"\\'\") }}', {{ product.price }}, {{ product.stock }}, '{{ product.product_type }}', '{{ product.unit }}')\"
# We want to change it to:
# onclick="addToCart({{ product.id }}, '{{ product.name | replace("'", "\'") }}', {{ product.price }}, {{ product.stock }}, '{{ product.product_type }}', '{{ product.unit }}')"

target = r"onclick=\\\"addToCart\(\{\{ product.id \}\}, '\{\{ product.name \| replace\(\"'\", \"\\'\"\) \}\}', \{\{ product.price \}\}, \{\{ product.stock \}\}, '\{\{ product.product_type \}\}', '\{\{ product.unit \}\}'\)\\\""
# Wait, let's just do simple replacements.
c = c.replace('onclick=\\"addToCart', 'onclick="addToCart')
c = c.replace("}}')\\\"", "}}')\"")

with open("templates/shop.html", "w", encoding="utf-8") as f:
    f.write(c)
