import { useState, useEffect } from "react"
import { useSearchParams } from "react-router-dom"
import { motion } from "framer-motion"
import { Search as SearchIcon, Sparkles, Network, FileText, ChevronDown } from "lucide-react"

export default function Search() {
    const [searchParams, setSearchParams] = useSearchParams()
    const initialQuery = searchParams.get("q") || ""

    const [query, setQuery] = useState(initialQuery)
    const [isSearching, setIsSearching] = useState(false)
    const [results, setResults] = useState(null)

    useEffect(() => {
        if (initialQuery) {
            handleSearch(initialQuery)
        }
    }, [initialQuery])

    const handleSearch = async (q = query) => {
        if (!q.trim()) return
        setIsSearching(true)
        setSearchParams({ q })
        setResults(null)

        try {
            const res = await fetch("http://localhost:8000/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question: q,
                    top_k: 10,
                    profile: {}
                })
            })
            if (!res.ok) throw new Error("API requested failed.")
            const data = await res.json()
            setResults(data)
        } catch (error) {
            console.error(error)
            setResults({ answer: "Error connecting to Graph Policy Backend.", schemes: [], sources: [], confidence_score: 0 })
        } finally {
            setIsSearching(false)
        }
    }

    return (
        <div className="flex flex-col h-full max-w-4xl mx-auto w-full pt-8 md:pt-16 px-4">

            {/* Search Header / Input Centered initially */}
            <motion.div
                layout
                className={`flex flex-col ${results ? "mb-12" : "mt-24 items-center text-center"}`}
            >
                {!results && (
                    <motion.div layoutId="title" className="mb-8">
                        <h1 className="text-4xl font-bold mb-4 flex items-center justify-center gap-3">
                            <Sparkles className="text-cyan-400 w-8 h-8" />
                            Ask Graph Policy
                        </h1>
                        <p className="text-slate-400">Search rules, eligibility criteria, and benefits across all indexed schemes.</p>
                    </motion.div>
                )}

                <motion.div layoutId="searchBox" className="w-full relative group">
                    <div className="absolute inset-0 bg-indigo-500/10 blur-xl rounded-full opacity-0 group-focus-within:opacity-100 transition-opacity" />
                    <div className="relative flex items-center bg-slate-800/80 border border-slate-700 focus-within:border-indigo-500/50 rounded-2xl shadow-xl overflow-hidden p-2 transition-colors">
                        <SearchIcon className="w-6 h-6 text-slate-400 ml-4 flex-shrink-0" />
                        <input
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                            placeholder="e.g. Schemes for farmers in India"
                            className="w-full bg-transparent border-none text-lg px-4 py-3 focus:outline-none text-slate-100 placeholder:text-slate-500"
                        />
                        <button
                            onClick={() => handleSearch()}
                            className="bg-indigo-600 hover:bg-indigo-500 text-white p-3 rounded-xl transition-colors shadow-lg shadow-indigo-600/20 active:scale-95 flex-shrink-0"
                            disabled={isSearching}
                        >
                            {isSearching ? <Sparkles className="w-5 h-5 animate-spin" /> : <SearchIcon className="w-5 h-5" />}
                        </button>
                    </div>
                </motion.div>
            </motion.div>

            {/* Results Section */}
            {isSearching && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col gap-4 mt-8">
                    <div className="flex items-center gap-3 text-slate-400 font-medium">
                        <Network className="w-5 h-5 animate-pulse text-indigo-400" />
                        Traversing knowledge graph...
                    </div>
                    <div className="h-32 bg-slate-800/50 rounded-xl animate-pulse" />
                    <div className="h-32 bg-slate-800/30 rounded-xl animate-pulse delay-75" />
                </motion.div>
            )}

            {results && !isSearching && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col gap-6"
                >
                    <div className="flex items-center gap-2 text-slate-400 pb-2 border-b border-white/5">
                        <Sparkles className="w-5 h-5 text-cyan-400" />
                        <h2 className="text-lg font-medium">Synthesized Answer</h2>
                    </div>

                    <div className="glass p-6 md:p-8 flex flex-col gap-4 group">
                        <p className="text-slate-100 leading-relaxed text-[16px]">
                            {results.answer}
                        </p>

                        {results.schemes?.length > 0 && (
                            <div className="mt-4">
                                <h3 className="text-sm font-semibold text-slate-400 mb-2 uppercase tracking-wider">Related Services / Schemes</h3>
                                <div className="flex flex-wrap gap-2">
                                    {results.schemes.map((s, idx) => (
                                        <span key={idx} className="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-sm font-medium">
                                            {s}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {results.steps?.length > 0 && (
                            <div className="mt-4">
                                <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">Procedure / Steps</h3>
                                <div className="space-y-3 pl-2 border-l-2 border-slate-700">
                                    {results.steps.map((st, idx) => (
                                        <div key={idx} className="flex gap-4">
                                            <span className="text-cyan-400 font-bold shrink-0">{idx + 1}.</span>
                                            <span className="text-slate-200">{st}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="flex flex-col md:flex-row gap-6 mt-4">
                            {results.documents_required?.length > 0 && (
                                <div className="flex-1 bg-slate-800/40 p-5 rounded-2xl border border-white/5">
                                    <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider flex items-center gap-2">
                                        <FileText className="w-4 h-4 text-emerald-400" /> Documents Required
                                    </h3>
                                    <ul className="list-disc list-inside text-sm text-slate-300 space-y-1.5 marker:text-emerald-500/50">
                                        {results.documents_required.map((d, i) => <li key={i}>{d}</li>)}
                                    </ul>
                                </div>
                            )}

                            {results.fees?.length > 0 && (
                                <div className="flex-1 bg-slate-800/40 p-5 rounded-2xl border border-white/5">
                                    <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider flex items-center gap-2">
                                        <Sparkles className="w-4 h-4 text-amber-400" /> Fees
                                    </h3>
                                    <ul className="list-disc list-inside text-sm text-slate-300 space-y-1.5 marker:text-amber-500/50">
                                        {results.fees.map((f, i) => <li key={i}>{f}</li>)}
                                    </ul>
                                </div>
                            )}
                        </div>

                        {results.authority && results.authority !== "Unknown" && (
                            <div className="mt-2 text-sm text-slate-400 border border-t-white/10 pt-4 mt-6">
                                <strong>Providing Authority:</strong> <span className="text-slate-200">{results.authority}</span>
                            </div>
                        )}

                        {results.sources?.length > 0 && (
                            <div className="mt-4">
                                <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">
                                    Source Evidence ({Math.round(results.confidence_score * 100)}% Match)
                                </h3>
                                <div className="space-y-3">
                                    {results.sources.map((src, i) => {
                                        const docName = src.metadata?.source?.split('\\').pop()?.split('/').pop() || src.metadata?.filename || "Document"
                                        return (
                                            <div key={i} className="p-4 rounded-xl bg-slate-800/50 border border-white/5 hover:border-indigo-500/30 transition-colors">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <FileText className="w-4 h-4 text-cyan-400" />
                                                    <span className="text-sm font-bold text-cyan-100">{docName}</span>
                                                    <span className="text-xs text-slate-500 bg-slate-900 px-2 py-0.5 rounded ml-auto">Score: {(src.score).toFixed(2)}</span>
                                                </div>
                                                <div className="text-sm text-slate-400 italic">"{src.text}"</div>
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>
                        )}
                    </div>
                </motion.div>
            )}
        </div>
    )
}
