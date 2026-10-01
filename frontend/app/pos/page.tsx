import Link from "next/link";
import Image from "next/image";

// Dummy data
const PRODUCTS = [
  { id: 1, name: "Clothwash Sticker Bottle", price: 150, stock: 20 },
  { id: 2, name: "Floor Cleaner 5L", price: 450, stock: 15 },
  { id: 3, name: "Dishwash Gel 500ml", price: 85, stock: 42 },
  { id: 4, name: "Glass Cleaner Spray", price: 120, stock: 8 },
  { id: 5, name: "Toilet Bowl Cleaner", price: 95, stock: 35 },
  { id: 6, name: "Multi-Surface Wipes", price: 210, stock: 12 },
  { id: 7, name: "Hand Wash Liquid 1L", price: 180, stock: 25 },
  { id: 8, name: "Room Freshener", price: 140, stock: 18 },
];

const CART_ITEMS = [
  { id: 1, name: "Clothwash Sticker Bottle", price: 150, quantity: 2 },
  { id: 2, name: "Dishwash Gel 500ml", price: 85, quantity: 1 },
];

export default function POSScreen() {
  const subtotal = CART_ITEMS.reduce((acc, item) => acc + item.price * item.quantity, 0);
  const tax = subtotal * 0.18;
  const total = subtotal + tax;

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-surface-bg">
      {/* Top Nav */}
      <header className="h-[64px] bg-surface-card border-b border-[#64748B] flex items-center px-6 shrink-0 justify-between">
        <div className="flex items-center gap-8">
          <h1 className="text-xl font-bold text-text-primary">Ponnangai POS</h1>
          <nav className="flex items-center gap-6">
            <Link href="/pos" className="text-brand font-bold text-sm">Point of Sale</Link>
            <Link href="/admin" className="text-text-secondary font-medium text-sm hover:text-text-primary transition-colors">Inventory</Link>
            <Link href="/admin" className="text-text-secondary font-medium text-sm hover:text-text-primary transition-colors">Reports</Link>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm font-medium text-text-secondary">Logged in as <span className="text-text-primary font-bold">Admin</span></div>
          <Link href="/login" className="text-sm font-medium text-text-secondary hover:text-text-primary">Logout</Link>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel: Active Cart (35%) */}
        <div className="w-[35%] bg-surface-card flex flex-col h-full border-r border-[#64748B]/20">
          <div className="p-6 border-b border-[#64748B]/20">
            <h2 className="text-lg font-bold text-text-primary">Current Order</h2>
            <p className="text-sm text-text-secondary font-medium mt-1">Order #0042 • Walk-in Customer</p>
          </div>
          
          {/* Cart Items */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {CART_ITEMS.map((item) => (
              <div key={item.id} className="flex flex-row items-center justify-between p-3 border-b border-[#64748B]/10 last:border-0">
                <div className="flex flex-col flex-1 pr-4">
                  <span className="text-sm font-bold text-text-primary truncate">{item.name}</span>
                  <span className="text-[13px] font-extrabold text-brand mt-1">₹{item.price.toFixed(2)}</span>
                </div>
                <div className="flex items-center gap-3">
                  <button className="w-8 h-8 rounded border border-[#64748B]/30 flex items-center justify-center text-text-primary font-bold hover:bg-surface-bg shrink-0">-</button>
                  <span className="text-sm font-bold text-text-primary w-4 text-center">{item.quantity}</span>
                  <button className="w-8 h-8 rounded border border-[#64748B]/30 flex items-center justify-center text-text-primary font-bold hover:bg-surface-bg shrink-0">+</button>
                </div>
              </div>
            ))}
          </div>

          {/* Total Calculation Block */}
          <div className="p-6 border-t border-[#64748B]/20 bg-surface-card shrink-0 space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-text-secondary font-medium">
                <span>Subtotal</span>
                <span>₹{subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm text-text-secondary font-medium">
                <span>Tax (18%)</span>
                <span>₹{tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-lg font-bold text-text-primary pt-2 border-t border-[#64748B]/20 mt-2">
                <span>Total</span>
                <span>₹{total.toFixed(2)}</span>
              </div>
            </div>
            
            <button className="w-full bg-checkout text-white font-bold py-4 rounded-[8px] text-base hover:opacity-90 transition-opacity mt-4">
              Confirm & Print Bill
            </button>
          </div>
        </div>

        {/* Right Panel: Product Grid (65%) */}
        <div className="w-[65%] h-full p-6 overflow-y-auto bg-surface-bg">
          <div className="mb-6 flex justify-between items-center">
            <h2 className="text-xl font-bold text-text-primary">Products</h2>
            <input 
              type="text" 
              placeholder="Search products..." 
              className="px-4 py-2 text-sm font-medium rounded-[8px] border border-[#64748B] w-64 focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent"
            />
          </div>
          
          <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {PRODUCTS.map((product) => (
              <div key={product.id} className="bg-surface-card p-4 rounded-none flex flex-col h-full">
                {/* Product Image Placeholder */}
                <div className="w-full aspect-square bg-surface-bg mb-4 flex items-center justify-center">
                  <span className="text-text-secondary font-medium text-xs">Image</span>
                </div>
                
                {/* Product Details (Left Aligned) */}
                <div className="flex flex-col items-start mb-4 flex-1 text-left">
                  <h3 className="text-[14px] font-bold text-text-primary mb-1 text-left line-clamp-2 w-full">{product.name}</h3>
                  <div className="text-[16px] font-extrabold text-brand mb-1 text-left w-full">₹{product.price.toFixed(2)}</div>
                  <div className="text-[12px] font-medium text-text-secondary text-left w-full">Stock: {product.stock}</div>
                </div>
                
                {/* Add to Cart Button */}
                <button className="w-full bg-action-secondary text-brand font-medium py-2 text-[14px] hover:bg-[#DDEBFF] transition-colors">
                  Add to Cart
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
