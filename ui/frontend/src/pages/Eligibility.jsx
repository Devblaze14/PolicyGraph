import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { CheckCircle2, XCircle, AlertCircle, FileText, ChevronRight, Calculator, IndianRupee } from "lucide-react"
import { cn } from "../lib/utils"

const CATEGORIES = ["General", "OBC", "SC", "ST", "Minority", "EWS"]

export default function Eligibility() {
    const [formData, setFormData] = useState({
        age: "",
        income: "",
        occupation: "",
        location: "",
        category: "General"
    })

    const [loading, setLoading] = useState(false)
    const [results, setResults] = useState(null)

    const handleCheck = (e) => {
        e.preventDefault()
        setLoading(true)

        // Simulate check
        setTimeout(() => {
            setLoading(false)
            setResults([
                {
                    id: "PM_KISAN",
                    title: "PM-KISAN",
                    status: "ELIGIBLE",
                    score: 100,
                    reason: ["Age > 18 (Valid)", "Income < 200,000 (Valid)", "Occupation = Farmer (Valid)"],
                    benefits: "₹6,000 per year paid in three equal installments."
                },
                {
                    id: "PMAY",
                    title: "PM Awas Yojana",
                    status: "NOT_ELIGIBLE",
                    score: 45,
                    reason: ["Income limit > 300,000 (Failed)"],
                    benefits: "Interest subsidy on housing loans."
                },
                {
                    id: "AYUSHMAN",
                    title: "Ayushman Bharat",
                    status: "NEEDS_INFO",
                    score: 80,
                    reason: ["SECC Database verification required."],
                    benefits: "Health cover of ₹5 lakhs per family per year."
                }
            ])
        }, 1500)
    }

    const handleChange = (e) => {
        setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))
    }

    return (
        <div className="max-w-6xl mx-auto w-full pt-8 flex flex-col lg:flex-row gap-8 lg:gap-12">

            {/* Form Section */}
            <motion.div
                layout
                className="flex-1 shrink-0 lg:max-w-md w-full"
            >
                <div className="glass p-8">
                    <div className="mb-8">
                        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
                            <Calculator className="text-indigo-400 w-6 h-6" />
                            Check Eligibility
                        </h2>
                        <p className="text-slate-400 text-sm">Enter your profile to see matched schemes.</p>
                    </div>

                    <form onSubmit={handleCheck} className="flex flex-col gap-5">
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">Age</label>
                            <input
                                type="number" name="age" value={formData.age} onChange={handleChange} required
                                className="styled-input" placeholder="e.g. 25"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2 flex items-center gap-1">
                                Annual Income <IndianRupee className="w-3 h-3 text-slate-500" />
                            </label>
                            <input
                                type="number" name="income" value={formData.income} onChange={handleChange} required
                                className="styled-input" placeholder="e.g. 250000"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">Occupation</label>
                            <input
                                type="text" name="occupation" value={formData.occupation} onChange={handleChange} required
                                className="styled-input" placeholder="e.g. Farmer, Student, Teacher"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">State / Location</label>
                            <input
                                type="text" name="location" value={formData.location} onChange={handleChange} required
                                className="styled-input" placeholder="e.g. Rajasthan"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">Category</label>
                            <select
                                name="category" value={formData.category} onChange={handleChange} required
                                className="styled-input appearance-none bg-[url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2220%22%20height%3D%2220%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M5%208l5%205%205-5%22%20stroke%3D%22%2394a3b8%22%20stroke-width%3D%222%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[position:right_1rem_center]"
                            >
                                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                            </select>
                        </div>

                        <button type="submit" disabled={loading} className="btn-primary mt-4 w-full text-lg shadow-indigo-600/30">
                            {loading ? <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : "Run Engine"}
                        </button>
                    </form>
                </div>
            </motion.div>

            {/* Results Section */}
            <div className="flex-[1.5] flex flex-col">
                {!results && !loading && (
                    <div className="h-full min-h-[400px] border border-dashed border-slate-700/50 rounded-2xl flex flex-col items-center justify-center text-slate-500 p-8">
                        <Calculator className="w-16 h-16 text-slate-700 mb-4" />
                        <h3 className="text-xl font-medium text-slate-300 mb-2">Results will appear here</h3>
                        <p className="text-center max-w-sm">Fill in your profile and run the eligibility engine to match with the knowledge graph.</p>
                    </div>
                )}

                {loading && (
                    <div className="h-full flex flex-col items-center justify-center pt-24 text-slate-400 gap-4">
                        <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
                        <p className="animate-pulse">Traversing rules & criteria graph...</p>
                    </div>
                )}

                {results && !loading && (
                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col gap-6 w-full pb-12">

                        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                            <h2 className="text-2xl font-bold">Eligibility Results</h2>
                            <span className="px-4 py-1.5 rounded-full bg-indigo-500/10 text-indigo-400 font-medium border border-indigo-500/20 text-sm">
                                {results.length} Schemes Analyzed
                            </span>
                        </div>

                        <div className="flex flex-col gap-6">
                            <AnimatePresence>
                                {results.map((res, i) => {

                                    const isEl = res.status === "ELIGIBLE"
                                    const isNot = res.status === "NOT_ELIGIBLE"
                                    const isInfo = res.status === "NEEDS_INFO"

                                    return (
                                        <motion.div
                                            key={res.id}
                                            initial={{ opacity: 0, y: 30 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.15 }}
                                            className="glass-panel overflow-hidden flex flex-col group relative"
                                        >
                                            {/* Left color bar */}
                                            <div className={cn("absolute left-0 top-0 bottom-0 w-1",
                                                isEl ? "bg-emerald-500 shadow-[0_0_15px_#10b981]" :
                                                    isNot ? "bg-rose-500" : "bg-amber-500"
                                            )} />

                                            <div className="p-6 md:p-8 ml-1">
                                                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                                                    <h3 className="text-xl font-bold text-slate-100 flex items-center gap-3">
                                                        {isEl && <CheckCircle2 className="text-emerald-500 w-6 h-6" />}
                                                        {isNot && <XCircle className="text-rose-500 w-6 h-6" />}
                                                        {isInfo && <AlertCircle className="text-amber-500 w-6 h-6" />}
                                                        {res.title}
                                                    </h3>

                                                    <div className={cn("px-4 py-1.5 rounded-full text-xs font-bold tracking-wider",
                                                        isEl ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                                                            isNot ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" :
                                                                "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                                    )}>
                                                        {res.status.replace("_", " ")}
                                                    </div>
                                                </div>

                                                <div className="flex flex-col gap-4">

                                                    {/* Reason List */}
                                                    <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-700/50">
                                                        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                                                            <FileText className="w-4 h-4" /> Rule Trace
                                                        </h4>
                                                        <ul className="flex flex-col gap-2">
                                                            {res.reason.map((r, ri) => {
                                                                const passed = r.includes('(Valid)')
                                                                const failed = r.includes('(Failed)')
                                                                return (
                                                                    <li key={ri} className="flex items-center gap-2 text-sm text-slate-300 font-mono">
                                                                        <span className={cn("w-1.5 h-1.5 rounded-full inline-block", passed ? "bg-emerald-500" : failed ? "bg-rose-500" : "bg-amber-500")} />
                                                                        {r}
                                                                    </li>
                                                                )
                                                            })}
                                                        </ul>
                                                    </div>

                                                    {/* Benefits */}
                                                    <div className="px-4 py-3 bg-indigo-500/5 border border-indigo-500/10 rounded-xl text-sm text-indigo-300 flex items-start gap-3">
                                                        <ChevronRight className="w-5 h-5 mt-0.5 text-indigo-500 shrink-0" />
                                                        <div>
                                                            <strong className="block text-slate-200 mb-1">Benefits provided:</strong>
                                                            {res.benefits}
                                                        </div>
                                                    </div>

                                                </div>
                                            </div>
                                        </motion.div>
                                    )
                                })}
                            </AnimatePresence>
                        </div>
                    </motion.div>
                )}
            </div>
        </div>
    )
}
