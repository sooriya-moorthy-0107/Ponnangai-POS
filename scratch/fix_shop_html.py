import re

with open(r"templates\shop.html", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the first addToCart call
content = re.sub(
    r"onclick=\"addToCart\(\{\{ product\.id \}\}, '\{\{ product\.name \| replace\(\"'\", \"\\\\'\"\)\ \}\}', \{\{ product\.price \}\}, \{\{ product\.stock \}\}\)\"",
    r"onclick=\"addToCart({{ product.id }}, '{{ product.name | replace(\"'\", \"\\\\'\") }}', {{ product.price }}, {{ product.stock }}, '{{ product.product_type }}', '{{ product.unit }}')\"",
    content
)

# Fix the second addToCart call in JS
content = re.sub(
    r"addToCart\(\$\{product\.id\}, '\$\{escapedName\}', \$\{product\.price\}, \$\{product\.stock\}\)",
    r"addToCart(${product.id}, '${escapedName}', ${product.price}, ${product.stock}, '${product.product_type || \'solid\'}', '${product.unit || \'Pcs\'}')",
    content
)

with open(r"templates\shop.html", "w", encoding="utf-8") as f:
    f.write(content)
