import Link from "next/link";

const INVENTORY = [
  { id: 1, name: "Clothwash Sticker Bottle", category: "Cleaning", stock: 20, price: 150, status: "In Stock" },
  { id: 2, name: "Floor Cleaner 5L", category: "Cleaning", stock: 15, price: 450, status: "Low Stock" },
  { id: 3, name: "Dishwash Gel 500ml", category: "Kitchen", stock: 42, price: 85, status: "In Stock" },
  { id: 4, name: "Glass Cleaner Spray", category: "Cleaning", stock: 8, price: 120, status: "Low Stock" },
  { id: 5, name: "Toilet Bowl Cleaner", category: "Bathroom", stock: 35, price: 95, status: "In Stock" },
  { id: 6, name: "Multi-Surface Wipes", category: "Cleaning", stock: 0, price: 210, status: "Out of Stock" },
];

export default function AdminDashboard() {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-surface-bg">
      {/* Sidebar (#0F172A background) */}
      <aside className="w-[260px] bg-[#0F172A] shrink-0 flex flex-col h-full text-white">
        <div className="p-6 h-[64px] flex items-center border-b border-white/10">
          <h1 className="text-xl font-bold">Admin Portal</h1>
        </div>
        <nav className="flex-1 py-6 flex flex-col gap-2 px-4">
          <Link href="/pos" className="text-white/70 font-medium px-4 py-2 hover:bg-white/5 rounded-[4px] transition-colors">
            Back to POS
          </Link>
          <Link href="/admin" className="text-brand bg-white/10 font-bold px-4 py-2 rounded-[4px]">
            Inventory
          </Link>
          <Link href="/admin/reports" className="text-white/70 font-medium px-4 py-2 hover:bg-white/5 rounded-[4px] transition-colors">
            Reports
          </Link>
          <Link href="/admin/settings" className="text-white/70 font-medium px-4 py-2 hover:bg-white/5 rounded-[4px] transition-colors">
            Settings
          </Link>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <header className="h-[64px] bg-surface-card border-b border-[#64748B] flex items-center px-8 shrink-0 justify-between">
          <h2 className="text-xl font-bold text-text-primary">Inventory Management</h2>
          <div className="flex items-center gap-4">
            <button className="bg-brand text-white font-medium px-4 py-2 rounded-[4px] text-sm">
              Add Product
            </button>
          </div>
        </header>

        <div className="p-8">
          {/* Top row of metric summary cards */}
          <div className="grid grid-cols-4 gap-6 mb-8">
            <div className="bg-surface-card p-6 border border-[#64748B]/20">
              <div className="text-sm font-medium text-text-secondary mb-1">Total Products</div>
              <div className="text-3xl font-bold text-text-primary">124</div>
            </div>
            <div className="bg-surface-card p-6 border border-[#64748B]/20">
              <div className="text-sm font-medium text-text-secondary mb-1">Low Stock Items</div>
              <div className="text-3xl font-bold text-[#EA580C]">12</div>
            </div>
            <div className="bg-surface-card p-6 border border-[#64748B]/20">
              <div className="text-sm font-medium text-text-secondary mb-1">Out of Stock</div>
              <div className="text-3xl font-bold text-red-600">3</div>
            </div>
            <div className="bg-surface-card p-6 border border-[#64748B]/20">
              <div className="text-sm font-medium text-text-secondary mb-1">Total Value</div>
              <div className="text-3xl font-bold text-text-primary">₹45,250</div>
            </div>
          </div>

          {/* Data Table */}
          <div className="bg-surface-card border border-[#64748B]/20">
            <div className="px-6 py-4 border-b border-[#64748B]/20 flex justify-between items-center">
              <h3 className="font-bold text-text-primary text-lg">All Items</h3>
              <input 
                type="text" 
                placeholder="Search inventory..." 
                className="px-4 py-2 text-sm font-medium rounded-[4px] border border-[#64748B] w-64 focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent"
              />
            </div>
            
            <div className="w-full overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-[#64748B] bg-surface-bg/50">
                    <th className="px-6 py-3 text-xs font-bold text-text-secondary uppercase tracking-wider">ID</th>
                    <th className="px-6 py-3 text-xs font-bold text-text-secondary uppercase tracking-wider">Product Name</th>
                    <th className="px-6 py-3 text-xs font-bold text-text-secondary uppercase tracking-wider">Category</th>
                    <th className="px-6 py-3 text-xs font-bold text-text-secondary uppercase tracking-wider">Stock</th>
                    <th className="px-6 py-3 text-xs font-bold text-text-secondary uppercase tracking-wider">Price</th>
                    <th className="px-6 py-3 text-xs font-bold text-text-secondary uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-surface-card">
                  {INVENTORY.map((item) => (
                    <tr key={item.id} className="border-b border-[#64748B]/20 hover:bg-surface-bg transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-text-secondary">#{item.id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-text-primary">{item.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-text-secondary">{item.category}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-text-primary">{item.stock}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-extrabold text-brand">₹{item.price.toFixed(2)}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-bold rounded-none ${
                          item.status === 'In Stock' ? 'bg-green-100 text-green-800' : 
                          item.status === 'Low Stock' ? 'bg-orange-100 text-orange-800' : 
                          'bg-red-100 text-red-800'
                        }`}>
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <div className="px-6 py-4 border-t border-[#64748B]/20 flex justify-between items-center text-sm text-text-secondary font-medium">
              <span>Showing 1 to 6 of 124 entries</span>
              <div className="flex gap-2">
                <button className="px-3 py-1 border border-[#64748B]/20 disabled:opacity-50 font-medium text-text-primary hover:bg-surface-bg">Previous</button>
                <button className="px-3 py-1 border border-[#64748B]/20 font-medium text-text-primary hover:bg-surface-bg">Next</button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
