import os

files = ['admin.html', 'shop.html', 'factory_pos.html']

for file_name in files:
    file_path = os.path.join(os.path.dirname(__file__), 'templates', file_name)
    if not os.path.exists(file_path):
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace \' with '
    content = content.replace("\\'", "'")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
print("Removed escaped quotes")
