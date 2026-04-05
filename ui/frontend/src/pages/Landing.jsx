import { motion } from "framer-motion"
import { Search, BrainCircuit, FileCheck, ArrowRight, ShieldCheck } from "lucide-react"
import { Link } from "react-router-dom"

const FEATURES = [
    {
        icon: BrainCircuit,
        title: "AI Knowledge Graph",
        description: "Policies are structured into smart nodes connected by logic, criteria, and benefits."
    },
    {
        icon: Search,
        title: "Semantic Search",
        description: "State-of-the-art vector embeddings match your natural language questions to exact documents."
    },
    {
        icon: FileCheck,
        title: "Eligibility Engine",
        description: "Deterministic rules run against profile data ensuring exact, verifiable eligibility checks."
    }
]

export default function Landing() {
    return (
        <div className="flex flex-col gap-24 py-12">

            {/* Hero Section */}
            <section className="relative flex flex-col items-center justify-center text-center px-4 pt-12">
                {/* Glow Effects */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-indigo-600/20 blur-[120px] rounded-full pointer-events-none" />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[300px] bg-cyan-500/10 blur-[100px] rounded-full pointer-events-none" />

                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="relative z-10 flex flex-col items-center"
                >
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 backdrop-blur-md mb-8 text-indigo-300 font-medium text-sm shadow-inner">
                        <ShieldCheck className="w-4 h-4" />
                        <span>Next Generation GovTech &nbsp;&bull;&nbsp; RAG + KG Architecture</span>
                    </div>

                    <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 max-w-4xl text-slate-100 drop-shadow-lg">
                        AI Powered <span className="text-gradient">Policy Assistant</span>
                    </h1>

                    <p className="text-lg md:text-xl text-slate-400 max-w-2xl mb-12 leading-relaxed">
                        Discover government schemes, check your eligibility instantly, and explore complex policy frameworks through interactive knowledge graphs.
                    </p>

                    <div className="flex flex-col sm:flex-row items-center gap-4">
                        <Link to="/search" className="btn-primary w-full sm:w-auto text-lg px-8 py-4 shadow-indigo-600/30">
                            <Search className="w-5 h-5" />
                            Try Policy Search
                        </Link>
                        <Link to="/eligibility" className="btn-secondary w-full sm:w-auto text-lg px-8 py-4 bg-slate-800/80 border-slate-700/50 hover:bg-slate-700">
                            Check Eligibility
                            <ArrowRight className="w-5 h-5 text-slate-400" />
                        </Link>
                    </div>
                </motion.div>
            </section>

            {/* Features Section */}
            <section className="px-4 max-w-6xl mx-auto w-full z-10">
                <div className="text-center mb-16">
                    <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-200 to-slate-500">How It Works</h2>
                    <p className="text-slate-400 mt-4">Three pillars of the Graph Policy system</p>
                </div>

                <div className="grid md:grid-cols-3 gap-8">
                    {FEATURES.map((feat, i) => {
                        const Icon = feat.icon
                        return (
                            <motion.div
                                key={feat.title}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: i * 0.15 }}
                                className="glass p-8 flex flex-col items-center text-center group hover:-translate-y-2 transition-transform duration-300"
                            >
                                <div className="w-16 h-16 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center mb-6 group-hover:bg-indigo-600/20 group-hover:border-indigo-500/30 group-hover:shadow-[0_0_30px_rgba(79,70,229,0.2)] transition-all">
                                    <Icon className="w-8 h-8 text-cyan-400 group-hover:text-indigo-400" />
                                </div>
                                <h3 className="text-xl font-bold text-slate-100 mb-3">{feat.title}</h3>
                                <p className="text-slate-400 leading-relaxed text-sm">{feat.description}</p>
                            </motion.div>
                        )
                    })}
                </div>
            </section>

            {/* Example Queries */}
            <section className="glass-panel max-w-4xl mx-auto w-full p-8 md:p-12 text-center relative overflow-hidden z-10">
                <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 blur-[80px] rounded-full pointer-events-none" />
                <h2 className="text-2xl font-bold mb-8">What people are asking</h2>
                <div className="flex flex-wrap justify-center gap-4">
                    {["Schemes for farmers in India", "Scholarships for low income students", "Government housing schemes", "Startup India Seed Fund eligibility"].map(q => (
                        <Link key={q} to={`/search?q=${encodeURIComponent(q)}`} className="px-5 py-3 rounded-full bg-slate-800/80 border border-slate-700 hover:border-indigo-500/50 hover:bg-slate-700 transition-colors text-sm text-slate-300 flex items-center gap-2">
                            <Search className="w-4 h-4 text-indigo-400" />
                            {q}
                        </Link>
                    ))}
                </div>
            </section>

        </div>
    )
}
