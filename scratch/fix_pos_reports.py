import re

# 1. Update factory_pos.html
with open(r"templates\factory_pos.html", "r", encoding="utf-8") as f:
    factory_html = f.read()

target_factory_header = """        <div style="font-weight: bold;">Ponnangai POS (Factory)</div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="font-size: 14px;">Cashier: {{ cashier_name }}</div>
            <a href="/logout" class="btn btn-secondary btn-small" style="text-decoration: none; padding: 4px 10px;">Logout</a>
        </div>"""

replacement_factory_header = """        <div style="font-weight: bold;">Ponnangai POS (Factory)</div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="font-size: 14px; margin-right: 10px;">Cashier: {{ cashier_name }}</div>
            
            <div style="display: flex; align-items: center; gap: 4px; background: #E2E8F0; padding: 4px; border-radius: 4px;">
                <span style="font-size: 11px; font-weight: bold; padding: 0 4px;">Report:</span>
                <button class="btn btn-small" style="padding: 2px 8px; font-size: 11px; background: #38A169;" onclick="downloadPosReport('today')">Today</button>
                <button class="btn btn-secondary btn-small" style="padding: 2px 8px; font-size: 11px;" onclick="downloadPosReport('range')">Range</button>
            </div>
            
            <a href="/logout" class="btn btn-secondary btn-small" style="text-decoration: none; padding: 4px 10px;">Logout</a>
        </div>"""

if "downloadPosReport" not in factory_html:
    factory_html = factory_html.replace(target_factory_header, replacement_factory_header)

target_factory_js = """        window.addEventListener('load', () => {
            loadBillHistory();
        });
    </script>"""

replacement_factory_js = """        function getTodayString() {
            const d = new Date();
            let month = '' + (d.getMonth() + 1), day = '' + d.getDate(), year = d.getFullYear();
            if (month.length < 2) month = '0' + month;
            if (day.length < 2) day = '0' + day;
            return [year, month, day].join('-');
        }

        function downloadPosReport(type) {
            const today = getTodayString();
            let start = today;
            let end = today;
            
            if (type === 'range') {
                const s = prompt("Enter Start Date (YYYY-MM-DD):", today);
                if (!s) return;
                const e = prompt("Enter End Date (YYYY-MM-DD):", today);
                if (!e) return;
                start = s;
                end = e;
            }
            
            window.location.href = `/api/reports/daily/export?shopkeeper_id=${ACTIVE_CASHIER_ID}&start_date=${start}&end_date=${end}`;
        }

        window.addEventListener('load', () => {
            loadBillHistory();
        });
    </script>"""

if "downloadPosReport(type)" not in factory_html:
    factory_html = factory_html.replace(target_factory_js, replacement_factory_js)

with open(r"templates\factory_pos.html", "w", encoding="utf-8") as f:
    f.write(factory_html)

# 2. Update shop.html
with open(r"templates\shop.html", "r", encoding="utf-8") as f:
    shop_html = f.read()

target_shop_header = """        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="font-size: 14px;">Cashier: {{ user.username }}</div>
            <a href="/logout" class="btn btn-secondary btn-small" style="text-decoration: none; padding: 4px 10px;">Logout</a>
        </div>"""

replacement_shop_header = """        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="font-size: 14px; margin-right: 10px;">Cashier: {{ user.username }}</div>
            
            <div style="display: flex; align-items: center; gap: 4px; background: #E2E8F0; padding: 4px; border-radius: 4px;">
                <span style="font-size: 11px; font-weight: bold; padding: 0 4px;">Report:</span>
                <button class="btn btn-small" style="padding: 2px 8px; font-size: 11px; background: #38A169;" onclick="downloadPosReport('today')">Today</button>
                <button class="btn btn-secondary btn-small" style="padding: 2px 8px; font-size: 11px;" onclick="downloadPosReport('range')">Range</button>
            </div>
            
            <a href="/logout" class="btn btn-secondary btn-small" style="text-decoration: none; padding: 4px 10px;">Logout</a>
        </div>"""

if "downloadPosReport" not in shop_html:
    shop_html = shop_html.replace(target_shop_header, replacement_shop_header)

target_shop_js = """        window.addEventListener('load', () => {
            loadBillHistory();
            renderProducts(productsData);
        });
    </script>"""

replacement_shop_js = """        function getTodayString() {
            const d = new Date();
            let month = '' + (d.getMonth() + 1), day = '' + d.getDate(), year = d.getFullYear();
            if (month.length < 2) month = '0' + month;
            if (day.length < 2) day = '0' + day;
            return [year, month, day].join('-');
        }

        function downloadPosReport(type) {
            const today = getTodayString();
            let start = today;
            let end = today;
            
            if (type === 'range') {
                const s = prompt("Enter Start Date (YYYY-MM-DD):", today);
                if (!s) return;
                const e = prompt("Enter End Date (YYYY-MM-DD):", today);
                if (!e) return;
                start = s;
                end = e;
            }
            
            const targetShopId = document.querySelector('select[name="shopkeeper_id"]') ? document.querySelector('select[name="shopkeeper_id"]').value : ACTIVE_SHOPKEEPER_ID;
            window.location.href = `/api/reports/daily/export?shopkeeper_id=${targetShopId}&start_date=${start}&end_date=${end}`;
        }

        window.addEventListener('load', () => {
            loadBillHistory();
            renderProducts(productsData);
        });
    </script>"""

if "downloadPosReport(type)" not in shop_html:
    shop_html = shop_html.replace(target_shop_js, replacement_shop_js)

with open(r"templates\shop.html", "w", encoding="utf-8") as f:
    f.write(shop_html)

print("POS report buttons added successfully.")
