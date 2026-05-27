import re

# 1. Update app.js
with open(r"static\js\app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

# Update addToCart signature and logic
target_add_to_cart = """function addToCart(productId, productName, productPrice, maxStock) {
    const existingItem = cart.find(item => item.id === productId);
    if (existingItem) {
        if (existingItem.qty >= existingItem.maxStock) {
            alert(`Cannot add more. Only ${existingItem.maxStock} items available in stock.`);
            return;
        }
        existingItem.qty += 1;
    } else {
        if (maxStock <= 0) {
            alert("This product is out of stock.");
            return;
        }
        cart.push({ id: productId, name: productName, price: productPrice, qty: 1, maxStock: maxStock });
    }
    renderCart();
}"""
replacement_add_to_cart = """function addToCart(productId, productName, productPrice, maxStock, productType = 'solid', unit = 'Pcs') {
    const existingItem = cart.find(item => item.id === productId);
    if (existingItem) {
        if (existingItem.qty >= existingItem.maxStock) {
            alert(`Cannot add more. Only ${existingItem.maxStock} items available in stock.`);
            return;
        }
        existingItem.qty += 1;
    } else {
        if (maxStock <= 0) {
            alert("This product is out of stock.");
            return;
        }
        
        let newItem = { 
            id: productId, 
            name: productName, 
            price: productPrice, 
            qty: 1, 
            maxStock: maxStock,
            type: productType,
            unit: unit
        };
        
        if (productType === 'liquid') {
            newItem.packaging_type = 'loose';
            newItem.bottle_type = 'Type 1';
        }
        
        cart.push(newItem);
    }
    renderCart();
}

function updatePackaging(id, newPkg) {
    const item = cart.find(i => i.id === id);
    if (!item) return;
    item.packaging_type = newPkg;
    renderCart();
}

function updateBottleType(id, newBtlType) {
    const item = cart.find(i => i.id === id);
    if (!item) return;
    item.bottle_type = newBtlType;
    renderCart();
}"""
app_js = app_js.replace(target_add_to_cart, replacement_add_to_cart)

# Update renderCart to show packaging dropdowns
target_render_cart_item = """        const cartItemEl = document.createElement('div');
        cartItemEl.className = 'cart-item';
        cartItemEl.innerHTML = `
            <div class="cart-item-info">
                <div class="cart-item-title">${item.name}</div>
                <div class="cart-item-price">₹${item.price.toFixed(2)}</div>
            </div>
            <div class="cart-item-controls">
                <button class="btn btn-secondary btn-small" onclick="updateQty(${item.id}, -1)">-</button>
                <span class="cart-qty">${item.qty}</span>
                <button class="btn btn-secondary btn-small" onclick="updateQty(${item.id}, 1)">+</button>
            </div>
            <div style="font-weight: 600; min-width: 60px; text-align: right;">
                ₹${itemTotal.toFixed(2)}
            </div>
        `;
        cartItemsContainer.appendChild(cartItemEl);"""

replacement_render_cart_item = """        const cartItemEl = document.createElement('div');
        cartItemEl.className = 'cart-item';
        
        const step = item.type === 'liquid' ? 'any' : '1';
        
        let packagingHtml = '';
        if (item.type === 'liquid') {
            packagingHtml = `
            <div style="display:flex; gap: 4px; margin-top: 6px; width: 100%;">
                <select style="padding: 2px; font-size: 11px; border: 1px solid #CBD5E0; border-radius: 4px; flex: 1;" onchange="updatePackaging(${item.id}, this.value)">
                    <option value="loose" ${item.packaging_type === 'loose' ? 'selected' : ''}>Loose</option>
                    <option value="bottle" ${item.packaging_type === 'bottle' ? 'selected' : ''}>Bottle</option>
                </select>
                ${item.packaging_type === 'bottle' ? `
                <select style="padding: 2px; font-size: 11px; border: 1px solid #CBD5E0; border-radius: 4px; flex: 1;" onchange="updateBottleType(${item.id}, this.value)">
                    <option value="Type 1" ${item.bottle_type === 'Type 1' ? 'selected' : ''}>Type 1</option>
                    <option value="Type 2" ${item.bottle_type === 'Type 2' ? 'selected' : ''}>Type 2</option>
                    <option value="Type 3" ${item.bottle_type === 'Type 3' ? 'selected' : ''}>Type 3</option>
                </select>` : ''}
            </div>`;
        }
        
        cartItemEl.innerHTML = `
            <div style="display: flex; flex-direction: column; flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                    <div class="cart-item-info" style="flex: 1;">
                        <div class="cart-item-title">${item.name}</div>
                        <div class="cart-item-price">₹${item.price.toFixed(2)}</div>
                    </div>
                    <div class="cart-item-controls">
                        <button class="btn btn-secondary btn-small" onclick="updateQty(${item.id}, -1)">-</button>
                        <input type="number" step="${step}" min="0.01" max="${item.maxStock}" value="${item.qty}" 
                            style="width: 45px; text-align: center; border: 1px solid #CBD5E0; border-radius: 4px; padding: 2px; height: 26px; outline: none; margin-bottom: 0;"
                            onchange="if(this.value > 0) { updateQty(${item.id}, this.value - ${item.qty}); } else { updateQty(${item.id}, -${item.qty}); }">
                        <button class="btn btn-secondary btn-small" onclick="updateQty(${item.id}, 1)">+</button>
                    </div>
                    <div style="font-weight: 600; min-width: 60px; text-align: right; margin-left: 8px;">
                        ₹${itemTotal.toFixed(2)}
                    </div>
                </div>
                ${packagingHtml}
            </div>
        `;
        cartItemEl.style.alignItems = 'flex-start';
        cartItemsContainer.appendChild(cartItemEl);"""
app_js = app_js.replace(target_render_cart_item, replacement_render_cart_item)

# Update submitBill payload in app.js
target_submit_payload = """        items: cart.map(item => ({ id: item.id, qty: item.qty })),"""
replacement_submit_payload = """        items: cart.map(item => ({ id: item.id, qty: item.qty, packaging_type: item.packaging_type, bottle_type: item.bottle_type })),"""
app_js = app_js.replace(target_submit_payload, replacement_submit_payload)

with open(r"static\js\app.js", "w", encoding="utf-8") as f:
    f.write(app_js)

# 2. Update shop.html template
with open(r"templates\shop.html", "r", encoding="utf-8") as f:
    shop_html = f.read()

target_shop_add = """                    onclick="addToCart({{ product.id }}, '{{ product.name | replace("'", "\\'") }}', {{ product.price }}, {{ product.stock }})\""""
replacement_shop_add = """                    onclick="addToCart({{ product.id }}, '{{ product.name | replace("'", "\\'") }}', {{ product.price }}, {{ product.stock }}, '{{ product.product_type }}', '{{ product.unit }}')\""""
shop_html = shop_html.replace(target_shop_add, replacement_shop_add)

target_shop_add_js = """            card.setAttribute('onclick', `addToCart(${product.id}, '${escapedName}', ${product.price}, ${product.stock})`);"""
replacement_shop_add_js = """            card.setAttribute('onclick', `addToCart(${product.id}, '${escapedName}', ${product.price}, ${product.stock}, '${product.product_type || 'solid'}', '${product.unit || 'Pcs'}')`);"""
shop_html = shop_html.replace(target_shop_add_js, replacement_shop_add_js)

with open(r"templates\shop.html", "w", encoding="utf-8") as f:
    f.write(shop_html)

# 3. Update main.py API for date range
with open("main.py", "r", encoding="utf-8") as f:
    main_py = f.read()

target_api_1 = """@app.get("/api/reports/daily")
async def get_daily_report(request: Request, shopkeeper_id: int, date: str, db: Session = Depends(get_db)):"""
replacement_api_1 = """@app.get("/api/reports/daily")
async def get_daily_report(request: Request, shopkeeper_id: int, start_date: str, end_date: str, db: Session = Depends(get_db)):"""
main_py = main_py.replace(target_api_1, replacement_api_1)

target_api_1_logic = """    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": "Invalid date format. Use YYYY-MM-DD"})

    # Fetch bills for this shopkeeper on the specific date
    bills = db.query(Bill).filter(
        Bill.cashier_id == shopkeeper_id,
        Bill.is_cancelled == False,
        func.date(Bill.timestamp) == target_date
    ).all()"""
replacement_api_1_logic = """    try:
        t_start = datetime.strptime(start_date, '%Y-%m-%d').date()
        t_end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": "Invalid date format. Use YYYY-MM-DD"})

    # Fetch bills for this shopkeeper in the date range (inclusive)
    bills = db.query(Bill).filter(
        Bill.cashier_id == shopkeeper_id,
        Bill.is_cancelled == False,
        func.date(Bill.timestamp) >= t_start,
        func.date(Bill.timestamp) <= t_end
    ).all()"""
main_py = main_py.replace(target_api_1_logic, replacement_api_1_logic)

target_api_2 = """@app.get("/api/reports/daily/export")
async def export_daily_report(request: Request, shopkeeper_id: int, date: str, db: Session = Depends(get_db)):"""
replacement_api_2 = """@app.get("/api/reports/daily/export")
async def export_daily_report(request: Request, shopkeeper_id: int, start_date: str, end_date: str, db: Session = Depends(get_db)):"""
main_py = main_py.replace(target_api_2, replacement_api_2)

target_api_2_logic = """    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": "Invalid date format. Use YYYY-MM-DD"})

    shop = db.query(User).filter(User.id == shopkeeper_id).first()
    shop_name = shop.username if shop else "Unknown"

    bills = db.query(Bill).filter(
        Bill.cashier_id == shopkeeper_id,
        Bill.is_cancelled == False,
        func.date(Bill.timestamp) == target_date
    ).all()"""
replacement_api_2_logic = """    try:
        t_start = datetime.strptime(start_date, '%Y-%m-%d').date()
        t_end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": "Invalid date format. Use YYYY-MM-DD"})

    shop = db.query(User).filter(User.id == shopkeeper_id).first()
    shop_name = shop.username if shop else "Unknown"

    bills = db.query(Bill).filter(
        Bill.cashier_id == shopkeeper_id,
        Bill.is_cancelled == False,
        func.date(Bill.timestamp) >= t_start,
        func.date(Bill.timestamp) <= t_end
    ).all()"""
main_py = main_py.replace(target_api_2_logic, replacement_api_2_logic)

# Replace the single date write in export
target_api_2_write = """    writer.writerow(["Date:", target_date.strftime("%Y-%m-%d")])"""
replacement_api_2_write = """    writer.writerow(["Date Range:", f"{t_start.strftime('%Y-%m-%d')} to {t_end.strftime('%Y-%m-%d')}"])"""
main_py = main_py.replace(target_api_2_write, replacement_api_2_write)

target_api_2_filename = """    headers = {
        'Content-Disposition': f'attachment; filename="Daily_Report_{shop_name}_{target_date.strftime("%Y-%m-%d")}.csv"'
    }"""
replacement_api_2_filename = """    headers = {
        'Content-Disposition': f'attachment; filename="Sales_Report_{shop_name}_{t_start.strftime("%Y-%m-%d")}_to_{t_end.strftime("%Y-%m-%d")}.csv"'
    }"""
main_py = main_py.replace(target_api_2_filename, replacement_api_2_filename)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(main_py)

# 4. Update admin.html UI for date range
with open(r"templates\admin.html", "r", encoding="utf-8") as f:
    admin_html = f.read()

target_admin_ui = """                <div>
                    <label style="font-size: 12px; font-weight: 600; color: #4A5568; margin-bottom: 4px; display: block;">Select Date</label>
                    <input type="date" id="report-date" style="padding: 8px; border: 1px solid #CBD5E0; border-radius: 4px;">
                </div>"""
replacement_admin_ui = """                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <button id="btn-report-today" class="btn" style="padding: 4px 12px; background: var(--primary); color: white;" onclick="setReportMode('today')">Today</button>
                        <button id="btn-report-range" class="btn btn-secondary" style="padding: 4px 12px;" onclick="setReportMode('range')">Date Range</button>
                    </div>
                    <div id="report-date-today-container">
                        <input type="date" id="report-date-today" style="padding: 8px; border: 1px solid #CBD5E0; border-radius: 4px; background: #EDF2F7;" readonly>
                    </div>
                    <div id="report-date-range-container" style="display: none; align-items: center; gap: 8px;">
                        <input type="date" id="report-start-date" style="padding: 8px; border: 1px solid #CBD5E0; border-radius: 4px;">
                        <span style="color: #718096; font-size: 12px; font-weight: bold;">TO</span>
                        <input type="date" id="report-end-date" style="padding: 8px; border: 1px solid #CBD5E0; border-radius: 4px;">
                    </div>
                </div>"""
admin_html = admin_html.replace(target_admin_ui, replacement_admin_ui)

target_admin_js = """        document.addEventListener('DOMContentLoaded', () => {
            const dateInput = document.getElementById('report-date');
            if(dateInput) dateInput.value = getTodayDate();
        });

        async function fetchDailyReport() {
            const shopId = document.getElementById('report-shop').value;
            const date = document.getElementById('report-date').value;
            
            if (!shopId || !date) {
                alert("Please select both a shop and a date.");
                return;
            }
            
            try {
                const res = await fetch(`/api/reports/daily?shopkeeper_id=${shopId}&date=${date}`);"""
replacement_admin_js = """        let reportMode = 'today';
        
        function setReportMode(mode) {
            reportMode = mode;
            if (mode === 'today') {
                document.getElementById('btn-report-today').style.background = 'var(--primary)';
                document.getElementById('btn-report-today').style.color = 'white';
                document.getElementById('btn-report-today').className = 'btn';
                document.getElementById('btn-report-range').className = 'btn btn-secondary';
                document.getElementById('btn-report-range').style.background = '';
                document.getElementById('btn-report-range').style.color = '';
                
                document.getElementById('report-date-today-container').style.display = 'block';
                document.getElementById('report-date-range-container').style.display = 'none';
            } else {
                document.getElementById('btn-report-range').style.background = 'var(--primary)';
                document.getElementById('btn-report-range').style.color = 'white';
                document.getElementById('btn-report-range').className = 'btn';
                document.getElementById('btn-report-today').className = 'btn btn-secondary';
                document.getElementById('btn-report-today').style.background = '';
                document.getElementById('btn-report-today').style.color = '';
                
                document.getElementById('report-date-today-container').style.display = 'none';
                document.getElementById('report-date-range-container').style.display = 'flex';
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            const todayStr = getTodayDate();
            const dateInput = document.getElementById('report-date-today');
            if(dateInput) dateInput.value = todayStr;
            const startDate = document.getElementById('report-start-date');
            if(startDate) startDate.value = todayStr;
            const endDate = document.getElementById('report-end-date');
            if(endDate) endDate.value = todayStr;
        });

        function getReportDates() {
            if (reportMode === 'today') {
                const d = document.getElementById('report-date-today').value;
                return { start: d, end: d };
            } else {
                return { 
                    start: document.getElementById('report-start-date').value,
                    end: document.getElementById('report-end-date').value
                };
            }
        }

        async function fetchDailyReport() {
            const shopId = document.getElementById('report-shop').value;
            const dates = getReportDates();
            
            if (!shopId || !dates.start || !dates.end) {
                alert("Please select a shop and ensure dates are valid.");
                return;
            }
            
            try {
                const res = await fetch(`/api/reports/daily?shopkeeper_id=${shopId}&start_date=${dates.start}&end_date=${dates.end}`);"""
admin_html = admin_html.replace(target_admin_js, replacement_admin_js)

target_admin_export = """        function exportDailyReport() {
            const shopId = document.getElementById('report-shop').value;
            const date = document.getElementById('report-date').value;
            if (!shopId || !date) {
                alert("Please select both a shop and a date.");
                return;
            }
            window.location.href = `/api/reports/daily/export?shopkeeper_id=${shopId}&date=${date}`;
        }"""
replacement_admin_export = """        function exportDailyReport() {
            const shopId = document.getElementById('report-shop').value;
            const dates = getReportDates();
            if (!shopId || !dates.start || !dates.end) {
                alert("Please select a shop and valid dates.");
                return;
            }
            window.location.href = `/api/reports/daily/export?shopkeeper_id=${shopId}&start_date=${dates.start}&end_date=${dates.end}`;
        }"""
admin_html = admin_html.replace(target_admin_export, replacement_admin_export)

with open(r"templates\admin.html", "w", encoding="utf-8") as f:
    f.write(admin_html)
