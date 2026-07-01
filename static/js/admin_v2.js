
// Added for XSS protection
function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    return str.toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}


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
                await Swal.fire("Please select a shop and ensure dates are valid.");
                return;
            }

            try {
                const res = await fetch(`/api/reports/daily?shopkeeper_id=${shopId}&start_date=${dates.start}&end_date=${dates.end}`);
                const data = await res.json();

                if (res.ok) {
                    const tbody = document.getElementById('report-table-body');
                    const thead = document.querySelector('#report-table thead tr');
                    tbody.innerHTML = '';

                    thead.innerHTML = `
                        <th>Product Name</th>
                        <th>Bottle Type</th>
                        <th>Packaging Type</th>
                        <th style="text-align: right;">Total Quantity Sold</th>
                        <th style="text-align: right;">Total Revenue (Rs)</th>
                    `;

                    if (data.data.length === 0) {
                        document.getElementById('report-results').style.display = 'none';
                        document.getElementById('report-empty').style.display = 'block';
                    } else {
                        document.getElementById('report-empty').style.display = 'none';
                        document.getElementById('report-results').style.display = 'block';

                        let totalRev = 0;

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
                    }
                } else {
                    await Swal.fire(data.detail || "Error generating report");
                }
            } catch (err) {
                await Swal.fire("Network error fetching report.");
            }
        }

        async function exportDailyReport() {
            const shopId = document.getElementById('report-shop').value;
            const dates = getReportDates();
            if (!shopId || !dates.start || !dates.end) {
                await Swal.fire("Please select a shop and valid dates.");
                return;
            }
            window.location.href = `/api/reports/daily/export?shopkeeper_id=${shopId}&start_date=${dates.start}&end_date=${dates.end}`;
        }

        async function resetSystem() {
            const _swalRes15831 = await Swal.fire({ text: "Are you absolutely sure? This will permanently delete ALL products, shop inventories, bills, and sales history. This CANNOT be undone.", icon: 'warning', showCancelButton: true, confirmButtonColor: 'var(--primary)', cancelButtonColor: '#C53030' });
            if (_swalRes15831.isConfirmed) {
                const { value: check } = await Swal.fire({ title: "Type RESET to confirm:", input: 'text', showCancelButton: true });
                if (!check) return; // User cancelled
                if (check.trim().toUpperCase() !== "RESET") {
                    await Swal.fire("Verification failed", "You didn't type RESET correctly.", "error");
                    return;
                }

                try {
                    const response = await fetch('/api/system/reset', {
                        method: 'POST'
                    });
                    const data = await response.json();
                    if (response.ok) {
                        await Swal.fire(data.detail || 'System reset successfully.');
                        location.reload();
                    } else {
                        await Swal.fire(data.detail || 'Failed to reset system.');
                    }
                } catch (err) {
                    await Swal.fire('Error resetting system.');
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
                await Swal.fire('Please select a CSV file to upload.');
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
                    await Swal.fire(data.detail || 'Stock updated successfully!');
                    location.reload();
                } else {
                    await Swal.fire(data.detail || 'Failed to upload stock CSV.');
                }
            } catch (err) {
                await Swal.fire('Error uploading stock CSV.');
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
                await Swal.fire('Please provide at least product name and price.');
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
                    await Swal.fire(data.detail || 'Product added successfully!');
                    location.reload();
                } else {
                    await Swal.fire(data.detail || 'Failed to add product.');
                }
            } catch (err) {
                await Swal.fire('Error adding product.');
            }
        }

        async function uploadBulkProductsToShop(shopkeeperId) {
            const fileInput = document.getElementById(`product-csv-file-${shopkeeperId}`);
            if (!fileInput || fileInput.files.length === 0) {
                await Swal.fire('Please select a CSV file to upload.');
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
                    await Swal.fire(data.detail || 'Products uploaded successfully!');
                    location.reload();
                } else {
                    await Swal.fire(data.detail || 'Failed to upload CSV.');
                }
            } catch (err) {
                await Swal.fire('Error uploading CSV.');
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
                    await Swal.fire('Stock updated successfully!');
                    location.reload();
                } else {
                    await Swal.fire('Failed to update stock.');
                }
            } catch (err) {
                await Swal.fire('Error updating stock.');
            }
        }

        async function deleteProduct(productId, productName) {
            const _swalRes23946 = await Swal.fire({ text: `Are you sure you want to delete product '${productName}'? This will soft-delete it so historical receipts and analytics are preserved, but it will be hidden from the active catalog and POS.`, icon: 'warning', showCancelButton: true, confirmButtonColor: 'var(--primary)', cancelButtonColor: '#C53030' });
            if (_swalRes23946.isConfirmed) {
                try {
                    const response = await fetch('/api/products/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: productId })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        await Swal.fire(data.detail || 'Product deleted successfully!');
                        location.reload();
                    } else {
                        await Swal.fire(data.detail || 'Failed to delete product.');
                    }
                } catch (err) {
                    await Swal.fire('Error deleting product.');
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
                    await Swal.fire(data.detail || 'Photo updated successfully!');
                    location.reload();
                } else {
                    await Swal.fire(data.detail || 'Failed to update photo.');
                }
            } catch (err) {
                await Swal.fire('Error uploading photo.');
            }
            input.value = '';
        }

        async function addUser() {
            const username = document.getElementById('new-username').value.trim();
            const password = document.getElementById('new-password').value;
            const role = document.getElementById('new-role').value;

            if (!username || !password) {
                await Swal.fire('Please provide username and password.');
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
                    await Swal.fire(data.detail || 'User added successfully!');
                    location.reload();
                } else {
                    await Swal.fire(data.detail || 'Failed to add user.');
                }
            } catch (err) {
                await Swal.fire('Error adding user.');
            }
        }

        async function resetPassword(userId, username) {
            const { value: newPwd } = await Swal.fire({ title: `Enter new password for ${username}:`, input: 'text', showCancelButton: true });
            if (!newPwd) return;

            try {
                const response = await fetch('/api/users/update_password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, new_password: newPwd })
                });
                const data = await response.json();
                if (response.ok) {
                    await Swal.fire(data.detail || 'Password updated successfully!');
                } else {
                    await Swal.fire(data.detail || 'Failed to update password.');
                }
            } catch (err) {
                await Swal.fire('Error updating password.');
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
                    await Swal.fire('User updated successfully!');
                    location.reload();
                } else {
                    await Swal.fire(data.detail || 'Failed to update user.');
                }
            } catch (err) {
                await Swal.fire('Error updating user.');
            }
        }

        async function deleteUser(userId, username) {
            const _swalRes29872 = await Swal.fire({ text: `Are you sure you want to permanently DELETE user '${username}'?`, icon: 'warning', showCancelButton: true, confirmButtonColor: 'var(--primary)', cancelButtonColor: '#C53030' });
            if (_swalRes29872.isConfirmed) {
                try {
                    const response = await fetch('/api/users/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: userId })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        await Swal.fire('User deleted successfully!');
                        location.reload();
                    } else {
                        await Swal.fire(data.detail || 'Failed to delete user.');
                    }
                } catch (err) {
                    await Swal.fire('Error deleting user.');
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
                                    <td>${escapeHTML(item.product_name)}</td>
                                    <td style="text-align: center;">${item.qty}</td>
                                    <td style="text-align: right;">₹${item.revenue.toFixed(2)}</td>
                                </tr>
                            `;
                        });
                    }

                    document.getElementById('analytics-modal').style.display = 'flex';
                } else {
                    await Swal.fire(data.detail || 'Failed to fetch analytics.');
                }
            } catch (err) {
                await Swal.fire('Error fetching analytics.');
            }
        }

        async function viewShopAnalyticsToday(shopId) {
            try {
                const response = await fetch(`/api/analytics/shop/${shopId}/today`);
                const data = await response.json();
                if (response.ok) {
                    document.getElementById('analytics-shop-name').innerText = `${data.shop_name} - Analytics`;
                    document.getElementById('analytics-total-sales').innerText = `${data.total_sales} Bills`;
                    document.getElementById('analytics-total-revenue').innerText = `₹${data.total_revenue.toFixed(2)}`;

                    const tbody = document.getElementById('analytics-breakdown-body');
                    tbody.innerHTML = '';
                    if (data.breakdown.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #718096;">No sales data available today.</td></tr>';
                    } else {
                        data.breakdown.forEach(item => {
                            tbody.innerHTML += `
                                <tr>
                                    <td>${escapeHTML(item.product_name)}</td>
                                    <td style="text-align: center;">${item.qty}</td>
                                    <td style="text-align: right;">₹${item.revenue.toFixed(2)}</td>
                                </tr>
                            `;
                        });
                    }

                    document.getElementById('analytics-modal').style.display = 'flex';
                } else {
                    await Swal.fire(data.detail || 'Failed to fetch analytics.');
                }
            } catch (err) {
                await Swal.fire('Error fetching analytics.');
            }
        }

        async function hardDeleteUser(userId, username) {
            const _swalRes1 = await Swal.fire({ text: `DANGER: Are you absolutely sure you want to PERMANENTLY delete the archived account '${username}'? This will erase all their products, bills, and history. This CANNOT be undone.`, icon: 'warning', showCancelButton: true, confirmButtonColor: 'var(--primary)', cancelButtonColor: '#C53030' });
            if (!_swalRes1.isConfirmed) return;

            const _swalRes2 = await Swal.fire({ text: `FINAL WARNING: Have you exported necessary reports? Press OK to proceed with wiping all data for '${username}'.`, icon: 'warning', showCancelButton: true, confirmButtonColor: 'var(--primary)', cancelButtonColor: '#C53030' });
            if (!_swalRes2.isConfirmed) return;

            try {
                const response = await fetch('/api/users/hard_delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId })
                });
                const data = await response.json();
                if (response.ok) {
                    await Swal.fire("Account and history permanently deleted.");
                    location.reload();
                } else {
                    await Swal.fire(data.detail || 'Failed to permanently delete user.');
                }
            } catch (err) {
                await Swal.fire('Network error during permanent deletion.');
        }
    }

function openEditProductModal(id, currentName, currentStock, shopkeeperId, currentPrice, currentRateQty) {
    document.getElementById("edit-product-id").value = id;
    document.getElementById("edit-product-name").value = currentName;
    document.getElementById("edit-product-price").value = currentPrice || "";
    document.getElementById("edit-product-rate-qty").value = currentRateQty || "";
    document.getElementById("edit-product-stock").value = currentStock;
    document.getElementById("edit-shopkeeper-id").value = shopkeeperId;
    document.getElementById("edit-product-image").value = "";
    document.getElementById("edit-product-modal").style.display = "flex";
}

function closeEditProductModal() {
    document.getElementById("edit-product-modal").style.display = "none";
}

async function submitEditProduct() {
    const id = document.getElementById("edit-product-id").value;
    const name = document.getElementById("edit-product-name").value.trim();
    const price = document.getElementById("edit-product-price").value;
    const rateQty = document.getElementById("edit-product-rate-qty").value;
    const stock = document.getElementById("edit-product-stock").value || 0;
    const shopkeeperId = document.getElementById("edit-shopkeeper-id").value;
    const fileInput = document.getElementById("edit-product-image");
    
    if (!name) {
        await Swal.fire("Product name cannot be empty.");
        return;
    }
    
    const formData = new FormData();
    formData.append("name", name);
    if (price) formData.append("price", parseFloat(price));
    if (rateQty) formData.append("rate_qty", parseFloat(rateQty));
    formData.append("stock", stock);
    formData.append("shopkeeper_id", shopkeeperId);
    if (fileInput.files[0]) {
        formData.append("file", fileInput.files[0]);
    }
    
    try {
        const response = await fetch(`/api/products/${id}/edit`, {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        
        if (response.ok) {
            await Swal.fire(data.detail || "Product updated successfully!");
            location.reload();
        } else {
            await Swal.fire(data.detail || "Failed to update product.");
        }
    } catch (err) {
        await Swal.fire("Error updating product.");
    }
}

function toggleMobileMenu() {
    const controls = document.querySelector(".header-controls");
    const overlay = document.getElementById("mobile-menu-overlay");
    if (controls) controls.classList.toggle("active");
    if (overlay) overlay.classList.toggle("active");
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
}

async function viewShopExpensesToday(shopId, shopName) {
    document.getElementById('expense-shop-name').innerText = shopName;
    const container = document.getElementById('expense-list-container');
    container.innerHTML = '<div style="text-align: center; padding: 20px; color: #718096;">Loading...</div>';
    
    openModal('shop-expenses-modal');
    
    try {
        const res = await fetch(`/api/admin/expenses/today/${shopId}`);
        const data = await res.json();
        
        if (res.ok) {
            if (data.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 20px; color: #718096;">No expenses found for today.</div>';
                return;
            }
            
            let html = '<ul style="list-style: none; padding: 0;">';
            let total = 0;
            data.forEach(exp => {
                total += exp.amount;
                html += `
                    <li style="padding: 10px 0; border-bottom: 1px solid #EDF2F7; display: flex; justify-content: space-between;">
                        <div style="display: flex; flex-direction: column;">
                            <span style="font-weight: bold; color: #2D3748;">${escapeHTML(exp.reason)}</span>
                            <span style="font-size: 11px; color: #A0AEC0;">${exp.timestamp}</span>
                        </div>
                        <span style="color: #E53E3E; font-weight: 600;">₹${exp.amount.toFixed(2)}</span>
                    </li>
                `;
            });
            html += `</ul>
                <div style="margin-top: 16px; padding-top: 12px; border-top: 2px dashed #E2E8F0; text-align: right; font-size: 16px;">
                    <strong>Total: <span style="color: #E53E3E;">₹${total.toFixed(2)}</span></strong>
                </div>
            `;
            container.innerHTML = html;
        } else {
            container.innerHTML = `<div style="text-align: center; padding: 20px; color: #E53E3E;">Failed to load expenses.</div>`;
        }
    } catch (err) {
        container.innerHTML = `<div style="text-align: center; padding: 20px; color: #E53E3E;">Network error while fetching.</div>`;
    }
}

// Close modals when clicking outside or pressing ESC
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const activeModals = document.querySelectorAll('.modal-overlay');
        activeModals.forEach(m => {
            if (m.style.display === 'flex' || m.classList.contains('active')) {
                closeModal(m.id);
                m.classList.remove('active');
            }
        });
        
        // Handle specific modals that might not use standard open/close
        const editModal = document.getElementById('edit-product-modal');
        if (editModal && editModal.style.display === 'flex') {
            closeEditProductModal();
        }
        
        const shopSelector = document.getElementById('shop-selector-modal');
        if (shopSelector && shopSelector.classList.contains('active')) {
            shopSelector.classList.remove('active');
        }
    }
});

document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal(e.target.id);
        e.target.classList.remove('active');
    }
    
    // For edit product modal which uses inline styles sometimes instead of classes
    const editModal = document.getElementById('edit-product-modal');
    if (editModal && e.target === editModal) {
        closeEditProductModal();
    }
});