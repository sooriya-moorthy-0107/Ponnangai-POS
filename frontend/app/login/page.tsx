export default function LoginPage() {
  return (
    <div className="flex min-h-screen w-full">
      {/* Left side branding */}
      <div className="hidden lg:flex w-1/2 bg-brand flex-col justify-center items-center p-12 text-white">
        <h1 className="text-5xl font-bold mb-4">Ponnangai POS</h1>
        <p className="text-xl font-medium opacity-90 text-center max-w-md">
          Enterprise Point-of-Sale & Inventory Management System
        </p>
      </div>
      
      {/* Right side login module */}
      <div className="w-full lg:w-1/2 flex items-center justify-center bg-surface-bg p-8">
        <div 
          className="w-full max-w-md bg-surface-card rounded-[16px] p-10"
          style={{ boxShadow: "0px 4px 24px rgba(0, 0, 0, 0.08)" }}
        >
          <div className="mb-10 text-center">
            <h2 className="text-[28px] font-bold text-text-primary mb-2">Welcome Back</h2>
            <p className="text-text-secondary font-medium">Please enter your details to sign in.</p>
          </div>
          
          <form className="space-y-6">
            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-bold text-text-primary text-left">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                placeholder="admin@ponnangai.com"
                className="w-full rounded-[8px] border border-[#64748B] bg-white px-4 py-3 text-text-primary font-medium focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent transition-shadow"
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-bold text-text-primary text-left">
                Password
              </label>
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                className="w-full rounded-[8px] border border-[#64748B] bg-white px-4 py-3 text-text-primary font-medium focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent transition-shadow"
              />
            </div>
            
            <div className="pt-2">
              <a href="/pos" className="block w-full">
                <button
                  type="button"
                  className="w-full bg-checkout text-white font-bold py-4 rounded-[8px] hover:opacity-90 transition-opacity text-base"
                >
                  Login
                </button>
              </a>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
