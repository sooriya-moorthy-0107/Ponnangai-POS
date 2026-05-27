import sys
import re

# Update admin.html
with open(r"templates\admin.html", "r", encoding="utf-8") as f:
    admin_content = f.read()

# 1. Remove factory session reports block
admin_content = re.sub(
    r'<!-- Factory Shifts & Stock Reconciliation Reports -->.*?</div>\s*</div>\s*<!-- Shop Analytics Modal -->',
    '</div>\n    <!-- Shop Analytics Modal -->',
    admin_content,
    flags=re.DOTALL
)

# 2. Fix Stock Display
stock_display_target = """                                        <td>
                                            {% if sk.role == 'Factory' %}
                                            <span style="color: #718096; font-style: italic;">N/A (Shift-Based)</span>
                                            {% else %}
                                            <span style="{% if stk < 10 %}color: var(--destructive); font-weight: bold;{% endif %}">
                                                {{ stk }}
                                            </span>
                                            {% endif %}
                                        </td>"""
stock_display_replacement = """                                        <td>
                                            <span style="{% if stk < 10 %}color: var(--destructive); font-weight: bold;{% endif %}">
                                                {{ stk }}
                                            </span>
                                        </td>"""
admin_content = admin_content.replace(stock_display_target, stock_display_replacement)

# 3. Fix Update Stock block
update_stock_target = """                                        <td>
                                            {% if sk.role == 'Factory' %}
                                            <span style="color: #718096; font-style: italic;">Factory session balance</span>
                                            {% else %}
                                            <div style="display: flex; gap: 4px; max-width: 150px;">
                                                <input type="number" id="stock-{{ sk.id }}-{{ product.id }}" value="{{ stk }}"
                                                    style="margin-bottom: 0; padding: 6px;">
                                                <button class="btn btn-small"
                                                    onclick="updateStock({{ sk.id }}, {{ product.id }})">Save</button>
                                            </div>
                                            {% endif %}
                                        </td>"""
update_stock_replacement = """                                        <td>
                                            <div style="display: flex; gap: 4px; max-width: 150px;">
                                                <input type="number" id="stock-{{ sk.id }}-{{ product.id }}" value="{{ stk }}"
                                                    style="margin-bottom: 0; padding: 6px;">
                                                <button class="btn btn-small"
                                                    onclick="updateStock({{ sk.id }}, {{ product.id }})">Save</button>
                                            </div>
                                        </td>"""
admin_content = admin_content.replace(update_stock_target, update_stock_replacement)

# 4. Fix Initial Stock Input block
initial_stock_target = """<input type="number" id="new-product-stock-{{ sk.id }}" placeholder="0" {% if sk.role == 'Factory' %}value="0" disabled title="Stock managed via morning opening balance"{% endif %} style="margin-bottom: 0;">"""
initial_stock_replacement = """<input type="number" id="new-product-stock-{{ sk.id }}" placeholder="0" style="margin-bottom: 0;">"""
admin_content = admin_content.replace(initial_stock_target, initial_stock_replacement)

# 5. Remove price disabled block
price_target = """<input type="number" id="new-product-price-{{ sk.id }}" placeholder="0.00" step="0.01" value="{% if sk.role == 'Factory' %}0{% endif %}" style="margin-bottom: 0;">"""
price_replacement = """<input type="number" id="new-product-price-{{ sk.id }}" placeholder="0.00" step="0.01" style="margin-bottom: 0;">"""
admin_content = admin_content.replace(price_target, price_replacement)

price_label_target = """<div style="flex: 1; min-width: 100px; {% if sk.role == 'Factory' %}display: none;{% endif %}">"""
price_label_replacement = """<div style="flex: 1; min-width: 100px;">"""
admin_content = admin_content.replace(price_label_target, price_label_replacement)

with open(r"templates\admin.html", "w", encoding="utf-8") as f:
    f.write(admin_content)

# Update factory_pos.html
with open(r"templates\factory_pos.html", "r", encoding="utf-8") as f:
    pos_content = f.read()

# 1. Remove end day button
end_day_target = """            <a href="/factory/shift" class="btn btn-destructive btn-small" style="text-decoration: none;">End Day &
                Close Shift</a>"""
pos_content = pos_content.replace(end_day_target, "")
end_day_target_singleline = """            <a href="/factory/shift" class="btn btn-destructive btn-small" style="text-decoration: none;">End Day & Close Shift</a>"""
pos_content = pos_content.replace(end_day_target_singleline, "")

with open(r"templates\factory_pos.html", "w", encoding="utf-8") as f:
    f.write(pos_content)
