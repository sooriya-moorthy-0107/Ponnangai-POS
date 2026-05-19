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
            // Redirect to receipt page for printing
            window.location.href = `/receipt/${data.bill_id}`;
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
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn-secondary btn-small" style="flex: 1;" onclick="revertBillFromHistory(${bill.id})">
                            ↩️ Revert & Edit
                        </button>
                        <button class="btn btn-destructive btn-small" style="flex: 1;" onclick="cancelBillFromHistory(${bill.id})">
                            ❌ Cancel
                        </button>
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
