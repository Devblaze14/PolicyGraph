import { Link, useLocation } from "react-router-dom"
import { ShieldCheck, Search, Activity, Network, BarChart3, Menu, X } from "lucide-react"
import { useState } from "react"
import { cn } from "../../lib/utils"

const NAV_LINKS = [
    { name: "Home", href: "/", icon: ShieldCheck },
    { name: "AI Search", href: "/search", icon: Search },
    { name: "Eligibility", href: "/eligibility", icon: Activity },
    { name: "Knowledge Graph", href: "/graph", icon: Network },
    { name: "Dashboard", href: "/dashboard", icon: BarChart3 },
]

export function Navbar() {
    const { pathname } = useLocation()
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

    return (
        <header className="fixed top-0 left-0 right-0 h-16 bg-slate-900/80 backdrop-blur-xl border-b border-white/10 z-50 flex items-center justify-center">
            <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
                {/* Brand */}
                <Link to="/" className="flex items-center gap-2 group">
                    <div className="bg-gradient-to-tr from-indigo-500 to-cyan-400 p-1.5 rounded-lg shadow-lg shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition-shadow">
                        <ShieldCheck className="w-5 h-5 text-white" />
                    </div>
                    <span className="font-bold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-slate-100 to-slate-400">
                        Graph Policy
                    </span>
                </Link>

                {/* Desktop Nav */}
                <nav className="hidden md:flex items-center gap-1 bg-slate-800/50 rounded-full px-2 py-1.5 border border-white/5">
                    {NAV_LINKS.map((link) => {
                        const Icon = link.icon
                        const isActive = pathname === link.href || (pathname.startsWith(link.href) && link.href !== "/")
                        return (
                            <Link
                                key={link.name}
                                to={link.href}
                                className={cn(
                                    "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200",
                                    isActive
                                        ? "bg-slate-700/80 text-white shadow-sm"
                                        : "text-slate-400 hover:text-slate-100 hover:bg-slate-700/40"
                                )}
                            >
                                <Icon className="w-4 h-4" />
                                {link.name}
                            </Link>
                        )
                    })}
                </nav>

                {/* Right CTA */}
                <div className="hidden md:flex items-center gap-3">
                    <Link to="/search" className="btn-primary text-sm px-4 py-2">
                        Try AI Search
                    </Link>
                </div>

                {/* Mobile menu button */}
                <button
                    className="md:hidden p-2 text-slate-400 hover:text-white"
                    onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                >
                    {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                </button>
            </div>

            {/* Mobile Nav */}
            {mobileMenuOpen && (
                <div className="absolute top-16 left-0 right-0 bg-slate-900 border-b border-white/10 p-4 flex flex-col gap-2 md:hidden">
                    {NAV_LINKS.map((link) => {
                        const Icon = link.icon
                        const isActive = pathname === link.href
                        return (
                            <Link
                                key={link.name}
                                to={link.href}
                                onClick={() => setMobileMenuOpen(false)}
                                className={cn(
                                    "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                                    isActive
                                        ? "bg-indigo-500/20 text-indigo-400"
                                        : "text-slate-300 hover:bg-white/5"
                                )}
                            >
                                <Icon className="w-5 h-5" />
                                {link.name}
                            </Link>
                        )
                    })}
                </div>
            )}
        </header>
    )
}
