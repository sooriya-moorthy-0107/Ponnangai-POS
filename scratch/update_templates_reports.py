import sys
import re

# Update factory_pos.html
with open(r"templates\factory_pos.html", "r", encoding="utf-8") as f:
    pos_content = f.read()

# 1. Update cart items injection in addLiquid
target_add_liquid = """            if (existing) {
                existing.qty += 1;
            } else {
                cart.push({ id, name, price, qty: 1, unit: 'Ltrs', type: 'liquid' });
            }"""

replacement_add_liquid = """            if (existing) {
                existing.qty += 1;
            } else {
                cart.push({ id, name, price, qty: 1, unit: 'Ltrs', type: 'liquid', packaging_type: 'loose', bottle_type: 'Type 1' });
            }"""
pos_content = pos_content.replace(target_add_liquid, replacement_add_liquid)

# 2. Add updatePackaging and updateBottleType functions
update_packaging_funcs = """
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
        }

        function renderCart() {"""
pos_content = pos_content.replace("        function renderCart() {", update_packaging_funcs)

# 3. Update renderCart HTML string
target_render_cart_item = """                        <div style="display:flex; align-items:center; gap:2px;">
                            <span style="font-size:11px; color:#718096; display:none;">Qty:</span>
                            <input type="number" step="${step}" min="0.01" value="${item.qty}" 
                                   style="width:45px; padding:4px; text-align:center; border:1px solid #CBD5E0; border-radius:4px; height:26px; font-weight:600; font-size:13px; outline:none;"
                                   onchange="updateQty(${item.id}, this.value)">
                            <span style="font-size:11px; color:#A0AEC0;">${item.unit}</span>
                        </div>"""

replacement_render_cart_item = """                        <div style="display:flex; flex-direction:column; gap:4px;">
                            <div style="display:flex; align-items:center; gap:2px;">
                                <span style="font-size:11px; color:#718096; display:none;">Qty:</span>
                                <input type="number" step="${step}" min="0.01" value="${item.qty}" 
                                       style="width:45px; padding:4px; text-align:center; border:1px solid #CBD5E0; border-radius:4px; height:26px; font-weight:600; font-size:13px; outline:none;"
                                       onchange="updateQty(${item.id}, this.value)">
                                <span style="font-size:11px; color:#A0AEC0;">${item.unit}</span>
                            </div>
                            ${item.type === 'liquid' ? `
                            <div style="display:flex; gap: 4px;">
                                <select style="padding: 2px; font-size: 11px; border: 1px solid #CBD5E0; border-radius: 4px;" onchange="updatePackaging(${item.id}, this.value)">
                                    <option value="loose" ${item.packaging_type === 'loose' ? 'selected' : ''}>Loose</option>
                                    <option value="bottle" ${item.packaging_type === 'bottle' ? 'selected' : ''}>Bottle</option>
                                </select>
                                ${item.packaging_type === 'bottle' ? `
                                <select style="padding: 2px; font-size: 11px; border: 1px solid #CBD5E0; border-radius: 4px;" onchange="updateBottleType(${item.id}, this.value)">
                                    <option value="Type 1" ${item.bottle_type === 'Type 1' ? 'selected' : ''}>Type 1</option>
                                    <option value="Type 2" ${item.bottle_type === 'Type 2' ? 'selected' : ''}>Type 2</option>
                                    <option value="Type 3" ${item.bottle_type === 'Type 3' ? 'selected' : ''}>Type 3</option>
                                </select>` : ''}
                            </div>
                            ` : ''}
                        </div>"""
pos_content = pos_content.replace(target_render_cart_item, replacement_render_cart_item)

# 4. Update submitBill payload
target_submit_payload = """                items: cart.map(i => ({ id: i.id, qty: i.qty, price: i.price })),"""
replacement_submit_payload = """                items: cart.map(i => ({ id: i.id, qty: i.qty, price: i.price, packaging_type: i.packaging_type, bottle_type: i.bottle_type })),"""
pos_content = pos_content.replace(target_submit_payload, replacement_submit_payload)

with open(r"templates\factory_pos.html", "w", encoding="utf-8") as f:
    f.write(pos_content)

# Update admin.html
with open(r"templates\admin.html", "r", encoding="utf-8") as f:
    admin_content = f.read()

# Add reports section to admin.html
reports_html = """        <!-- Daily Sales Reports -->
        <div class="card" style="margin-top: var(--spacing);">
            <h2 style="font-size: 18px; border-bottom: 2px solid var(--primary); padding-bottom: 8px; margin-bottom: 16px;">
                📊 Daily Sales & Packaging Reports
            </h2>
            
            <div style="display: flex; gap: 16px; margin-bottom: 16px; align-items: flex-end; flex-wrap: wrap;">
                <div>
                    <label style="font-size: 12px; font-weight: 600; color: #4A5568; margin-bottom: 4px; display: block;">Select Date</label>
                    <input type="date" id="report-date" style="padding: 8px; border: 1px solid #CBD5E0; border-radius: 4px;">
                </div>
                <div>
                    <label style="font-size: 12px; font-weight: 600; color: #4A5568; margin-bottom: 4px; display: block;">Select Shop</label>
                    <select id="report-shop" style="padding: 8px; border: 1px solid #CBD5E0; border-radius: 4px; min-width: 200px;">
                        <option value="">-- Select a Shop --</option>
                        {% for sk in shopkeepers %}
                        <option value="{{ sk.id }}">{{ sk.username }}</option>
                        {% endfor %}
                        {% for sk in archived_shopkeepers %}
                        <option value="{{ sk.id }}">{{ sk.username }} (Archived)</option>
                        {% endfor %}
                    </select>
                </div>
                <button class="btn" onclick="fetchDailyReport()">Generate Report</button>
            </div>

            <div id="report-results" style="display: none;">
                <table class="admin-table" id="report-table">
                    <thead>
                        <tr style="background-color: #EDF2F7;">
                            <th>Product Name</th>
                            <th>Packaging</th>
                            <th>Bottle Type</th>
                            <th style="text-align: right;">Total Qty Sold</th>
                            <th style="text-align: right;">Total Revenue</th>
                        </tr>
                    </thead>
                    <tbody id="report-table-body">
                    </tbody>
                </table>
                <div style="margin-top: 16px; text-align: right;">
                    <button class="btn" style="background-color: #38A169; border-color: #38A169;" onclick="exportDailyReport()">
                        📥 Export to Excel (CSV)
                    </button>
                </div>
            </div>
            <div id="report-empty" style="display: none; text-align: center; color: #718096; padding: 24px;">
                No sales found for the selected shop and date.
            </div>
        </div>
"""

# Insert right after the Dashboard Stats or Shop Inventories
# Actually, I'll insert it right before the Shop Analytics Modal
target_insert_admin = """    <!-- Shop Analytics Modal -->"""
admin_content = admin_content.replace(target_insert_admin, reports_html + "\n    <!-- Shop Analytics Modal -->")

# Add JS logic for reports
script_logic = """
        function getTodayDate() {
            const today = new Date();
            const yyyy = today.getFullYear();
            let mm = today.getMonth() + 1; // Months start at 0!
            let dd = today.getDate();
            if (dd < 10) dd = '0' + dd;
            if (mm < 10) mm = '0' + mm;
            return yyyy + '-' + mm + '-' + dd;
        }
        
        document.addEventListener('DOMContentLoaded', () => {
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
                const res = await fetch(`/api/reports/daily?shopkeeper_id=${shopId}&date=${date}`);
                const data = await res.json();
                
                if (res.ok) {
                    const tbody = document.getElementById('report-table-body');
                    tbody.innerHTML = '';
                    
                    if (data.data.length === 0) {
                        document.getElementById('report-results').style.display = 'none';
                        document.getElementById('report-empty').style.display = 'block';
                    } else {
                        document.getElementById('report-empty').style.display = 'none';
                        document.getElementById('report-results').style.display = 'block';
                        
                        data.data.forEach(row => {
                            const tr = document.createElement('tr');
                            tr.innerHTML = `
                                <td><strong>${row.product}</strong></td>
                                <td>
                                    <span style="font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold; text-transform: uppercase; ${row.packaging === 'bottle' ? 'background: #EBF8FF; color: #2B6CB0;' : 'background: #EDF2F7; color: #4A5568;'}">
                                        ${row.packaging}
                                    </span>
                                </td>
                                <td>${row.bottle_type !== 'N/A' ? row.bottle_type : '<span style="color:#A0AEC0;">-</span>'}</td>
                                <td style="text-align: right; font-weight: 600;">${row.total_quantity.toFixed(2)}</td>
                                <td style="text-align: right; color: var(--primary); font-weight: bold;">₹${row.total_revenue.toFixed(2)}</td>
                            `;
                            tbody.appendChild(tr);
                        });
                    }
                } else {
                    alert(data.detail || "Error generating report");
                }
            } catch (err) {
                alert("Network error fetching report.");
            }
        }
        
        function exportDailyReport() {
            const shopId = document.getElementById('report-shop').value;
            const date = document.getElementById('report-date').value;
            if (!shopId || !date) {
                alert("Please select both a shop and a date.");
                return;
            }
            window.location.href = `/api/reports/daily/export?shopkeeper_id=${shopId}&date=${date}`;
        }
"""
admin_content = admin_content.replace("        async function resetSystem() {", script_logic + "\n        async function resetSystem() {")

with open(r"templates\admin.html", "w", encoding="utf-8") as f:
    f.write(admin_content)
