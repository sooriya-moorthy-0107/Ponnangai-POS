import re
import os

files = ['admin.html', 'shop.html', 'factory_pos.html']

for file_name in files:
    file_path = os.path.join(os.path.dirname(__file__), 'templates', file_name)
    if not os.path.exists(file_path):
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix Javascript onclicks with unquoted jinja arguments
    content = re.sub(r'onclick="viewShopAnalytics\(\{\{\s*([^}]+)\s*\}\}\)"',
                     r'onclick="viewShopAnalytics(\'{{\1}}\')" ', content)

    content = re.sub(r'onclick=\'event\.stopPropagation\(\);\s*hardDeleteUser\(\{\{\s*([^}]+)\s*\}\},\s*\{\{\s*([^}]+)\s*\|\s*tojson\s*\}\}\)\'',
                     r'onclick="event.stopPropagation(); hardDeleteUser(\'{{\1}}\', \'{{\2}}\')"', content)

    content = re.sub(r'onclick=\'openEditUserModal\(\{\{\s*([^}]+)\s*\}\},\s*\{\{\s*([^}]+)\s*\|\s*tojson\s*\}\},\s*\{\{\s*([^}]+)\s*\|\s*tojson\s*\}\}\)\'',
                     r'onclick="openEditUserModal(\'{{\1}}\', \'{{\2}}\', \'{{\3}}\')"', content)

    content = re.sub(r'onclick=\'deleteUser\(\{\{\s*([^}]+)\s*\}\},\s*\{\{\s*([^}]+)\s*\|\s*tojson\s*\}\}\)\'',
                     r'onclick="deleteUser(\'{{\1}}\', \'{{\2}}\')"', content)

    content = re.sub(r'onclick=\'restoreUser\(\{\{\s*([^}]+)\s*\}\},\s*\{\{\s*([^}]+)\s*\|\s*tojson\s*\}\}\)\'',
                     r'onclick="restoreUser(\'{{\1}}\', \'{{\2}}\')"', content)

    content = re.sub(r'onclick=\'openEditProductModal\(\{\{\s*product\.id\s*\}\},\s*\{\{\s*product\.name\s*\|\s*tojson\s*\}\},\s*\{\{\s*([^}]+)\s*\}\},\s*\{\{\s*([^}]+)\s*\}\}\)\'',
                     r'onclick="openEditProductModal(\'{{ product.id }}\', \'{{ product.name }}\', \'{{\1}}\', \'{{\2}}\')"', content)

    content = re.sub(r'onclick=\'deleteProduct\(\{\{\s*product\.id\s*\}\},\s*\{\{\s*product\.name\s*\|\s*tojson\s*\}\}\)\'',
                     r'onclick="deleteProduct(\'{{ product.id }}\', \'{{ product.name }}\')"', content)

    content = re.sub(r'onclick=\'uploadDirectPhoto\(this,\s*\{\{\s*product\.id\s*\}\}\)\'',
                     r'onclick="uploadDirectPhoto(this, \'{{ product.id }}\')"', content)

    content = re.sub(r'onclick="updateStock\(\{\{\s*([^}]+)\s*\}\},\s*\{\{\s*product\.id\s*\}\}\)"',
                     r'onclick="updateStock(\'{{\1}}\', \'{{ product.id }}\')" ', content)

    content = re.sub(r'onclick="toggleAddProductForm\(\{\{\s*([^}]+)\s*\}\}\)"',
                     r'onclick="toggleAddProductForm(\'{{\1}}\')" ', content)

    content = re.sub(r'onclick="addNewProductToShop\(\{\{\s*([^}]+)\s*\}\}\)"',
                     r'onclick="addNewProductToShop(\'{{\1}}\')" ', content)

    content = re.sub(r'onclick="toggleBulkUploadForm\(\{\{\s*([^}]+)\s*\}\}\)"',
                     r'onclick="toggleBulkUploadForm(\'{{\1}}\')" ', content)

    content = re.sub(r'onclick="uploadBulkProductsToShop\(\{\{\s*([^}]+)\s*\}\}\)"',
                     r'onclick="uploadBulkProductsToShop(\'{{\1}}\')" ', content)

    content = re.sub(r'onclick="toggleBulkStockForm\(\{\{\s*([^}]+)\s*\}\}\)"',
                     r'onclick="toggleBulkStockForm(\'{{\1}}\')" ', content)

    content = re.sub(r'onclick="downloadStockTemplate\(\{\{\s*([^}]+)\s*\}\}\)"',
                     r'onclick="downloadStockTemplate(\'{{\1}}\')" ', content)

    content = re.sub(r'onclick="uploadBulkStockToShop\(\{\{\s*([^}]+)\s*\}\}\)"',
                     r'onclick="uploadBulkStockToShop(\'{{\1}}\')" ', content)

    content = re.sub(r'onchange="uploadDirectPhoto\(this,\s*\{\{\s*product\.id\s*\}\}\)"',
                     r'onchange="uploadDirectPhoto(this, \'{{ product.id }}\')" ', content)

    # Some switchShop fixes
    content = re.sub(r'onclick="switchShop\(\{\{\s*([^}]+)\s*\}\}\)"',
                     r'onclick="switchShop(\'{{\1}}\')" ', content)

    content = re.sub(r'onchange="window\.location\.href=\'/shop\?shopkeeper_id=\'\+this\.value;"',
                     r'onchange="window.location.href=\'/shop?shopkeeper_id=\' + this.value;"', content)

    # Some basic CSS inline style fixes 
    content = re.sub(r'style="\{\%\s*if\s*stk\s*<\s*10\s*\%\}\s*color:\s*var\(--destructive\);\s*font-weight:\s*bold;\s*\{\%\s*endif\s*\%\}"',
                 r'{% if stk < 10 %}style="color: var(--destructive); font-weight: bold;"{% endif %}', content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
print("Fixed jinja parser errors in all templates")
