
        function toggleSessionDetails(sessionId) {
            const el = document.getElementById(`session-details-${sessionId}`);
            if (el) {
                el.style.display = el.style.display === 'none' ? 'block' : 'none';
            }
        }



        function getTodayDate() {
            const today = new Date();
            const yyyy = today.getFullYear();
            let mm = today.getMonth() + 1; // Months start at 0!
            let dd = today.getDate();
            if (dd < 10) dd = '0' + dd;
            if (mm < 10) mm = '0' + mm;
            return yyyy + '-' + mm + '-' + dd;
        }

        let reportMode = 'today';

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
            if (dateInput) dateInput.value = todayStr;
            const startDate = document.getElementById('report-start-date');
            if (startDate) startDate.value = todayStr;
            const endDate = document.getElementById('report-end-date');
            if (endDate) endDate.value = todayStr;
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
                const res = await fetch(`/api/reports/daily?shopkeeper_id=${shopId}&start_date=${dates.start}&end_date=${dates.end}`);
                const data = await res.json();

                if (res.ok) {
                    const tbody = document.getElementById('report-table-body');
                    const thead = document.querySelector('#report-table thead tr');
                    tbody.innerHTML = '';

                    if (data.shop_role === 'Factory') {
                        thead.innerHTML = `
                            <th>Product Name</th>
                            <th>Bottle Type</th>
                            <th>Packaging Type</th>
                            <th style="text-align: right;">Total Quantity Sold</th>
                            <th style="text-align: right;">Total Revenue (Rs)</th>
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

                            if (data.revenue_breakdown) {
                                document.getElementById('report-top-revenue').innerHTML = `
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span>Total Revenue: ₹${data.revenue_breakdown.Total.toFixed(2)}</span>
                                        <div style="font-size: 13px; font-weight: normal; color: #4A5568;">
                                            <span style="margin-left: 12px;">Cash: ₹${data.revenue_breakdown.Cash.toFixed(2)}</span>
                                            <span style="margin-left: 12px;">UPI: ₹${data.revenue_breakdown.UPI.toFixed(2)}</span>
                                            <span style="margin-left: 12px;">Card: ₹${data.revenue_breakdown.Card.toFixed(2)}</span>
                                        </div>
                                    </div>
                                `;

                                const netCash = data.revenue_breakdown.Cash + data.total_cash_in - data.total_cash_out;
                                const breakDownHtml = `
                                    <tr style="background-color: #F7FAFC;"><td colspan="4" style="text-align: right; color: #4A5568;">Cash:</td><td style="text-align: right;">₹${data.revenue_breakdown.Cash.toFixed(2)}</td></tr>
                                    <tr style="background-color: #F7FAFC;"><td colspan="4" style="text-align: right; color: #4A5568;">UPI:</td><td style="text-align: right;">₹${data.revenue_breakdown.UPI.toFixed(2)}</td></tr>
                                    <tr style="background-color: #F7FAFC;"><td colspan="4" style="text-align: right; color: #4A5568;">Card:</td><td style="text-align: right;">₹${data.revenue_breakdown.Card.toFixed(2)}</td></tr>
                                    <tr style="background-color: #FFF5F5;"><td colspan="4" style="text-align: right; color: #C53030;">Money OUT (Expenses):</td><td style="text-align: right; color: #C53030;">-₹${data.total_cash_out.toFixed(2)}</td></tr>
                                    <tr style="background-color: #F0FFF4;"><td colspan="4" style="text-align: right; font-weight: bold; color: #2F855A;">Total After Expense (Cash in Drawer):</td><td style="text-align: right; font-weight: bold; color: #2F855A;">₹${netCash.toFixed(2)}</td></tr>
                                `;
                                tbody.insertAdjacentHTML('beforeend', breakDownHtml);
                            }


                            const bottleCountsDiv = document.getElementById('report-bottle-counts');
                            if (bottleCountsDiv) {
                                let bcHtml = '<strong>Bottle Counts:</strong> ';
                                let hasBottles = false;
                                for (const [type, count] of Object.entries(data.bottle_counts)) {
                                    if (count > 0) {
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

                            if (data.revenue_breakdown) {
                                document.getElementById('report-top-revenue').innerHTML = `
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span>Total Revenue: ₹${data.revenue_breakdown.Total.toFixed(2)}</span>
                                        <div style="font-size: 13px; font-weight: normal; color: #4A5568;">
                                            <span style="margin-left: 12px;">Cash: ₹${data.revenue_breakdown.Cash.toFixed(2)}</span>
                                            <span style="margin-left: 12px;">UPI: ₹${data.revenue_breakdown.UPI.toFixed(2)}</span>
                                            <span style="margin-left: 12px;">Card: ₹${data.revenue_breakdown.Card.toFixed(2)}</span>
                                        </div>
                                    </div>
                                `;

                                const netCash = data.revenue_breakdown.Cash + data.total_cash_in - data.total_cash_out;
                                const breakDownHtml = `
                                    <tr style="background-color: #F7FAFC;"><td colspan="2" style="text-align: right; color: #4A5568;">Cash:</td><td style="text-align: right;">₹${data.revenue_breakdown.Cash.toFixed(2)}</td></tr>
                                    <tr style="background-color: #F7FAFC;"><td colspan="2" style="text-align: right; color: #4A5568;">UPI:</td><td style="text-align: right;">₹${data.revenue_breakdown.UPI.toFixed(2)}</td></tr>
                                    <tr style="background-color: #F7FAFC;"><td colspan="2" style="text-align: right; color: #4A5568;">Card:</td><td style="text-align: right;">₹${data.revenue_breakdown.Card.toFixed(2)}</td></tr>
                                    <tr style="background-color: #FFF5F5;"><td colspan="2" style="text-align: right; color: #C53030;">Money OUT (Expenses):</td><td style="text-align: right; color: #C53030;">-₹${data.total_cash_out.toFixed(2)}</td></tr>
                                    <tr style="background-color: #F0FFF4;"><td colspan="2" style="text-align: right; font-weight: bold; color: #2F855A;">Total After Expense (Cash in Drawer):</td><td style="text-align: right; font-weight: bold; color: #2F855A;">₹${netCash.toFixed(2)}</td></tr>
                                `;
                                tbody.insertAdjacentHTML('beforeend', breakDownHtml);
                            }


                            const bottleCountsDiv = document.getElementById('report-bottle-counts');
                            if (bottleCountsDiv) bottleCountsDiv.innerHTML = '';
                        }
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
            const dates = getReportDates();
            if (!shopId || !dates.start || !dates.end) {
                alert("Please select a shop and valid dates.");
                return;
            }
            window.location.href = `/api/reports/daily/export?shopkeeper_id=${shopId}&start_date=${dates.start}&end_date=${dates.end}`;
        }

        async function resetSystem() {
            if (confirm("Are you absolutely sure? This will permanently delete ALL products, shop inventories, bills, and sales history. This CANNOT be undone.")) {
                const check = prompt("Type RESET to confirm:");
                if (check !== "RESET") return;

                try {
                    const response = await fetch('/api/system/reset', {
                        method: 'POST'
                    });
                    const data = await response.json();
                    if (response.ok) {
                        alert(data.detail || 'System reset successfully.');
                        location.reload();
                    } else {
                        alert(data.detail || 'Failed to reset system.');
                    }
                } catch (err) {
                    alert('Error resetting system.');
                }
            }
        }


        function toggleAddProductForm(shopId) {
            const el = document.getElementById(`add-product-form-${shopId}`);
            if (el) {
                el.style.display = el.style.display === 'none' ? 'flex' : 'none';
            }
            const bulkEl = document.getElementById(`bulk-upload-form-${shopId}`);
            if (bulkEl) bulkEl.style.display = 'none';
            const stockEl = document.getElementById(`bulk-stock-form-${shopId}`);
            if (stockEl) stockEl.style.display = 'none';
        }

        function toggleBulkUploadForm(shopId) {
            const el = document.getElementById(`bulk-upload-form-${shopId}`);
            if (el) {
                el.style.display = el.style.display === 'none' ? 'flex' : 'none';
            }
            const addEl = document.getElementById(`add-product-form-${shopId}`);
            if (addEl) addEl.style.display = 'none';
            const stockEl = document.getElementById(`bulk-stock-form-${shopId}`);
            if (stockEl) stockEl.style.display = 'none';
        }

        function toggleBulkStockForm(shopId) {
            const el = document.getElementById(`bulk-stock-form-${shopId}`);
            if (el) {
                el.style.display = el.style.display === 'none' ? 'flex' : 'none';
            }
            const addEl = document.getElementById(`add-product-form-${shopId}`);
            if (addEl) addEl.style.display = 'none';
            const bulkEl = document.getElementById(`bulk-upload-form-${shopId}`);
            if (bulkEl) bulkEl.style.display = 'none';
        }

        function downloadProductTemplate() {
            window.location.href = '/api/products/template';
        }

        function downloadStockTemplate(shopkeeperId) {
            window.location.href = `/api/inventory/template/${shopkeeperId}`;
        }

        async function uploadBulkStockToShop(shopkeeperId) {
            const fileInput = document.getElementById(`stock-csv-file-${shopkeeperId}`);
            if (!fileInput || fileInput.files.length === 0) {
                alert('Please select a CSV file to upload.');
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('shopkeeper_id', shopkeeperId);

            try {
                const response = await fetch('/api/inventory/bulk_upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (response.ok) {
                    alert(data.detail || 'Stock updated successfully!');
                    location.reload();
                } else {
                    alert(data.detail || 'Failed to upload stock CSV.');
                }
            } catch (err) {
                alert('Error uploading stock CSV.');
            }
        }

        async function addNewProductToShop(shopkeeperId) {
            const nameEl = document.getElementById(`new-product-name-${shopkeeperId}`);
            const priceEl = document.getElementById(`new-product-price-${shopkeeperId}`);
            const stockEl = document.getElementById(`new-product-stock-${shopkeeperId}`);
            const typeEl = document.getElementById(`new-product-type-${shopkeeperId}`);
            const unitEl = document.getElementById(`new-product-unit-${shopkeeperId}`);

            if (!nameEl || !priceEl || !stockEl) return;

            const name = nameEl.value.trim();
            const price = priceEl.value;
            const stock = stockEl.value;
            const product_type = typeEl ? typeEl.value : "solid";
            const unit = unitEl ? unitEl.value.trim() : "Pcs";

            if (!name || !price) {
                alert('Please provide at least product name and price.');
                return;
            }

            try {
                const response = await fetch('/api/products/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: name,
                        price: parseFloat(price),
                        stock: parseInt(stock) || 0,
                        shopkeeper_id: parseInt(shopkeeperId),
                        product_type: product_type,
                        unit: unit
                    })
                });

                const data = await response.json();
                if (response.ok) {
                    alert(data.detail || 'Product added successfully!');
                    location.reload();
                } else {
                    alert(data.detail || 'Failed to add product.');
                }
            } catch (err) {
                alert('Error adding product.');
            }
        }

        async function uploadBulkProductsToShop(shopkeeperId) {
            const fileInput = document.getElementById(`product-csv-file-${shopkeeperId}`);
            if (!fileInput || fileInput.files.length === 0) {
                alert('Please select a CSV file to upload.');
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('shopkeeper_id', shopkeeperId);

            try {
                const response = await fetch('/api/products/bulk_upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (response.ok) {
                    alert(data.detail || 'Products uploaded successfully!');
                    location.reload();
                } else {
                    alert(data.detail || 'Failed to upload CSV.');
                }
            } catch (err) {
                alert('Error uploading CSV.');
            }
        }

        function showInventory(shopId) {
            document.querySelectorAll('.inventory-table-container').forEach(el => el.style.display = 'none');
            const target = document.getElementById('inventory-table-wrapper-' + shopId);
            if (target) target.style.display = 'block';
        }

        async function updateStock(shopkeeperId, productId) {
            const newStock = document.getElementById(`stock-${shopkeeperId}-${productId}`).value;
            try {
                const response = await fetch('/api/inventory/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: productId, stock: parseInt(newStock), shopkeeper_id: shopkeeperId })
                });
                if (response.ok) {
                    alert('Stock updated successfully!');
                    location.reload();
                } else {
                    alert('Failed to update stock.');
                }
            } catch (err) {
                alert('Error updating stock.');
            }
        }

        async function deleteProduct(productId, productName) {
            if (confirm(`Are you sure you want to delete product '${productName}'? This will soft-delete it so historical receipts and analytics are preserved, but it will be hidden from the active catalog and POS.`)) {
                try {
                    const response = await fetch('/api/products/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: productId })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        alert(data.detail || 'Product deleted successfully!');
                        location.reload();
                    } else {
                        alert(data.detail || 'Failed to delete product.');
                    }
                } catch (err) {
                    alert('Error deleting product.');
                }
            }
        }

        async function uploadDirectPhoto(input, productId) {
            const file = input.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/products/' + productId + '/image', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (response.ok) {
                    alert(data.detail || 'Photo updated successfully!');
                    location.reload();
                } else {
                    alert(data.detail || 'Failed to update photo.');
                }
            } catch (err) {
                alert('Error uploading photo.');
            }
            input.value = '';
        }

        async function addUser() {
            const username = document.getElementById('new-username').value.trim();
            const password = document.getElementById('new-password').value;
            const role = document.getElementById('new-role').value;

            if (!username || !password) {
                alert('Please provide username and password.');
                return;
            }

            try {
                const response = await fetch('/api/users/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password, role })
                });

                const data = await response.json();
                if (response.ok) {
                    alert(data.detail || 'User added successfully!');
                    location.reload();
                } else {
                    alert(data.detail || 'Failed to add user.');
                }
            } catch (err) {
                alert('Error adding user.');
            }
        }

        async function resetPassword(userId, username) {
            const newPwd = prompt(`Enter new password for ${username}:`);
            if (!newPwd) return;

            try {
                const response = await fetch('/api/users/update_password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, new_password: newPwd })
                });
                const data = await response.json();
                if (response.ok) {
                    alert(data.detail || 'Password updated successfully!');
                } else {
                    alert(data.detail || 'Failed to update password.');
                }
            } catch (err) {
                alert('Error updating password.');
            }
        }

        function hideAddUserForm() {
            document.getElementById('add-user-form').style.display = 'none';
            document.getElementById('new-username').value = '';
            document.getElementById('new-role').value = 'Shopkeeper';
            document.getElementById('new-password').value = '';
            document.getElementById('new-password').placeholder = "";
            const saveBtn = document.getElementById('save-user-btn');
            saveBtn.onclick = addUser;
            saveBtn.innerText = "Save";
        }

        function showEditUser(id, username, role) {
            document.getElementById('add-user-form').style.display = 'flex';
            document.getElementById('new-username').value = username;
            document.getElementById('new-role').value = role;
            document.getElementById('new-password').placeholder = "(Unchanged)";
            document.getElementById('new-password').value = "";

            const saveBtn = document.getElementById('save-user-btn');
            saveBtn.onclick = function () { editUser(id); };
            saveBtn.innerText = "Update";
        }

        async function editUser(userId) {
            const username = document.getElementById('new-username').value.trim();
            const role = document.getElementById('new-role').value;

            try {
                const response = await fetch('/api/users/edit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, username, role })
                });
                const data = await response.json();
                if (response.ok) {
                    alert('User updated successfully!');
                    location.reload();
                } else {
                    alert(data.detail || 'Failed to update user.');
                }
            } catch (err) {
                alert('Error updating user.');
            }
        }

        async function deleteUser(userId, username) {
            if (confirm(`Are you sure you want to permanently DELETE user '${username}'?`)) {
                try {
                    const response = await fetch('/api/users/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: userId })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        alert('User deleted successfully!');
                        location.reload();
                    } else {
                        alert(data.detail || 'Failed to delete user.');
                    }
                } catch (err) {
                    alert('Error deleting user.');
                }
            }
        }

        async function viewShopAnalytics(shopId) {
            try {
                const response = await fetch(`/api/analytics/shop/${shopId}`);
                const data = await response.json();
                if (response.ok) {
                    document.getElementById('analytics-shop-name').innerText = `${data.shop_name} - Analytics`;
                    document.getElementById('analytics-total-sales').innerText = `${data.total_sales} Bills`;
                    document.getElementById('analytics-total-revenue').innerText = `₹${data.total_revenue.toFixed(2)}`;

                    const tbody = document.getElementById('analytics-breakdown-body');
                    tbody.innerHTML = '';
                    if (data.breakdown.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #718096;">No sales data available.</td></tr>';
                    } else {
                        data.breakdown.forEach(item => {
                            tbody.innerHTML += `
                                <tr>
                                    <td>${item.product_name}</td>
                                    <td style="text-align: center;">${item.qty}</td>
                                    <td style="text-align: right;">₹${item.revenue.toFixed(2)}</td>
                                </tr>
                            `;
                        });
                    }

                    document.getElementById('analytics-modal').style.display = 'flex';
                } else {
                    alert(data.detail || 'Failed to fetch analytics.');
                }
            } catch (err) {
                alert('Error fetching analytics.');
            }
        }

        async function hardDeleteUser(userId, username) {
            if (!confirm(`DANGER: Are you absolutely sure you want to PERMANENTLY delete the archived account '${username}'? This will erase all their products, bills, and history. This CANNOT be undone.`)) {
                return;
            }
            if (!confirm(`FINAL WARNING: Have you exported necessary reports? Press OK to proceed with wiping all data for '${username}'.`)) {
                return;
            }

            try {
                const response = await fetch('/api/users/hard_delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId })
                });
                const data = await response.json();
                if (response.ok) {
                    alert("Account and history permanently deleted.");
                    location.reload();
                } else {
                    alert(data.detail || 'Failed to permanently delete user.');
                }
            } catch (err) {
                alert('Network error during permanent deletion.');
            }
        }
    