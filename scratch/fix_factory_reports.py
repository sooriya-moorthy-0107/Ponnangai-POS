import re

# 1. Update main.py /factory route
with open("main.py", "r", encoding="utf-8") as f:
    main_py = f.read()

target_factory_products = """    # Fetch products active for this factory cashier
    products = db.query(Product).filter(
        Product.shopkeeper_id == target_cashier_id,
        Product.is_deleted == False
    ).all()"""
replacement_factory_products = """    # Fetch ALL active products for factory cashier so everything is visible
    products = db.query(Product).filter(
        Product.is_deleted == False
    ).all()"""
main_py = main_py.replace(target_factory_products, replacement_factory_products)

# 2. Update get_daily_report
target_get_daily = """    bills = db.query(Bill).filter(
        Bill.cashier_id == shopkeeper_id,
        Bill.is_cancelled == False,
        func.date(Bill.timestamp) >= t_start,
        func.date(Bill.timestamp) <= t_end
    ).all()

    report_data = {}
    for bill in bills:
        for item in bill.items:"""
replacement_get_daily = """    bills = db.query(Bill).filter(
        Bill.cashier_id == shopkeeper_id,
        Bill.is_cancelled == False,
        func.date(Bill.timestamp) >= t_start,
        func.date(Bill.timestamp) <= t_end
    ).all()

    shop = db.query(User).filter(User.id == shopkeeper_id).first()
    shop_role = shop.role if shop else "Shopkeeper"

    bottle_counts = {}
    report_data = {}
    for bill in bills:
        for item in bill.items:
            if item.packaging_type == "bottle" and item.bottle_type:
                if item.bottle_type not in bottle_counts:
                    bottle_counts[item.bottle_type] = 0
                bottle_counts[item.bottle_type] += int(item.quantity)"""
main_py = main_py.replace(target_get_daily, replacement_get_daily)

target_get_daily_return = """    return {"status": "success", "data": results}"""
replacement_get_daily_return = """    return {"status": "success", "data": results, "shop_role": shop_role, "bottle_counts": bottle_counts}"""
main_py = main_py.replace(target_get_daily_return, replacement_get_daily_return)

# 3. Update export_daily_report
target_export_daily = """    report_data = {}
    total_sales = 0.0
    for bill in bills:
        for item in bill.items:"""
replacement_export_daily = """    report_data = {}
    total_sales = 0.0
    bottle_counts = {}
    for bill in bills:
        for item in bill.items:
            if item.packaging_type == "bottle" and item.bottle_type:
                if item.bottle_type not in bottle_counts:
                    bottle_counts[item.bottle_type] = 0
                bottle_counts[item.bottle_type] += int(item.quantity)"""
main_py = main_py.replace(target_export_daily, replacement_export_daily)

target_export_write = """    writer.writerow(["Total Revenue:", f"Rs {total_sales:.2f}"])
    writer.writerow([])
    writer.writerow(["Product Name", "Packaging Type", "Bottle Type", "Total Quantity Sold", "Total Revenue (Rs)"])
    
    results = list(report_data.values())
    results.sort(key=lambda x: (x["packaging"], x["product"]))
    
    for r in results:
        writer.writerow([r["product"], r["packaging"], r["bottle_type"], f"{r['total_quantity']:.2f}", f"{r['total_revenue']:.2f}"])
        
    output.seek(0)"""
replacement_export_write = """    writer.writerow([])
    
    results = list(report_data.values())
    results.sort(key=lambda x: (x["packaging"], x["product"]))
    
    if shop and shop.role == "Factory":
        writer.writerow(["Product Name", "Bottle Type", "Packaging Type", "Total Quantity Sold", "Total Revenue (Rs)"])
        for r in results:
            writer.writerow([r["product"], r["bottle_type"], r["packaging"], f"{r['total_quantity']:.2f}", f"{r['total_revenue']:.2f}"])
        writer.writerow([])
        writer.writerow(["Total Revenue Summary", f"Rs {total_sales:.2f}"])
        writer.writerow([])
        writer.writerow(["Bottle Counts"])
        for b_type, count in bottle_counts.items():
            if count > 0:
                writer.writerow([b_type, count])
    else:
        writer.writerow(["Product Name", "Total Quantity Sold", "Total Revenue (Rs)"])
        shop_agg = {}
        for r in results:
            if r["product"] not in shop_agg:
                shop_agg[r["product"]] = {"qty": 0.0, "rev": 0.0}
            shop_agg[r["product"]]["qty"] += r["total_quantity"]
            shop_agg[r["product"]]["rev"] += r["total_revenue"]
        for prod, val in shop_agg.items():
            writer.writerow([prod, f"{val['qty']:.2f}", f"{val['rev']:.2f}"])
        writer.writerow([])
        writer.writerow(["Total Revenue Summary", f"Rs {total_sales:.2f}"])
        
    output.seek(0)"""
main_py = main_py.replace(target_export_write, replacement_export_write)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(main_py)

# 4. Update admin.html
with open(r"templates\admin.html", "r", encoding="utf-8") as f:
    admin_html = f.read()

target_admin_table = """                <table class="admin-table" id="report-table">
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
                </div>"""
replacement_admin_table = """                <table class="admin-table" id="report-table">
                    <thead>
                        <tr style="background-color: #EDF2F7;">
                            <!-- Handled by JS -->
                        </tr>
                    </thead>
                    <tbody id="report-table-body">
                    </tbody>
                </table>
                <div id="report-bottle-counts" style="margin-top: 16px; font-size: 14px; color: #4A5568;"></div>
                <div style="margin-top: 16px; text-align: right;">
                    <button class="btn" style="background-color: #38A169; border-color: #38A169;" onclick="exportDailyReport()">
                        📥 Export to Excel (CSV)
                    </button>
                </div>"""
admin_html = admin_html.replace(target_admin_table, replacement_admin_table)

target_admin_js = """                if (res.ok) {
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
                    }"""
replacement_admin_js = """                if (res.ok) {
                    const tbody = document.getElementById('report-table-body');
                    const thead = document.querySelector('#report-table thead tr');
                    tbody.innerHTML = '';
                    
                    if (data.shop_role === 'Factory') {
                        thead.innerHTML = `
                            <th>Product Name</th>
                            <th>Bottle Type</th>
                            <th>Packaging</th>
                            <th style="text-align: right;">Total Qty Sold</th>
                            <th style="text-align: right;">Total Revenue</th>
                        `;
                    } else {
                        thead.innerHTML = `
                            <th>Product Name</th>
                            <th style="text-align: right;">Total Qty Sold</th>
                            <th style="text-align: right;">Total Revenue</th>
                        `;
                    }
                    
                    if (data.data.length === 0) {
                        document.getElementById('report-results').style.display = 'none';
                        document.getElementById('report-empty').style.display = 'block';
                    } else {
                        document.getElementById('report-empty').style.display = 'none';
                        document.getElementById('report-results').style.display = 'block';
                        
                        let totalRev = 0;
                        
                        if (data.shop_role === 'Factory') {
                            data.data.forEach(row => {
                                totalRev += row.total_revenue;
                                const tr = document.createElement('tr');
                                tr.innerHTML = `
                                    <td><strong>${row.product}</strong></td>
                                    <td>${row.bottle_type !== 'N/A' ? row.bottle_type : '<span style="color:#A0AEC0;">-</span>'}</td>
                                    <td>
                                        <span style="font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold; text-transform: uppercase; ${row.packaging === 'bottle' ? 'background: #EBF8FF; color: #2B6CB0;' : 'background: #EDF2F7; color: #4A5568;'}">
                                            ${row.packaging}
                                        </span>
                                    </td>
                                    <td style="text-align: right; font-weight: 600;">${row.total_quantity.toFixed(2)}</td>
                                    <td style="text-align: right; color: var(--primary); font-weight: bold;">₹${row.total_revenue.toFixed(2)}</td>
                                `;
                                tbody.appendChild(tr);
                            });
                            
                            const sumRow = document.createElement('tr');
                            sumRow.style.backgroundColor = '#EBF8FF';
                            sumRow.innerHTML = `
                                <td colspan="4" style="text-align: right; font-weight: bold; color: #2B6CB0;">Total Revenue:</td>
                                <td style="text-align: right; font-weight: bold; color: var(--primary);">₹${totalRev.toFixed(2)}</td>
                            `;
                            tbody.appendChild(sumRow);
                            
                            const bottleCountsDiv = document.getElementById('report-bottle-counts');
                            if(bottleCountsDiv) {
                                let bcHtml = '<strong>Bottle Counts:</strong> ';
                                let hasBottles = false;
                                for (const [type, count] of Object.entries(data.bottle_counts)) {
                                    if(count > 0) {
                                        bcHtml += `<span style="margin-left: 8px; padding: 2px 8px; background: #CBD5E0; border-radius: 12px; font-size: 12px;">${type} = ${count}</span>`;
                                        hasBottles = true;
                                    }
                                }
                                bottleCountsDiv.innerHTML = hasBottles ? bcHtml : '';
                            }
                        } else {
                            const shopAgg = {};
                            data.data.forEach(row => {
                                if (!shopAgg[row.product]) {
                                    shopAgg[row.product] = { qty: 0, rev: 0 };
                                }
                                shopAgg[row.product].qty += row.total_quantity;
                                shopAgg[row.product].rev += row.total_revenue;
                                totalRev += row.total_revenue;
                            });
                            
                            for (const [prod, val] of Object.entries(shopAgg)) {
                                const tr = document.createElement('tr');
                                tr.innerHTML = `
                                    <td><strong>${prod}</strong></td>
                                    <td style="text-align: right; font-weight: 600;">${val.qty.toFixed(2)}</td>
                                    <td style="text-align: right; color: var(--primary); font-weight: bold;">₹${val.rev.toFixed(2)}</td>
                                `;
                                tbody.appendChild(tr);
                            }
                            
                            const sumRow = document.createElement('tr');
                            sumRow.style.backgroundColor = '#EBF8FF';
                            sumRow.innerHTML = `
                                <td colspan="2" style="text-align: right; font-weight: bold; color: #2B6CB0;">Total Revenue:</td>
                                <td style="text-align: right; font-weight: bold; color: var(--primary);">₹${totalRev.toFixed(2)}</td>
                            `;
                            tbody.appendChild(sumRow);
                            
                            const bottleCountsDiv = document.getElementById('report-bottle-counts');
                            if(bottleCountsDiv) bottleCountsDiv.innerHTML = '';
                        }
                    }"""
admin_html = admin_html.replace(target_admin_js, replacement_admin_js)

with open(r"templates\admin.html", "w", encoding="utf-8") as f:
    f.write(admin_html)
