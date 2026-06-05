
        const ACTIVE_SHOPKEEPER_ID = ACTIVE_CASHIER_ID;
        let cart = [];
        let bluetoothDevice = null;
        let printCharacteristic = null;
        let activeBillData = null;

        // Cash Tracker Logic for Factory
        function switchTab(tabId) {
            if (tabId === 'pos') {
                document.getElementById('pos-view').style.display = '';
                document.getElementById('cash-view').style.display = 'none';
                
                document.getElementById('tab-pos').style.backgroundColor = 'var(--primary)';
                document.getElementById('tab-pos').style.color = 'white';
                document.getElementById('tab-cash').style.backgroundColor = '#EDF2F7';
                document.getElementById('tab-cash').style.color = '#2D3748';
            } else {
                document.getElementById('pos-view').style.display = 'none';
                document.getElementById('cash-view').style.display = 'grid';
                
                document.getElementById('tab-pos').style.backgroundColor = '#EDF2F7';
                document.getElementById('tab-pos').style.color = '#2D3748';
                document.getElementById('tab-cash').style.backgroundColor = 'var(--primary)';
                document.getElementById('tab-cash').style.color = 'white';
                
                fetchCashData();
            }
        }

        async function fetchCashData() {
            try {
                const response = await fetch(`/api/cash-transactions?shopkeeper_id=${ACTIVE_SHOPKEEPER_ID}`);
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('cash-balance').textContent = `₹${data.balance.toFixed(2)}`;
                    document.getElementById('cash-sales').textContent = `₹${data.cash_sales.toFixed(2)}`;
                    document.getElementById('cash-in').textContent = `+₹${data.total_in.toFixed(2)}`;
                    document.getElementById('cash-out').textContent = `-₹${data.total_out.toFixed(2)}`;
                    
                    const container = document.getElementById('cash-history-container');
                    container.innerHTML = '';
                    
                    if (data.transactions.length === 0) {
                        container.innerHTML = '<div style="text-align: center; color: #A0AEC0; margin-top: 20px; font-size: 14px;">No cash transactions today</div>';
                        return;
                    }
                    
                    data.transactions.forEach(t => {
                        const isOut = t.type === 'OUT';
                        const color = isOut ? '#E53E3E' : '#319795';
                        const sign = isOut ? '-' : '+';
                        
                        const txTime = new Date(t.timestamp);
                        const now = new Date();
                        const diffSecs = (now - txTime) / 1000;
                        const canRevert = diffSecs < 180;
                        
                        const timeStr = txTime.toLocaleString(undefined, {
                            year: 'numeric', month: '2-digit', day: '2-digit', 
                            hour: '2-digit', minute: '2-digit'
                        });
                        
                        const card = document.createElement('div');
                        card.style.padding = '12px';
                        card.style.borderBottom = '1px solid #E2E8F0';
                        card.style.display = 'flex';
                        card.style.justifyContent = 'space-between';
                        card.style.alignItems = 'center';
                        
                        let revertBtnHtml = '';
                        if (canRevert) {
                            revertBtnHtml = `<button onclick="revertCashTransaction(${t.id})" style="margin-left: 12px; background: none; border: none; color: #E53E3E; cursor: pointer; font-size: 12px; text-decoration: underline;">Revert</button>`;
                        }
                        
                        card.innerHTML = `
                            <div>
                                <div style="font-weight: 600; font-size: 14px;">${t.type === 'IN' ? 'Money IN' : 'Money OUT'}</div>
                                <div style="font-size: 12px; color: #718096;">${t.description || 'No description'}</div>
                                <div style="font-size: 10px; color: #A0AEC0; margin-top: 4px;">${timeStr}</div>
                            </div>
                            <div style="display: flex; align-items: center;">
                                <div style="font-weight: bold; font-size: 16px; color: ${color};">
                                    ${sign}₹${t.amount.toFixed(2)}
                                </div>
                                ${revertBtnHtml}
                            </div>
                        `;
                        container.appendChild(card);
                    });
                }
            } catch (err) {
                console.error("Error fetching cash data", err);
            }
        }

        async function submitCashTransaction() {
            const amount = parseFloat(document.getElementById('cash-amount').value);
            const type = document.getElementById('cash-type').value;
            const desc = document.getElementById('cash-desc').value;
            
            if (isNaN(amount) || amount <= 0) {
                await Swal.fire("Please enter a valid amount greater than 0");
                return;
            }
            
            const payload = {
                amount: amount,
                type: type,
                description: desc,
                shopkeeper_id: ACTIVE_SHOPKEEPER_ID
            };
            
            try {
                const response = await fetch('/api/cash-transactions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('cash-amount').value = '';
                    document.getElementById('cash-desc').value = '';
                    fetchCashData();
                } else {
                    await Swal.fire("Failed to record cash transaction: " + (data.detail || 'Unknown error'));
                }
            } catch (err) {
                console.error("Error submitting cash transaction", err);
                await Swal.fire("Network error while submitting cash transaction.");
            }
        }
        
        async function revertCashTransaction(txId) {
            const _swalRes6861 = await Swal.fire({ text: "Are you sure you want to revert this transaction?", icon: 'warning', showCancelButton: true, confirmButtonColor: 'var(--primary)', cancelButtonColor: '#C53030' });
        if (!_swalRes6861.isConfirmed) return;
            try {
                const response = await fetch(`/api/cash-transactions/${txId}`, {
                    method: 'DELETE'
                });
                const data = await response.json();
                if (data.status === 'success') {
                    fetchCashData();
                } else {
                    await Swal.fire("Failed to revert: " + (data.detail || 'Unknown error'));
                }
            } catch(err) {
                console.error("Error reverting", err);
                await Swal.fire("Network error while reverting.");
            }
        }

        function addSolid(id, name, price, unit) {
            const existing = cart.find(i => i.id === id);
            if (existing) {
                existing.qty += 1;
            } else {
                cart.push({ id, name, price, qty: 1, unit, type: 'solid' });
            }
            renderCart();
        }

        function addLiquid(id, name, price) {
            const existing = cart.find(i => i.id === id);
            if (existing) {
                existing.qty += 1;
            } else {
                cart.push({ id, name, price, qty: 1, unit: 'Ltrs', type: 'liquid', packaging_type: 'loose', bottle_type: 'Type 1', bottle_count: 1 });
            }
            renderCart();
        }

        function removeFromCart(id) {
            cart = cart.filter(i => i.id !== id);
            renderCart();
        }

        function updateRate(id, newRate) {
            const item = cart.find(i => i.id === id);
            if (!item) return;
            const val = parseFloat(newRate);
            if (isNaN(val) || val < 0) return;
            item.price = val;
            calculateTotal();
            renderCart(); // re-render to update line total display
        }

        function updateQty(id, newQty) {
            const item = cart.find(i => i.id === id);
            if (!item) return;
            const val = parseFloat(newQty);
            if (isNaN(val) || val <= 0) {
                removeFromCart(id);
                return;
            }
            item.qty = val;
            calculateTotal();
            renderCart(); // re-render to update line total display
        }


        function updatePackaging(id, newPkg) {
            const item = cart.find(i => i.id === id);
            if (!item) return;
            item.packaging_type = newPkg;
            renderCart();
        }

        function updateBottleCount(id, count) {
            const item = cart.find(i => i.id === id);
            if (!item) return;
            item.bottle_count = parseInt(count) || 0;
            renderCart();
        }

        function updateBottleType(id, newBtlType) {
            const item = cart.find(i => i.id === id);
            if (!item) return;
            item.bottle_type = newBtlType;
            renderCart();
        }

        function renderCart() {
            const container = document.getElementById('cart-items');
            if (cart.length === 0) {
                container.innerHTML = '<div style="text-align: center; color: #A0AEC0; margin-top: 40px; font-size: 14px;">Tap products to add them to cart</div>';
                calculateTotal();
                return;
            }

            let html = '';
            cart.forEach(item => {
                const step = item.type === 'liquid' ? 'any' : '1';
                html += `
                <div style="padding:16px 0; border-bottom:1px solid #E2E8F0; display: flex; flex-direction: column; gap: 10px;">
                    <div style="font-weight:700; font-size:18px; color:#2D3748; word-break: break-word;">
                        ${item.name}
                    </div>
                    <div style="display:flex; align-items:center; justify-content:space-between; gap: 8px; flex-wrap: wrap;">
                        <div style="display:flex; align-items:center; gap:4px;">
                            <input type="number" step="${step}" min="0.01" value="${item.qty}" 
                                   style="width:70px; padding:6px; text-align:center; border:1px solid #CBD5E0; border-radius:4px; height:36px; font-weight:700; font-size:16px; outline:none;"
                                   onchange="updateQty(${item.id}, this.value)">
                            <span style="font-size:14px; font-weight:600; color:#A0AEC0;">${item.unit}</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:4px;">
                            <input type="number" step="any" min="0" value="${item.price}"
                                   style="width:85px; padding:6px; font-size:16px; font-weight:600; text-align:right; border:1px solid #CBD5E0; border-radius:4px; height:36px; outline:none;"
                                   onfocus="if(this.value==='0') this.value='';"
                                   onchange="updateRate(${item.id}, this.value)">
                        </div>
                        <div style="font-size:18px; font-weight:bold; color:var(--primary); text-align: right; min-width: 70px;">
                            ₹${(item.price * item.qty).toFixed(2)}
                        </div>
                        <div>
                            <button class="btn-remove" style="background:#E53E3E; color:white; border:none; border-radius:4px; cursor:pointer; width:36px; height:36px; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:18px;" onclick="removeFromCart(${item.id})">X</button>
                        </div>
                    </div>
                    ${item.type === 'liquid' ? `
                    <div style="display:flex; gap: 8px; align-items: center; margin-top: 4px;">
                        <select style="padding: 6px; font-size: 14px; font-weight:600; border: 1px solid #CBD5E0; border-radius: 4px; height:36px;" onchange="updatePackaging(${item.id}, this.value)">
                            <option value="loose" ${item.packaging_type === 'loose' ? 'selected' : ''}>Loose</option>
                            <option value="bottle" ${item.packaging_type === 'bottle' ? 'selected' : ''}>Bottle</option>
                        </select>
                        ${item.packaging_type === 'bottle' ? `
                        <select style="padding: 6px; font-size: 14px; font-weight:600; border: 1px solid #CBD5E0; border-radius: 4px; height:36px;" onchange="updateBottleType(${item.id}, this.value)">
                            <option value="Type 1" ${item.bottle_type === 'Type 1' ? 'selected' : ''}>Type 1</option>
                            <option value="Type 2" ${item.bottle_type === 'Type 2' ? 'selected' : ''}>Type 2</option>
                            <option value="Type 3" ${item.bottle_type === 'Type 3' ? 'selected' : ''}>Type 3</option>
                        </select>` : ''}
                    </div>
                    ` : ''}
                </div>
                `;
            });
            container.innerHTML = html;
            calculateTotal();
        }

        let subtotal = 0;
        let finalTotal = 0;
        let discount = 0;

        function calculateTotal() {
            subtotal = cart.reduce((acc, item) => acc + (item.price * item.qty), 0);
            discount = parseFloat(document.getElementById('discount-input').value) || 0;
            finalTotal = Math.max(0, subtotal - discount);

            document.getElementById('cart-subtotal').innerText = `₹${subtotal.toFixed(2)}`;
            document.getElementById('cart-final-total').innerText = `₹${finalTotal.toFixed(2)}`;
        }

        async function submitBill() {
            if (cart.length === 0) {
                await Swal.fire('Cart is empty.');
                return;
            }
            const paymentMode = document.getElementById('payment-mode').value;
            const payload = {
                shopkeeper_id: ACTIVE_CASHIER_ID,
                items: cart.map(i => ({ id: i.id, qty: i.qty, price: i.price, packaging_type: i.packaging_type, bottle_type: i.bottle_type, bottle_count: i.bottle_count || 0 })),
                discount: discount,
                payment_mode: paymentMode
            };

            try {
                const res = await fetch('/api/bills', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    cart = [];
                    renderCart();
                    document.getElementById('discount-input').value = 0;
                    await loadBillForReceipt(data.bill_id);
                    loadBillHistory();
                } else {
                    await Swal.fire(data.detail || 'Checkout failed.');
                }
            } catch (err) {
                await Swal.fire('Network/Server error during checkout.');
            }
        }

        async function loadBillHistory() {
            const container = document.getElementById('bill-history-container');
            try {
                const response = await fetch(`/api/bills/history?shopkeeper_id=${ACTIVE_CASHIER_ID}`);
                const data = await response.json();

                if (response.ok) {
                    container.innerHTML = '';
                    if (data.bills.length === 0) {
                        container.innerHTML = '<div style="text-align: center; color: #A0AEC0; margin-top: 20px; font-size: 14px;">No recent bills</div>';
                        return;
                    }

                    data.bills.forEach(bill => {
                        const card = document.createElement('div');
                        card.className = 'history-card';
                        if (bill.is_cancelled) {
                            card.style.opacity = '0.65';
                            card.style.borderLeft = '4px solid #E53E3E';
                            card.style.position = 'relative';
                            card.style.overflow = 'hidden';
                        }

                        const badgeHtml = bill.is_cancelled
                            ? '<span style="background-color: #FFF5F5; color: #E53E3E; border: 1px solid #FEB2B2; font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 800; letter-spacing: 0.5px;">CANCELLED</span>'
                            : '';

                        const priceStyle = bill.is_cancelled ? 'text-decoration: line-through; color: #A0AEC0;' : '';
                        const titleStyle = bill.is_cancelled ? 'text-decoration: line-through; color: #718096;' : '';

                        const actionButtonsHtml = bill.is_cancelled ? `
                            <button class="btn btn-small" style="background-color: #718096; color: white; width: 100%; display: flex; align-items: center; justify-content: center; gap: 4px;" onclick="loadBillForReceipt(${bill.id})">
                                 Print Void Receipt
                            </button>
                        ` : `
                            <button class="btn btn-small" style="background-color: var(--primary); color: white; width: 100%; display: flex; align-items: center; justify-content: center; gap: 4px;" onclick="loadBillForReceipt(${bill.id})">
                                 Print Receipt
                            </button>
                            <div style="display: flex; gap: 6px; width: 100%;">
                                <button class="btn btn-secondary btn-small" style="flex: 1;" onclick="revertBillFromHistory(${bill.id}, ${bill.bill_number || bill.id})">
                                    ↩ Edit
                                </button>
                                <button class="btn btn-destructive btn-small" style="flex: 1;" onclick="cancelBillFromHistory(${bill.id}, ${bill.bill_number || bill.id})">
                                     Cancel
                                </button>
                            </div>
                        `;

                        card.innerHTML = `
                            <div class="history-card-header" style="display: flex; align-items: center; justify-content: space-between; gap: 8px; width: 100%;">
                                <span style="${titleStyle}">Bill #${bill.bill_number || bill.id}</span>
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    ${badgeHtml}
                                    <span style="${priceStyle}">₹${bill.final_amount.toFixed(2)}</span>
                                </div>
                            </div>
                            <div class="history-card-details">
                                ${bill.timestamp} | ${bill.payment_mode}
                            </div>
                            <div style="display: flex; gap: 6px; flex-direction: column;">
                                ${actionButtonsHtml}
                            </div>
                        `;
                        container.appendChild(card);
                    });
                }
            } catch (err) {
                console.error("Error fetching bill history", err);
                container.innerHTML = '<div style="color: red; text-align: center; font-size: 12px;">Failed to load history</div>';
            }
        }

        async function revertBillFromHistory(billId, displayNo) {
            const label = displayNo ? `#${displayNo}` : `#${billId}`;
            const _swalRes20502 = await Swal.fire({ text: `Are you sure you want to revert Bill ${label}? The stock will be restored and you can edit the items in the cart.`, icon: 'warning', showCancelButton: true, confirmButtonColor: 'var(--primary)', cancelButtonColor: '#C53030' });
        if (!_swalRes20502.isConfirmed) return;

            try {
                const response = await fetch(`/api/bills/${billId}/revert`, { method: 'POST' });
                const data = await response.json();

                if (response.ok) {
                    // Load items into active cart. Map structure to factory cart item format
                    cart = data.items.map(i => ({
                        id: i.id,
                        name: i.name,
                        price: i.price,
                        qty: i.qty,
                        unit: 'Unit', // fallback unit
                        type: 'solid' // fallback type
                    }));
                    const discountInput = document.getElementById('discount-input');
                    if (discountInput) {
                        discountInput.value = data.discount || 0;
                    }
                    renderCart();
                    loadBillHistory();
                } else {
                    await Swal.fire(data.detail || "Failed to revert bill");
                }
            } catch (err) {
                await Swal.fire("Error connecting to server.");
                console.error(err);
            }
        }

        async function cancelBillFromHistory(billId, displayNo) {
            const label = displayNo ? `#${displayNo}` : `#${billId}`;
            const _swalRes21960 = await Swal.fire({ text: `Are you sure you want to CANCEL Bill ${label}? The stock will be restored, and the bill will be marked as cancelled.`, icon: 'warning', showCancelButton: true, confirmButtonColor: 'var(--primary)', cancelButtonColor: '#C53030' });
        if (!_swalRes21960.isConfirmed) return;

            try {
                const response = await fetch(`/api/bills/${billId}/revert`, { method: 'POST' });
                const data = await response.json();

                if (response.ok) {
                    await Swal.fire(`Bill ${label} has been cancelled and stock restored.`);
                    loadBillHistory();
                } else {
                    await Swal.fire(data.detail || "Failed to cancel bill");
                }
            } catch (err) {
                await Swal.fire("Error connecting to server.");
                console.error(err);
            }
        }
        async function loadBillForReceipt(billId) {
            try {
                const res = await fetch(`/api/bills/${billId}`);
                const data = await res.json();
                if (res.ok && data.bill) {
                    activeBillData = data.bill;
                    renderReceiptHTML(data.bill);
                    document.getElementById('receipt-preview-modal').classList.add('active');
                }
            } catch (e) {
                await Swal.fire('Error loading receipt data.');
            }
        }

        function renderReceiptHTML(bill) {
            const container = document.getElementById('receipt-container-preview');
            let itemsHtml = '';
            bill.items.forEach(item => {
                itemsHtml += `
                <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                    <div style="flex: 2;">${item.name}</div>
                    <div style="flex: 1; text-align: center;">${item.quantity}</div>
                    <div style="flex: 1; text-align: right;">₹${item.total.toFixed(2)}</div>
                </div>
                `;
            });

            container.innerHTML = `
            <div style="text-align: center; border-bottom: 1px dashed #000; padding-bottom: 8px; margin-bottom: 8px;">
                <h2 style="margin: 0; font-size: 16px;">PONNANGAI</h2>
                <h2 style="margin: 0; font-size: 16px;">ENTERPRISES</h2>
                <p style="margin: 2px 0; font-size: 11px;">Factory Outlet Sales</p>
                <p style="margin: 2px 0; font-size: 11px;">Date: ${bill.timestamp}</p>
                <p style="margin: 2px 0; font-size: 11px;">Bill No: #${bill.bill_number} | Mode: ${bill.payment_mode}</p>
            </div>
            <div style="border-bottom: 1px dashed #000; padding-bottom: 4px; margin-bottom: 8px; font-weight: bold; display: flex; font-size: 11px;">
                <div style="flex: 2;">Item</div>
                <div style="flex: 1; text-align: center;">Qty</div>
                <div style="flex: 1; text-align: right;">Amount</div>
            </div>
            <div style="border-bottom: 1px dashed #000; padding-bottom: 6px; margin-bottom: 8px;">
                ${itemsHtml}
            </div>
            <div style="font-size: 12px; display: flex; flex-direction: column; gap: 3px; align-items: flex-end; margin-bottom: 8px;">
                <div>Subtotal: ₹${bill.total_amount.toFixed(2)}</div>
                ${bill.discount > 0 ? `<div>Discount: ₹${bill.discount.toFixed(2)}</div>` : ''}
                <div style="font-weight: bold; font-size: 14px;">Total Paid: ₹${bill.final_amount.toFixed(2)}</div>
            </div>
            <div style="text-align: center; font-size: 11px; margin-top: 10px;">
                <p style="margin: 0; font-weight: bold;">Thank You! Visit Again</p>
                <p style="margin: 2px 0; font-size: 9px;">Cashier: ${bill.cashier_name}</p>
            </div>
            `;

            document.getElementById('receipt-container').innerHTML = container.innerHTML;
        }

        function closeReceiptModal() {
            document.getElementById('receipt-preview-modal').classList.remove('active');
            activeBillData = null;
        }

        // Printer Bluetooth logic
        function openPrinterModal() { document.getElementById('printer-settings-modal').classList.add('active'); }
        function closePrinterModal() { document.getElementById('printer-settings-modal').classList.remove('active'); }

        // --- Web Bluetooth Direct ESC/POS Driverless Engine ---

        async function connectToDevice(device) {
            const statusText = document.getElementById('bt-status-text');
            statusText.innerHTML = `<span style="color: #D69E2E;">🟡 Connecting to ${device.name || 'Printer'}...</span>`;

            bluetoothDevice = device;
            bluetoothDevice.addEventListener('gattserverdisconnected', onDisconnected);

            const server = await bluetoothDevice.gatt.connect();
            statusText.innerHTML = '<span style="color: #D69E2E;">🟡 Discovering printer services...</span>';

            let service = null;
            const serviceUUIDs = [
                '0000ffe0-0000-1000-8000-00805f9b34fb', // Standard BLE Serial
                '000018f0-0000-1000-8000-00805f9b34fb', // Standard Bluetooth Thermal printer service
                '49535343-fe7d-4ae5-8fa9-9fafd205e455'  // Microchip BLE module
            ];

            for (const uuid of serviceUUIDs) {
                try {
                    service = await server.getPrimaryService(uuid);
                    if (service) break;
                } catch (e) {
                    console.log(`Service ${uuid} not discovered, checking next service...`);
                }
            }

            if (!service) {
                try {
                    const services = await server.getPrimaryServices();
                    if (services.length > 0) {
                        service = services[0];
                    }
                } catch (e) {
                    console.error("Failed to inspect primary services", e);
                }
            }

            if (!service) {
                throw new Error("No print service discovered on this Niyama device.");
            }

            statusText.innerHTML = '<span style="color: #D69E2E;">🟡 Initializing data channel...</span>';
            const characteristics = await service.getCharacteristics();
            for (const char of characteristics) {
                if (char.properties.write || char.properties.writeWithoutResponse) {
                    printCharacteristic = char;
                    break;
                }
            }

            if (!printCharacteristic) {
                throw new Error("No write capability found on this Niyama device.");
            }

            statusText.innerHTML = `<span style="color: #48BB78; font-weight: bold;">🟢 Connected to ${bluetoothDevice.name}</span>`;
            document.getElementById('header-printer-status').innerText = 'Connected';
            document.getElementById('bt-test-btn').style.display = 'inline-block';
        }

        async function connectBluetooth() {
            const statusText = document.getElementById('bt-status-text');
            statusText.innerHTML = '<span style="color: #D69E2E;">🟡 Connecting...</span>';
            try {
                if (!navigator.bluetooth) {
                    throw new Error("Web Bluetooth API is not supported in this browser.");
                }

                const options = {
                    acceptAllDevices: true,
                    optionalServices: [
                        '0000ffe0-0000-1000-8000-00805f9b34fb',
                        '000018f0-0000-1000-8000-00805f9b34fb',
                        '49535343-fe7d-4ae5-8fa9-9fafd205e455'
                    ]
                };

                const device = await navigator.bluetooth.requestDevice(options);
                await connectToDevice(device);
            } catch (err) {
                console.error("Bluetooth connection failed", err);
                statusText.innerHTML = `<span style="color: #E53E3E; font-weight: bold;"> Connection Failed</span>`;
                document.getElementById('header-printer-status').innerText = 'Disconnected';
                printCharacteristic = null;
                bluetoothDevice = null;
            }
        }

        async function autoConnectBluetooth() {
            if (!navigator.bluetooth || !navigator.bluetooth.getDevices) {
                return;
            }
            const statusText = document.getElementById('bt-status-text');
            try {
                const devices = await navigator.bluetooth.getDevices();
                if (devices.length > 0) {
                    statusText.innerHTML = `<span style="color: #D69E2E;">🟡 Auto-connecting to paired printer...</span>`;
                    await connectToDevice(devices[0]);
                }
            } catch (err) {
                console.error("Auto-connect failed", err);
                statusText.innerHTML = '<span style="color: #718096; font-weight: bold;"> Disconnected</span>';
            }
        }

        function onDisconnected() {
            const statusText = document.getElementById('bt-status-text');
            statusText.innerHTML = '<span style="color: #718096; font-weight: bold;"> Disconnected</span>';
            document.getElementById('header-printer-status').innerText = 'Disconnected';
            printCharacteristic = null;
            bluetoothDevice = null;
            document.getElementById('bt-test-btn').style.display = 'none';
            // Auto-reconnect in 2 seconds
            setTimeout(autoConnectBluetooth, 2000);
        }

        // --- Lightweight ESC/POS Command Packetizer ---
        class EscPosEncoder {
            constructor(charLimit = 32) { // Defaulting to 32 chars for 58mm
                this.charLimit = charLimit;
                this.buffer = [];
            }

            addRaw(bytes) {
                this.buffer = this.buffer.concat(bytes);
                return this;
            }

            init() {
                this.addRaw([0x1B, 0x40]);
                return this;
            }

            align(type) {
                const alignMap = { left: 0x00, center: 0x01, right: 0x02 };
                this.addRaw([0x1B, 0x61, alignMap[type] || 0x00]);
                return this;
            }

            bold(enable) {
                this.addRaw([0x1B, 0x45, enable ? 0x01 : 0x00]);
                return this;
            }

            fontSize(size) {
                if (size === 'double') {
                    this.addRaw([0x1D, 0x21, 0x11]); // Double height + width
                } else {
                    this.addRaw([0x1D, 0x21, 0x00]); // Normal size
                }
                return this;
            }

            text(str) {
                let cleanStr = str.replace(/₹/g, 'Rs.');
                const encoder = new TextEncoder();
                const encoded = encoder.encode(cleanStr);
                this.buffer = this.buffer.concat(Array.from(encoded));
                return this;
            }

            line(str = '') {
                this.text(str + '\n');
                return this;
            }

            header(str) {
                this.align('center').fontSize('double').bold(true).line(str).fontSize('normal').bold(false).align('left');
                return this;
            }

            divider() {
                this.line('-'.repeat(this.charLimit));
                return this;
            }

            row(left, right) {
                const spaceCount = this.charLimit - (left.length + right.length);
                if (spaceCount > 0) {
                    this.line(left + ' '.repeat(spaceCount) + right);
                } else if (spaceCount === 0) {
                    this.line(left + right);
                } else {
                    const maxLeftLen = this.charLimit - right.length - 1;
                    const truncatedLeft = left.substring(0, maxLeftLen);
                    const extraSpaces = this.charLimit - (truncatedLeft.length + right.length);
                    this.line(truncatedLeft + ' '.repeat(extraSpaces) + right);
                }
                return this;
            }

            itemRow(itemName, qty, total) {
                const qtyStr = String(qty);
                const totalStr = String(total);
                const itemColWidth = this.charLimit - 12;
                const qtyColWidth = 4;
                const totalColWidth = 8;

                let words = itemName.split(' ');
                let lines = [];
                let currentLine = '';

                for (let word of words) {
                    if (word.length > itemColWidth) {
                        if (currentLine.length > 0) {
                            lines.push(currentLine);
                            currentLine = '';
                        }
                        while (word.length > itemColWidth) {
                            lines.push(word.substring(0, itemColWidth));
                            word = word.substring(itemColWidth);
                        }
                        currentLine = word;
                    } else if (currentLine.length + word.length + (currentLine.length > 0 ? 1 : 0) <= itemColWidth) {
                        currentLine += (currentLine.length > 0 ? ' ' : '') + word;
                    } else {
                        lines.push(currentLine);
                        currentLine = word;
                    }
                }
                if (currentLine.length > 0) {
                    lines.push(currentLine);
                }
                if (lines.length === 0) lines.push(" ");

                for (let i = 0; i < lines.length; i++) {
                    const leftPadded = lines[i].padEnd(itemColWidth, ' ');
                    if (i === 0) {
                        const centerPadded = qtyStr.padStart(qtyColWidth, ' ');
                        const rightPadded = totalStr.padStart(totalColWidth, ' ');
                        this.line(leftPadded + centerPadded + rightPadded);
                    } else {
                        this.line(leftPadded);
                    }
                }
                return this;
            }

            feed(lines = 3) {
                this.addRaw(new Array(lines).fill(0x0A));
                return this;
            }

            getBytes() {
                return new Uint8Array(this.buffer);
            }
        }

        async function sendPrintData(bytes) {
            const statusText = document.getElementById('bt-status-text');
            if (!printCharacteristic) {
                await Swal.fire("Niyama printer is not connected. Connect via Bluetooth first!");
                return;
            }

            statusText.innerHTML = '<span style="color: #D69E2E; font-weight: bold;">🟡 Sending to printer...</span>';
            const CHUNK_SIZE = 20;
            try {
                for (let i = 0; i < bytes.length; i += CHUNK_SIZE) {
                    const chunk = bytes.slice(i, i + CHUNK_SIZE);
                    await printCharacteristic.writeValue(chunk);
                    await new Promise(resolve => setTimeout(resolve, 35));
                }
                statusText.innerHTML = `<span style="color: #48BB78; font-weight: bold;">🟢 Connected to ${bluetoothDevice.name}</span>`;
            } catch (err) {
                console.error("Wireless printing failed", err);
                statusText.innerHTML = `<span style="color: #E53E3E; font-weight: bold;"> Print Failed: ${err.message || err}</span>`;
            }
        }

        async function printTestReceipt() {
            const encoder = new EscPosEncoder(32);
            encoder.init();
            encoder.align('center').bold(true).fontSize('double').line("Niyama POS").fontSize('normal').bold(false);
            encoder.divider();
            encoder.bold(true).line("Bluetooth Pairing Success!").bold(false);
            encoder.line("Your thermal printer is");
            encoder.line("fully connected & ready.");
            encoder.divider();
            encoder.feed(5);
            encoder.addRaw([0x1D, 0x56, 0x42, 0x00]);

            await sendPrintData(encoder.getBytes());
        }

        async function printActiveBillBluetooth() {
            if (!printCharacteristic || !activeBillData) {
                await Swal.fire("Printer not connected or no active bill to print.");
                return;
            }
            try {
                let bill = activeBillData;
                const encoder = new EscPosEncoder(32); // Use 32 char limit as standard

                encoder.init();
                encoder.header("PONNANGAI");
                encoder.header("ENTERPRISES");
                encoder.align('center').line("Factory Outlet Sales");
                encoder.align('left');

                encoder.row(`Bill: #${bill.bill_number}`, bill.timestamp);
                encoder.line(`Cashier: ${bill.cashier_name} | Mode: ${bill.payment_mode}`);
                encoder.divider();

                encoder.itemRow("Item", "Qty", "Amount");
                encoder.divider();

                for (let item of bill.items) {
                    let qtyStr = `${item.quantity}`;
                    let amtStr = `${item.total.toFixed(2)}`;
                    encoder.itemRow(item.name, qtyStr, amtStr);
                }

                encoder.divider();

                encoder.row("Subtotal:", `${bill.total_amount.toFixed(2)}`);
                if (bill.discount > 0) {
                    encoder.row("Discount:", `${bill.discount.toFixed(2)}`);
                }
                encoder.bold(true).row("Total Paid:", `Rs.${bill.final_amount.toFixed(2)}`).bold(false);

                encoder.feed(1).align('center').line("Thank You! Visit Again");
                encoder.feed(5);
                encoder.addRaw([0x1D, 0x56, 0x42, 0x00]); // Paper Cut

                await sendPrintData(encoder.getBytes());
            } catch (err) {
                console.error("Failed to compile receipt", err);
            }
        }

        function printActiveBillBrowser() {
            window.print();
        }

        function getTodayString() {
            const d = new Date();
            let month = '' + (d.getMonth() + 1), day = '' + d.getDate(), year = d.getFullYear();
            if (month.length < 2) month = '0' + month;
            if (day.length < 2) day = '0' + day;
            return [year, month, day].join('-');
        }

        async function downloadPosReport(type) {
            const today = getTodayString();
            let start = today;
            let end = today;
            
            if (type === 'range') {
                const { value: s } = await Swal.fire({ title: "Enter Start Date (YYYY-MM-DD):", inputValue: today, input: 'text', showCancelButton: true });
                if (!s) return;
                const { value: e } = await Swal.fire({ title: "Enter End Date (YYYY-MM-DD):", inputValue: today, input: 'text', showCancelButton: true });
                if (!e) return;
                start = s;
                end = e;
            }
            
            window.location.href = `/api/reports/daily/export?shopkeeper_id=${ACTIVE_CASHIER_ID}&start_date=${start}&end_date=${end}`;
        }

        window.addEventListener('load', () => {
            loadBillHistory();
        });
    