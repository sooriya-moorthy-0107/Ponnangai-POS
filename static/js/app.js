// Cart Logic
let cart = [];

function addToCart(productId, productName, productPrice) {
    const existingItem = cart.find(item => item.id === productId);
    if (existingItem) {
        existingItem.qty += 1;
    } else {
        cart.push({ id: productId, name: productName, price: productPrice, qty: 1 });
    }
    renderCart();
}

function updateQty(productId, change) {
    const itemIndex = cart.findIndex(item => item.id === productId);
    if (itemIndex > -1) {
        cart[itemIndex].qty += change;
        if (cart[itemIndex].qty <= 0) {
            cart.splice(itemIndex, 1);
        }
        renderCart();
    }
}

function renderCart() {
    const cartItemsContainer = document.getElementById('cart-items');
    if (!cartItemsContainer) return; // Not on shop page

    cartItemsContainer.innerHTML = '';
    let total = 0;

    cart.forEach(item => {
        const itemTotal = item.price * item.qty;
        total += itemTotal;

        const cartItemEl = document.createElement('div');
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
        cartItemsContainer.appendChild(cartItemEl);
    });

    // Update totals
    const discountInput = document.getElementById('discount-input');
    const discount = parseFloat(discountInput ? discountInput.value : 0) || 0;
    const finalAmount = Math.max(0, total - discount);

    document.getElementById('cart-subtotal').textContent = `₹${total.toFixed(2)}`;
    document.getElementById('cart-final-total').textContent = `₹${finalAmount.toFixed(2)}`;
}

// Attach event listener to discount input
document.addEventListener('DOMContentLoaded', () => {
    const discountInput = document.getElementById('discount-input');
    if (discountInput) {
        discountInput.addEventListener('input', renderCart);
    }
    
    // Check for reverted bill data
    const revertCartStr = sessionStorage.getItem('revert_cart');
    const revertDiscountStr = sessionStorage.getItem('revert_discount');
    
    if (revertCartStr) {
        try {
            cart = JSON.parse(revertCartStr);
            if (discountInput && revertDiscountStr) {
                discountInput.value = revertDiscountStr;
            }
            renderCart();
        } catch (e) {
            console.error("Error loading reverted cart", e);
        }
        sessionStorage.removeItem('revert_cart');
        sessionStorage.removeItem('revert_discount');
    }
});

async function submitBill() {
    if (cart.length === 0) {
        alert("Cart is empty!");
        return;
    }

    const discount = parseFloat(document.getElementById('discount-input').value) || 0;
    const paymentMode = document.getElementById('payment-mode').value;

    const payload = {
        items: cart.map(item => ({ id: item.id, qty: item.qty })),
        discount: discount,
        payment_mode: paymentMode
    };

    try {
        const response = await fetch('/api/bills', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        
        if (response.ok) {
            // Clear cart & reset UI
            cart = [];
            renderCart();
            const discountInput = document.getElementById('discount-input');
            if (discountInput) discountInput.value = 0;
            
            // Refresh bill history sidebar
            fetchBillHistory();
            
            // Trigger persistent modal receipt check & automatic printing
            handlePrintFlow(data.bill_id);
        } else {
            alert(data.detail || "Failed to create bill");
        }
    } catch (err) {
        alert("Error connecting to server.");
        console.error(err);
    }
}

// --- Bill History Logic ---
async function fetchBillHistory() {
    const container = document.getElementById('bill-history-container');
    if (!container) return;

    try {
        const response = await fetch('/api/bills/history');
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
                card.innerHTML = `
                    <div class="history-card-header">
                        <span>Bill #${bill.id}</span>
                        <span>₹${bill.final_amount.toFixed(2)}</span>
                    </div>
                    <div class="history-card-details">
                        ${bill.timestamp} | ${bill.payment_mode}
                    </div>
                    <div style="display: flex; gap: 6px; flex-direction: column;">
                        <button class="btn btn-small" style="background-color: var(--primary); color: white; width: 100%; display: flex; align-items: center; justify-content: center; gap: 4px;" onclick="handlePrintFlow(${bill.id})">
                            🖨️ Print Receipt
                        </button>
                        <div style="display: flex; gap: 6px; width: 100%;">
                            <button class="btn btn-secondary btn-small" style="flex: 1;" onclick="revertBillFromHistory(${bill.id})">
                                ↩️ Edit
                            </button>
                            <button class="btn btn-destructive btn-small" style="flex: 1;" onclick="cancelBillFromHistory(${bill.id})">
                                ❌ Cancel
                            </button>
                        </div>
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

async function revertBillFromHistory(billId) {
    if (!confirm(`Are you sure you want to revert Bill #${billId}? The stock will be restored and you can edit the items in the cart.`)) return;
    
    try {
        const response = await fetch(`/api/bills/${billId}/revert`, { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            // Load items into active cart
            cart = data.items;
            const discountInput = document.getElementById('discount-input');
            if (discountInput) {
                discountInput.value = data.discount;
            }
            renderCart();
            // Refresh bill history list
            fetchBillHistory();
        } else {
            alert(data.detail || "Failed to revert bill");
        }
    } catch (err) {
        alert("Error connecting to server.");
        console.error(err);
    }
}

document.addEventListener('DOMContentLoaded', fetchBillHistory);

async function cancelBillFromHistory(billId) {
    if (!confirm(`Are you sure you want to CANCEL Bill #${billId}? The stock will be restored, and the bill will be permanently deleted.`)) return;
    
    try {
        const response = await fetch(`/api/bills/${billId}/revert`, { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            alert(`Bill #${billId} has been cancelled and stock restored.`);
            // Refresh bill history list
            fetchBillHistory();
        } else {
            alert(data.detail || "Failed to cancel bill");
        }
    } catch (err) {
        alert("Error connecting to server.");
        console.error(err);
    }
}

// ==========================================================================
// SPA Printer & Web Bluetooth Global Connection Manager
// ==========================================================================

// Global Printer Connection State
let bluetoothDevice = null;
let writeCharacteristic = null;
let activeBillData = null; // Stored locally to allow Bluetooth & Browser reprinting

// Default Calibration Settings
const DEFAULT_SETTINGS = {
    width: '58',
    fontSize: '10',
    lineHeight: '1.0',
    charLimit: '32',
    autoPrint: true
};

function getSettings() {
    const width = localStorage.getItem('pos_print_width') || DEFAULT_SETTINGS.width;
    const defaultCharLimit = width === '58' ? DEFAULT_SETTINGS.charLimit : '48';
    return {
        width: width,
        fontSize: localStorage.getItem('pos_print_fontSize') || DEFAULT_SETTINGS.fontSize,
        lineHeight: localStorage.getItem('pos_print_lineHeight') || DEFAULT_SETTINGS.lineHeight,
        charLimit: localStorage.getItem('pos_print_charLimit') || defaultCharLimit,
        autoPrint: localStorage.getItem('pos_print_autoPrint') !== 'false'
    };
}

function saveSettings(settings) {
    localStorage.setItem('pos_print_width', settings.width);
    localStorage.setItem('pos_print_fontSize', settings.fontSize);
    localStorage.setItem('pos_print_lineHeight', settings.lineHeight);
    localStorage.setItem('pos_print_charLimit', settings.charLimit);
    localStorage.setItem('pos_print_autoPrint', settings.autoPrint);
}

function applySettings() {
    const settings = getSettings();
    const is58 = settings.width === '58';

    // Width toggles
    document.querySelectorAll('.width-toggle-buttons .toggle-btn').forEach(btn => {
        if (btn.dataset.width === settings.width) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Font size slider (if rendered)
    const fontSlider = document.getElementById('font-size-slider');
    if (fontSlider) {
        const fontVal = document.getElementById('font-size-val');
        fontSlider.value = settings.fontSize;
        fontVal.textContent = settings.fontSize + 'px';
    }

    // Line spacing slider (if rendered)
    const heightSlider = document.getElementById('line-height-slider');
    if (heightSlider) {
        const heightVal = document.getElementById('line-height-val');
        heightSlider.value = settings.lineHeight;
        heightVal.textContent = settings.lineHeight;
    }

    // Character width slider limits & value adjustment (if rendered)
    const charSlider = document.getElementById('char-limit-slider');
    if (charSlider) {
        const charVal = document.getElementById('char-limit-val');
        if (settings.width === '58') {
            charSlider.min = '24';
            charSlider.max = '34';
        } else {
            charSlider.min = '40';
            charSlider.max = '48';
        }
        charSlider.value = settings.charLimit;
        charVal.textContent = settings.charLimit + ' chars';
    }

    // Auto print switch (if rendered)
    const autoSwitch = document.getElementById('auto-print-switch');
    if (autoSwitch) {
        autoSwitch.checked = settings.autoPrint;
    }

    // Standard receipt layouts parameters
    const previewWidth = is58 ? '240px' : '380px';
    const printWidth = is58 ? '44mm' : '72mm';
    const printPadding = is58 ? '1mm' : '3mm';

    // Apply CSS custom variables dynamically to receipt containers
    const applyVars = (container) => {
        if (!container) return;
        container.style.setProperty('--receipt-preview-width', previewWidth);
        container.style.setProperty('--receipt-preview-font-size', settings.fontSize + 'px');
        container.style.setProperty('--receipt-preview-line-height', settings.lineHeight);
        container.style.setProperty('--print-width', printWidth);
        container.style.setProperty('--print-font-size', settings.fontSize + 'px');
        container.style.setProperty('--print-line-height', settings.lineHeight);
        container.style.setProperty('--print-padding', printPadding);
    };

    applyVars(document.getElementById('receipt-container-preview'));
    applyVars(document.getElementById('receipt-container'));
}

// Modal Control Functions
function openPrinterModal() {
    document.getElementById('printer-settings-modal').classList.add('active');
    applySettings();
}

function closePrinterModal() {
    document.getElementById('printer-settings-modal').classList.remove('active');
}

function openReceiptModal() {
    document.getElementById('receipt-preview-modal').classList.add('active');
    applySettings();
}

function closeReceiptModal() {
    document.getElementById('receipt-preview-modal').classList.remove('active');
}

// GATT Server Web Bluetooth Engine
async function connectToDevice(device) {
    const statusText = document.getElementById('bt-status-text');
    const headerStatus = document.getElementById('header-printer-status');
    const updateUi = (color, text) => {
        if (statusText) statusText.innerHTML = `<span style="color: ${color}; font-weight: bold;">${text}</span>`;
        if (headerStatus) {
            headerStatus.textContent = text.replace(/🟡 |🟢 |🔴 /g, '');
            headerStatus.parentElement.style.backgroundColor = color === '#48BB78' ? '#C6F6D5' : '#EDF2F7';
            headerStatus.parentElement.style.color = color === '#48BB78' ? '#22543D' : '#2D3748';
        }
    };

    updateUi('#D69E2E', `🟡 Connecting...`);
    bluetoothDevice = device;
    bluetoothDevice.addEventListener('gattserverdisconnected', onDisconnected);

    const server = await bluetoothDevice.gatt.connect();
    updateUi('#D69E2E', `🟡 Discovering...`);

    let service = null;
    const serviceUUIDs = [
        '0000ffe0-0000-1000-8000-00805f9b34fb', // Standard HM-10 Serial
        '000018f0-0000-1000-8000-00805f9b34fb', // Thermal Printer Service
        '49535343-fe7d-4ae5-8fa9-9fafd205e455'  // Microchip BLE
    ];

    for (const uuid of serviceUUIDs) {
        try {
            service = await server.getPrimaryService(uuid);
            if (service) break;
        } catch (e) {
            console.log(`Service ${uuid} check skipped.`);
        }
    }

    if (!service) {
        try {
            const services = await server.getPrimaryServices();
            if (services.length > 0) service = services[0];
        } catch (e) {
            console.error(e);
        }
    }

    if (!service) throw new Error("No primary service discovered.");

    updateUi('#D69E2E', `🟡 Initializing...`);
    const characteristics = await service.getCharacteristics();
    for (const char of characteristics) {
        if (char.properties.write || char.properties.writeWithoutResponse) {
            writeCharacteristic = char;
            break;
        }
    }

    if (!writeCharacteristic) throw new Error("No write channel found.");

    updateUi('#48BB78', `🟢 Connected`);
    const testBtn = document.getElementById('bt-test-btn');
    if (testBtn) testBtn.style.display = 'block';
}

async function connectBluetooth() {
    const statusText = document.getElementById('bt-status-text');
    try {
        if (!navigator.bluetooth) {
            throw new Error("Web Bluetooth not supported by browser. Use Chrome/Edge.");
        }
        const device = await navigator.bluetooth.requestDevice({
            acceptAllDevices: true,
            optionalServices: [
                '0000ffe0-0000-1000-8000-00805f9b34fb',
                '000018f0-0000-1000-8000-00805f9b34fb',
                '49535343-fe7d-4ae5-8fa9-9fafd205e455'
            ]
        });
        await connectToDevice(device);
    } catch (err) {
        console.error(err);
        if (statusText) statusText.innerHTML = `<span style="color: #E53E3E; font-weight: bold;">🔴 Connect Failed</span>`;
        writeCharacteristic = null;
        bluetoothDevice = null;
    }
}

async function autoConnectBluetooth() {
    if (!navigator.bluetooth || !navigator.bluetooth.getDevices) return;
    try {
        const devices = await navigator.bluetooth.getDevices();
        if (devices.length > 0) {
            await connectToDevice(devices[0]);
        }
    } catch (err) {
        console.error("Auto-connect failed", err);
    }
}

function onDisconnected() {
    const statusText = document.getElementById('bt-status-text');
    const headerStatus = document.getElementById('header-printer-status');
    if (statusText) statusText.innerHTML = '<span style="color: #718096; font-weight: bold;">🔴 Disconnected</span>';
    if (headerStatus) {
        headerStatus.textContent = 'Disconnected';
        headerStatus.parentElement.style.backgroundColor = '#EDF2F7';
        headerStatus.parentElement.style.color = '#2D3748';
    }
    writeCharacteristic = null;
    bluetoothDevice = null;
    const testBtn = document.getElementById('bt-test-btn');
    if (testBtn) testBtn.style.display = 'none';

    // Auto reconnect loop (every 2 seconds) for seamless connection retention
    setTimeout(autoConnectBluetooth, 2000);
}

async function sendPrintData(bytes) {
    const statusText = document.getElementById('bt-status-text');
    if (!writeCharacteristic) {
        alert("Printer is not connected. Connect via Bluetooth first!");
        openPrinterModal();
        return;
    }

    const CHUNK_SIZE = 20; // BLE standard MTU chunk boundaries
    try {
        for (let i = 0; i < bytes.length; i += CHUNK_SIZE) {
            const chunk = bytes.slice(i, i + CHUNK_SIZE);
            await writeCharacteristic.writeValue(chunk);
            await new Promise(resolve => setTimeout(resolve, 35)); // congestion prevention delay
        }
    } catch (err) {
        console.error("Direct printing failed", err);
        if (statusText) statusText.innerHTML = `<span style="color: #E53E3E; font-weight: bold;">🔴 Print Failed</span>`;
    }
}

// Lightweight ESC/POS Command Packetizer (Cleaned Binary Compiler)
class EscPosEncoder {
    constructor(charLimit = 28) {
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
            this.addRaw([0x1D, 0x21, 0x11]);
        } else {
            this.addRaw([0x1D, 0x21, 0x00]);
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

        let left = itemName;
        if (left.length > itemColWidth) left = left.substring(0, itemColWidth - 1);
        const leftPadded = left.padEnd(itemColWidth, ' ');
        const centerPadded = qtyStr.padStart(qtyColWidth, ' ');
        const rightPadded = totalStr.padStart(totalColWidth, ' ');

        this.line(leftPadded + centerPadded + rightPadded);
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

// Compile Receipt directly from JSON structure (not Dom Parsing)
function compileReceiptBytes(billData) {
    const settings = getSettings();
    const charLimit = parseInt(settings.charLimit);
    const encoder = new EscPosEncoder(charLimit);

    encoder.init();

    // Store header names
    encoder.header("Ponnangai");
    encoder.header("Enterprises");

    // Subheaders
    encoder.align('center').line("Housekeeping Products");
    encoder.align('center').line("Thank you for shopping!");

    // Metas
    const billNo = `Bill #: ${billData.id}`;
    const timestampStr = billData.timestamp;
    encoder.align('left').row(billNo, timestampStr);

    const cashier = billData.cashier_name || 'Unknown';
    const payMode = billData.payment_mode || 'Cash';
    encoder.align('left').line(`Cashier: ${cashier} | Mode: ${payMode}`);

    encoder.divider();
    encoder.align('left').itemRow("Item", "Qty", "Total");
    encoder.divider();

    // Products list
    billData.items.forEach(item => {
        encoder.itemRow(item.name, item.quantity, item.total.toFixed(2));
    });

    encoder.divider();

    // Summary totals
    encoder.row("Subtotal:", billData.total_amount.toFixed(2));
    if (billData.discount > 0) {
        encoder.row("Discount:", `- ${billData.discount.toFixed(2)}`);
    }

    encoder.bold(true).row("FINAL TOTAL:", `Rs.${billData.final_amount.toFixed(2)}`).bold(false);

    // Footer greetings
    encoder.feed(1).align('center').line("Please visit again!");
    encoder.feed(5);
    encoder.addRaw([0x1D, 0x56, 0x42, 0x00]); // Tear serration feed cut

    return encoder.getBytes();
}

// Generate receipt preview mockup HTML on screen
function generateReceiptHtml(billData) {
    let itemsHtml = '';
    billData.items.forEach(item => {
        itemsHtml += `
            <div class="receipt-item">
                <div style="flex: 2; word-break: break-word;">${item.name}</div>
                <div style="flex: 1; text-align: center;">${item.quantity}</div>
                <div style="flex: 1; text-align: right;">${item.total.toFixed(2)}</div>
            </div>
        `;
    });

    const discountHtml = billData.discount > 0 ? `
        <div style="display: flex; justify-content: space-between; font-size: 9px; color: #4A5568;">
            <span>Discount:</span>
            <span>- ${billData.discount.toFixed(2)}</span>
        </div>
    ` : '';

    return `
        <div class="receipt-header">
            <h2 style="font-size: 15px; margin-bottom: 4px; font-weight: 700; line-height: 1.2;">Ponnangai<br>Enterprises</h2>
            <div style="font-size: 11px; margin-bottom: 2px;">Housekeeping Products</div>
            <div style="font-size: 9px; margin-bottom: 4px;">Thank you for shopping!</div>
            
            <div class="receipt-bill-meta" style="display: flex; justify-content: space-between; font-size: 9px; margin-top: 8px;">
                <span>Bill #: ${billData.id}</span>
                <span>${billData.timestamp}</span>
            </div>
            <div class="receipt-cashier-meta" style="text-align: left; font-size: 9px; margin-top: 2px;">
                Cashier: ${billData.cashier_name || 'Unknown'} | Mode: ${billData.payment_mode}
            </div>
        </div>

        <div style="margin-top: 8px; border-bottom: 1px dashed #000; padding-bottom: 4px; margin-bottom: 4px; font-weight: bold; font-size: 9px; display: flex;">
            <div style="flex: 2;">Item</div>
            <div style="flex: 1; text-align: center;">Qty</div>
            <div style="flex: 1; text-align: right;">Total</div>
        </div>

        ${itemsHtml}

        <div class="receipt-summary" style="margin-top: 8px;">
            <div style="display: flex; justify-content: space-between; font-size: 9px;">
                <span>Subtotal:</span>
                <span>${billData.total_amount.toFixed(2)}</span>
            </div>
            ${discountHtml}
            
            <div class="receipt-total">
                <span>FINAL TOTAL:</span>
                <span>₹${billData.final_amount.toFixed(2)}</span>
            </div>
        </div>
        
        <div class="receipt-footer" style="text-align: center; font-size: 9px; margin-top: 16px; font-style: italic;">
            Please visit again!
        </div>
    `;
}

// Dynamic Print flow triggers from checkout success or history logs
async function handlePrintFlow(billId) {
    try {
        const response = await fetch(`/api/bills/${billId}`);
        const data = await response.json();
        
        if (response.ok) {
            activeBillData = data.bill;
            
            // Generate HTML for receipt structures
            const receiptHtml = generateReceiptHtml(activeBillData);
            document.getElementById('receipt-container-preview').innerHTML = receiptHtml;
            
            const printBox = document.getElementById('receipt-container');
            if (printBox) {
                printBox.innerHTML = receiptHtml;
            }
            
            // Pop open the Receipt Preview modal
            openReceiptModal();
            
            // Check Bluetooth Autoprint triggers
            const settings = getSettings();
            if (settings.autoPrint) {
                if (writeCharacteristic) {
                    await printActiveBillBluetooth();
                } else {
                    // Fallback to standard browser print if Bluetooth is disconnected
                    setTimeout(() => {
                        window.print();
                    }, 500);
                }
            }
        } else {
            alert("Could not load receipt details.");
        }
    } catch (err) {
        console.error(err);
        alert("Server communication failure.");
    }
}

async function printActiveBillBluetooth() {
    if (!activeBillData) return;
    const bytes = compileReceiptBytes(activeBillData);
    await sendPrintData(bytes);
}

function printActiveBillBrowser() {
    window.print();
}

async function printTestReceipt() {
    const settings = getSettings();
    const charLimit = parseInt(settings.charLimit);
    const encoder = new EscPosEncoder(charLimit);
    
    encoder.init();
    encoder.align('center').bold(true).fontSize('double').line("Niyama POS").fontSize('normal').bold(false);
    encoder.divider();
    encoder.bold(true).line("Bluetooth Pairing Success!").bold(false);
    encoder.line("Your thermal printer is");
    encoder.line("fully connected & ready.");
    encoder.divider();
    encoder.feed(5);
    encoder.addRaw([0x1D, 0x56, 0x42, 0x00]);
    
    const bytes = encoder.getBytes();
    await sendPrintData(bytes);
}

// In-Page Configuration Init
document.addEventListener('DOMContentLoaded', () => {
    // Force user's ideal calibration settings on first load
    if (!localStorage.getItem('pos_print_calibrated_ideal_v4')) {
        localStorage.setItem('pos_print_width', '58');
        localStorage.setItem('pos_print_fontSize', '10');
        localStorage.setItem('pos_print_lineHeight', '1.0');
        localStorage.setItem('pos_print_charLimit', '32');
        localStorage.setItem('pos_print_calibrated_ideal_v4', 'true');
    }

    applySettings();
    
    // Background Auto Connect to paired printer on page load
    autoConnectBluetooth();
    
    // Setup controls events (if rendered for Admin/Manager roles)
    document.querySelectorAll('.width-toggle-buttons .toggle-btn').forEach(btn => {
        btn.onclick = function(e) {
            const width = e.target.dataset.width;
            const settings = getSettings();
            settings.width = width;
            settings.charLimit = width === '58' ? '32' : '48';
            saveSettings(settings);
            applySettings();
        };
    });
    
    const fontSlider = document.getElementById('font-size-slider');
    if (fontSlider) {
        fontSlider.oninput = function(e) {
            const settings = getSettings();
            settings.fontSize = e.target.value;
            saveSettings(settings);
            applySettings();
        };
    }
    
    const heightSlider = document.getElementById('line-height-slider');
    if (heightSlider) {
        heightSlider.oninput = function(e) {
            const settings = getSettings();
            settings.lineHeight = e.target.value;
            saveSettings(settings);
            applySettings();
        };
    }

    const charSlider = document.getElementById('char-limit-slider');
    if (charSlider) {
        charSlider.oninput = function(e) {
            const settings = getSettings();
            settings.charLimit = e.target.value;
            saveSettings(settings);
            applySettings();
        };
    }
    
    const autoSwitch = document.getElementById('auto-print-switch');
    if (autoSwitch) {
        autoSwitch.onchange = function(e) {
            const settings = getSettings();
            settings.autoPrint = e.target.checked;
            saveSettings(settings);
            applySettings();
        };
    }
});
