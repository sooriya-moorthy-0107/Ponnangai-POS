import re
from sqlalchemy import create_engine, text

# 1. Update Database Schema
engine = create_engine('sqlite:///./pgdata/pos.db') # Wait, docker uses postgres!
# We will use main.py to execute the migration at startup.

# 2. Update main.py models and routes
with open("main.py", "r", encoding="utf-8") as f:
    main_py = f.read()

# Add column to model
main_py = main_py.replace('bottle_type = Column(String, nullable=True) # Type 1, Type 2, Type 3',
                          'bottle_type = Column(String, nullable=True) # Type 1, Type 2, Type 3\n    bottle_count = Column(Integer, default=0)')

# Add column in DB init
db_init_target = """        db_init.execute(text("ALTER TABLE products ADD COLUMN unit VARCHAR DEFAULT 'Pcs'"))
    except Exception:
        pass"""
db_init_replacement = """        db_init.execute(text("ALTER TABLE products ADD COLUMN unit VARCHAR DEFAULT 'Pcs'"))
    except Exception:
        pass
        
    try:
        db_init.execute(text("ALTER TABLE bill_items ADD COLUMN bottle_count INTEGER DEFAULT 0"))
        db_init.commit()
    except Exception:
        db_init.rollback()
        pass"""
if "bottle_count INTEGER" not in main_py:
    main_py = main_py.replace(db_init_target, db_init_replacement)

# Update BillItemCreate model
pydantic_target = """class BillItemCreate(BaseModel):
    id: int
    qty: float
    price: float
    packaging_type: Optional[str] = "loose"
    bottle_type: Optional[str] = None"""
pydantic_replacement = """class BillItemCreate(BaseModel):
    id: int
    qty: float
    price: float
    packaging_type: Optional[str] = "loose"
    bottle_type: Optional[str] = None
    bottle_count: Optional[int] = 0"""
main_py = main_py.replace(pydantic_target, pydantic_replacement)

# Update bill creation
bill_create_target = """        bill_item = BillItem(
            bill_id=new_bill.id,
            product_id=product.id,
            quantity=item.qty,
            price_at_sale=item.price,
            packaging_type=item.packaging_type if product.product_type == 'liquid' else 'loose',
            bottle_type=item.bottle_type if product.product_type == 'liquid' and item.packaging_type == 'bottle' else None
        )"""
bill_create_replacement = """        bill_item = BillItem(
            bill_id=new_bill.id,
            product_id=product.id,
            quantity=item.qty,
            price_at_sale=item.price,
            packaging_type=item.packaging_type if product.product_type == 'liquid' else 'loose',
            bottle_type=item.bottle_type if product.product_type == 'liquid' and item.packaging_type == 'bottle' else None,
            bottle_count=item.bottle_count if product.product_type == 'liquid' and item.packaging_type == 'bottle' else 0
        )"""
main_py = main_py.replace(bill_create_target, bill_create_replacement)

# Update get_daily_report
report_target = """                results.append({
                    "product": i.product.name,
                    "bottle_type": i.bottle_type or "N/A",
                    "packaging": i.packaging_type or "N/A",
                    "total_quantity": i.quantity,
                    "total_revenue": i.total_price
                })"""
report_replacement = """                results.append({
                    "product": i.product.name,
                    "bottle_type": i.bottle_type or "N/A",
                    "packaging": i.packaging_type or "N/A",
                    "total_quantity": i.quantity,
                    "total_revenue": i.total_price,
                    "bottle_count": i.bottle_count or 0
                })"""
main_py = main_py.replace(report_target, report_replacement)

report_existing_target = """            if existing:
                existing["total_quantity"] += i.quantity
                existing["total_revenue"] += i.total_price
            else:"""
report_existing_replacement = """            if existing:
                existing["total_quantity"] += i.quantity
                existing["total_revenue"] += i.total_price
                existing["bottle_count"] += (i.bottle_count or 0)
            else:"""
main_py = main_py.replace(report_existing_target, report_existing_replacement)

# Export report update
export_target = """        writer.writerow(["Product Name", "Bottle Type", "Packaging Type", "Total Quantity Sold", "Total Revenue (Rs)"])
        for r in results:
            writer.writerow([r["product"], r["bottle_type"], r["packaging"], f"{r['total_quantity']:.2f}", f"{r['total_revenue']:.2f}"])"""
export_replacement = """        writer.writerow(["Product Name", "Bottle Type", "Packaging Type", "Total Quantity Sold", "Bottle Count", "Total Revenue (Rs)"])
        for r in results:
            writer.writerow([r["product"], r["bottle_type"], r["packaging"], f"{r['total_quantity']:.2f}", str(r.get("bottle_count", 0)), f"{r['total_revenue']:.2f}"])"""
main_py = main_py.replace(export_target, export_replacement)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(main_py)

# 3. Update admin.html table
with open(r"templates\admin.html", "r", encoding="utf-8") as f:
    admin_html = f.read()

admin_thead_target = """                        thead.innerHTML = `
                            <th>Product Name</th>
                            <th>Bottle Type</th>
                            <th>Packaging</th>
                            <th style="text-align: right;">Total Qty Sold</th>
                            <th style="text-align: right;">Total Revenue</th>
                        `;"""
admin_thead_replacement = """                        thead.innerHTML = `
                            <th>Product Name</th>
                            <th>Bottle Type</th>
                            <th>Packaging</th>
                            <th style="text-align: right;">Total Qty Sold</th>
                            <th style="text-align: center;">Bottle Count</th>
                            <th style="text-align: right;">Total Revenue</th>
                        `;"""
admin_html = admin_html.replace(admin_thead_target, admin_thead_replacement)

admin_tr_target = """                                    <td style="text-align: right; font-weight: 600;">${row.total_quantity.toFixed(2)}</td>
                                    <td style="text-align: right; color: var(--primary); font-weight: bold;">₹${row.total_revenue.toFixed(2)}</td>
                                `;"""
admin_tr_replacement = """                                    <td style="text-align: right; font-weight: 600;">${row.total_quantity.toFixed(2)}</td>
                                    <td style="text-align: center; font-weight: 600; color: #2B6CB0;">${row.packaging === 'bottle' ? (row.bottle_count || 0) : '-'}</td>
                                    <td style="text-align: right; color: var(--primary); font-weight: bold;">₹${row.total_revenue.toFixed(2)}</td>
                                `;"""
admin_html = admin_html.replace(admin_tr_target, admin_tr_replacement)

admin_sum_target = """                            const sumRow = document.createElement('tr');
                            sumRow.style.backgroundColor = '#EBF8FF';
                            sumRow.innerHTML = `
                                <td colspan="4" style="text-align: right; font-weight: bold; color: #2B6CB0;">Total Revenue:</td>
                                <td style="text-align: right; font-weight: bold; color: var(--primary);">₹${totalRev.toFixed(2)}</td>
                            `;"""
admin_sum_replacement = """                            const sumRow = document.createElement('tr');
                            sumRow.style.backgroundColor = '#EBF8FF';
                            sumRow.innerHTML = `
                                <td colspan="5" style="text-align: right; font-weight: bold; color: #2B6CB0;">Total Revenue:</td>
                                <td style="text-align: right; font-weight: bold; color: var(--primary);">₹${totalRev.toFixed(2)}</td>
                            `;"""
admin_html = admin_html.replace(admin_sum_target, admin_sum_replacement)

with open(r"templates\admin.html", "w", encoding="utf-8") as f:
    f.write(admin_html)

# 4. Update app.js
with open(r"static\js\app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

app_js = app_js.replace("cart.push(newItem);", "newItem.bottle_count = 1;\n        cart.push(newItem);")
app_js = app_js.replace("items: cart.map(item => ({ id: item.id, qty: item.qty, packaging_type: item.packaging_type, bottle_type: item.bottle_type })),",
                        "items: cart.map(item => ({ id: item.id, qty: item.qty, packaging_type: item.packaging_type, bottle_type: item.bottle_type, bottle_count: item.bottle_count || 0 })),")

if "function updateBottleCount(" not in app_js:
    app_js = app_js.replace("function updateBottleType(id, newBtlType) {",
"""function updateBottleCount(id, count) {
    const item = cart.find(i => i.id === id);
    if (!item) return;
    item.bottle_count = parseInt(count) || 0;
    renderCart();
}

function updateBottleType(id, newBtlType) {""")

cart_html_target = """                                ${item.packaging_type === 'bottle' ? `
                                <select style="padding: 2px; font-size: 11px; border: 1px solid #CBD5E0; border-radius: 4px;" onchange="updateBottleType(${item.id}, this.value)">
                                    <option value="Type 1" ${item.bottle_type === 'Type 1' ? 'selected' : ''}>Type 1</option>
                                    <option value="Type 2" ${item.bottle_type === 'Type 2' ? 'selected' : ''}>Type 2</option>
                                    <option value="Type 3" ${item.bottle_type === 'Type 3' ? 'selected' : ''}>Type 3</option>
                                </select>` : ''}"""
cart_html_replacement = """                                ${item.packaging_type === 'bottle' ? `
                                <select style="padding: 2px; font-size: 11px; border: 1px solid #CBD5E0; border-radius: 4px;" onchange="updateBottleType(${item.id}, this.value)">
                                    <option value="Type 1" ${item.bottle_type === 'Type 1' ? 'selected' : ''}>Type 1</option>
                                    <option value="Type 2" ${item.bottle_type === 'Type 2' ? 'selected' : ''}>Type 2</option>
                                    <option value="Type 3" ${item.bottle_type === 'Type 3' ? 'selected' : ''}>Type 3</option>
                                </select>
                                <div style="display:flex; align-items:center; gap:2px; margin-left: 4px;">
                                    <span style="font-size:10px; color:#718096;">Count:</span>
                                    <input type="number" min="1" value="${item.bottle_count || 1}" style="width:35px; padding:2px; text-align:center; border:1px solid #CBD5E0; border-radius:4px; font-size:11px; outline:none;" onchange="updateBottleCount(${item.id}, this.value)">
                                </div>` : ''}"""
app_js = app_js.replace(cart_html_target, cart_html_replacement)

with open(r"static\js\app.js", "w", encoding="utf-8") as f:
    f.write(app_js)

# 5. Update factory_pos.html
with open(r"templates\factory_pos.html", "r", encoding="utf-8") as f:
    factory_html = f.read()

factory_html = factory_html.replace("cart.push({ id, name, price, qty: 1, unit: 'Ltrs', type: 'liquid', packaging_type: 'loose', bottle_type: 'Type 1' });",
                                    "cart.push({ id, name, price, qty: 1, unit: 'Ltrs', type: 'liquid', packaging_type: 'loose', bottle_type: 'Type 1', bottle_count: 1 });")

if "function updateBottleCount(" not in factory_html:
    factory_html = factory_html.replace("function updateBottleType(id, newBtlType) {",
"""function updateBottleCount(id, count) {
            const item = cart.find(i => i.id === id);
            if (!item) return;
            item.bottle_count = parseInt(count) || 0;
            renderCart();
        }

        function updateBottleType(id, newBtlType) {""")

factory_html = factory_html.replace(cart_html_target, cart_html_replacement)

payload_target = """items: cart.map(i => ({ id: i.id, qty: i.qty, price: i.price, packaging_type: i.packaging_type, bottle_type: i.bottle_type })),"""
payload_replacement = """items: cart.map(i => ({ id: i.id, qty: i.qty, price: i.price, packaging_type: i.packaging_type, bottle_type: i.bottle_type, bottle_count: i.bottle_count || 0 })),"""
factory_html = factory_html.replace(payload_target, payload_replacement)

with open(r"templates\factory_pos.html", "w", encoding="utf-8") as f:
    f.write(factory_html)

print("Done updating files for bottle count.")
