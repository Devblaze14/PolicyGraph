import { Outlet } from "react-router-dom"
import { Navbar } from "./Navbar"

export function Layout() {
    return (
        <div className="relative min-h-screen flex flex-col pt-16">
            <Navbar />
            <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
                <Outlet />
            </main>

            <footer className="w-full border-t border-slate-800 bg-slate-900/50 mt-auto py-8 text-center text-sm text-slate-500">
                <div className="max-w-7xl mx-auto px-4">
                    <p>PolicyGraph — AI Powered Policy Assistant &nbsp;&bull;&nbsp; Next-Gen GovTech Platform</p>
                </div>
            </footer>
        </div>
    )
}
