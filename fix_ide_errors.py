import re
import os

file_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin.html')
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix CSS styles with jinja inside
content = re.sub(r'style="border-color:\s*\{\%\s*if\s*low_stock_alerts\|length\s*>\s*0\s*\%\}\s*var\(--destructive\)\s*\{\%\s*else\s*\%\}\s*#E2E8F0\s*\{\%\s*endif\s*\%\};"',
                 r'{% if low_stock_alerts|length > 0 %}style="border-color: var(--destructive);"{% else %}style="border-color: #E2E8F0;"{% endif %}', content)

content = re.sub(r'style="color:\s*\{\%\s*if\s*low_stock_alerts\|length\s*>\s*0\s*\%\}\s*var\(--destructive\)\s*\{\%\s*else\s*\%\}\s*var\(--primary\)\s*\{\%\s*endif\s*\%\};"',
                 r'{% if low_stock_alerts|length > 0 %}style="color: var(--destructive);"{% else %}style="color: var(--primary);"{% endif %}', content)

content = re.sub(r'style="\{\%\s*if\s*loop\.index\s*!=\s*1\s*\%\}\s*display:\s*none;\s*\{\%\s*endif\s*\%\}""',
                 r'{% if loop.index != 1 %}style="display: none;"{% endif %}', content)
# Sometimes only 1 quote exists at end
content = re.sub(r'style="\{\%\s*if\s*loop\.index\s*!=\s*1\s*\%\}\s*display:\s*none;\s*\{\%\s*endif\s*\%\}"',
                 r'{% if loop.index != 1 %}style="display: none;"{% endif %}', content)

content = re.sub(r'style="\{\%\s*if\s*stk\s*<\s*10\s*\%\}\s*color:\s*var\(--destructive\);\s*font-weight:\s*bold;\s*\{\%\s*endif\s*\%\}"',
                 r'{% if stk < 10 %}style="color: var(--destructive); font-weight: bold;"{% endif %}', content)

# Fix Javascript onclicks with unquoted jinja arguments
content = re.sub(r'onclick="viewShopAnalytics\(\{\{\s*([^}]+)\s*\}\}\)"',
                 r'onclick="viewShopAnalytics(\'{{\1}}\')" ', content)

# Handle single quote wrapped event.stopPropagation
content = re.sub(r'onclick=\'event\.stopPropagation\(\);\s*hardDeleteUser\(\{\{\s*sk\.id\s*\}\},\s*\{\{\s*sk\.username\s*\|\s*tojson\s*\}\}\)\'',
                 r'onclick="event.stopPropagation(); hardDeleteUser(\'{{ sk.id }}\', \'{{ sk.username }}\')"', content)

content = re.sub(r'onclick=\'openEditUserModal\(\{\{\s*sk\.id\s*\}\},\s*\{\{\s*sk\.username\s*\|\s*tojson\s*\}\},\s*\{\{\s*sk\.role\s*\|\s*tojson\s*\}\}\)\'',
                 r'onclick="openEditUserModal(\'{{ sk.id }}\', \'{{ sk.username }}\', \'{{ sk.role }}\')"', content)

content = re.sub(r'onclick=\'deleteUser\(\{\{\s*sk\.id\s*\}\},\s*\{\{\s*sk\.username\s*\|\s*tojson\s*\}\}\)\'',
                 r'onclick="deleteUser(\'{{ sk.id }}\', \'{{ sk.username }}\')"', content)

content = re.sub(r'onclick=\'restoreUser\(\{\{\s*sk\.id\s*\}\},\s*\{\{\s*sk\.username\s*\|\s*tojson\s*\}\}\)\'',
                 r'onclick="restoreUser(\'{{ sk.id }}\', \'{{ sk.username }}\')"', content)

content = re.sub(r'onclick=\'openEditProductModal\(\{\{\s*product\.id\s*\}\},\s*\{\{\s*product\.name\s*\|\s*tojson\s*\}\},\s*\{\{\s*stk\s*\}\},\s*\{\{\s*sk\.id\s*\}\}\)\'',
                 r'onclick="openEditProductModal(\'{{ product.id }}\', \'{{ product.name }}\', \'{{ stk }}\', \'{{ sk.id }}\')"', content)

content = re.sub(r'onclick=\'deleteProduct\(\{\{\s*product\.id\s*\}\},\s*\{\{\s*product\.name\s*\|\s*tojson\s*\}\}\)\'',
                 r'onclick="deleteProduct(\'{{ product.id }}\', \'{{ product.name }}\')"', content)

content = re.sub(r'onclick=\'uploadDirectPhoto\(this,\s*\{\{\s*product\.id\s*\}\}\)\'',
                 r'onclick="uploadDirectPhoto(this, \'{{ product.id }}\')"', content)

content = re.sub(r'onclick="updateStock\(\{\{\s*sk\.id\s*\}\},\s*\{\{\s*product\.id\s*\}\}\)"',
                 r'onclick="updateStock(\'{{ sk.id }}\', \'{{ product.id }}\')" ', content)

content = re.sub(r'onclick="toggleAddProductForm\(\{\{\s*sk\.id\s*\}\}\)"',
                 r'onclick="toggleAddProductForm(\'{{ sk.id }}\')" ', content)

content = re.sub(r'onclick="addNewProductToShop\(\{\{\s*sk\.id\s*\}\}\)"',
                 r'onclick="addNewProductToShop(\'{{ sk.id }}\')" ', content)

content = re.sub(r'onclick="toggleBulkUploadForm\(\{\{\s*sk\.id\s*\}\}\)"',
                 r'onclick="toggleBulkUploadForm(\'{{ sk.id }}\')" ', content)

content = re.sub(r'onclick="uploadBulkProductsToShop\(\{\{\s*sk\.id\s*\}\}\)"',
                 r'onclick="uploadBulkProductsToShop(\'{{ sk.id }}\')" ', content)

content = re.sub(r'onclick="toggleBulkStockForm\(\{\{\s*sk\.id\s*\}\}\)"',
                 r'onclick="toggleBulkStockForm(\'{{ sk.id }}\')" ', content)

content = re.sub(r'onclick="downloadStockTemplate\(\{\{\s*sk\.id\s*\}\}\)"',
                 r'onclick="downloadStockTemplate(\'{{ sk.id }}\')" ', content)

content = re.sub(r'onclick="uploadBulkStockToShop\(\{\{\s*sk\.id\s*\}\}\)"',
                 r'onclick="uploadBulkStockToShop(\'{{ sk.id }}\')" ', content)

content = re.sub(r'onchange="uploadDirectPhoto\(this,\s*\{\{\s*product\.id\s*\}\}\)"',
                 r'onchange="uploadDirectPhoto(this, \'{{ product.id }}\')" ', content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed admin.html jinja parser errors")
