import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { Users, FileStack, Zap, ShieldCheck, Database, TrendingUp, Search } from "lucide-react"

const DATA_AREA = [
    { name: 'Mon', queries: 400 },
    { name: 'Tue', queries: 300 },
    { name: 'Wed', queries: 550 },
    { name: 'Thu', queries: 200 },
    { name: 'Fri', queries: 800 },
    { name: 'Sat', queries: 950 },
    { name: 'Sun', queries: 1100 },
]

const DATA_BAR = [
    { name: 'PM-KISAN', views: 85 },
    { name: 'Ayushman Bharat', views: 72 },
    { name: 'PMAY', views: 65 },
    { name: 'Startup Seed', views: 54 },
    { name: 'KCC', views: 40 },
]

export default function Dashboard() {
    const [metrics, setMetrics] = useState({
        policies_indexed: 0,
        documents_processed: 0,
        queries_answered: 0,
        graph_nodes: 0,
        graph_edges: 0
    })

    useEffect(() => {
        fetch("http://localhost:8000/metrics")
            .then(res => res.json())
            .then(data => {
                if (!data.error) {
                    setMetrics(data)
                }
            })
            .catch(err => console.error("Failed to fetch metrics:", err))
    }, [])

    const STATS = [
        { icon: ShieldCheck, label: "Policies Indexed", value: metrics.policies_indexed.toLocaleString(), trend: "+12.5%", color: "text-indigo-400", bg: "bg-indigo-500/10" },
        { icon: FileStack, label: "Documents Processed", value: metrics.documents_processed.toLocaleString(), trend: "+5.1%", color: "text-cyan-400", bg: "bg-cyan-500/10" },
        { icon: Zap, label: "Queries Answered", value: metrics.queries_answered.toLocaleString(), trend: "+24.3%", color: "text-emerald-400", bg: "bg-emerald-500/10" },
        { icon: Database, label: "Graph Nodes", value: (metrics.graph_nodes / 1000).toFixed(1) + "k", trend: "+8.4%", color: "text-amber-400", bg: "bg-amber-500/10" },
    ]
    return (
        <div className="flex flex-col gap-8 max-w-7xl mx-auto w-full pt-8 px-4">

            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
                        <TrendingUp className="w-8 h-8 text-indigo-400" />
                        System Metrics
                    </h1>
                    <p className="text-slate-400 mt-2">Real-time performance and usage statistics for Graph Policy engine.</p>
                </div>

                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700 transition-colors shadow-sm">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> Live Status
                    </button>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {STATS.map((stat, i) => {
                    const Icon = stat.icon
                    return (
                        <motion.div
                            key={stat.label}
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: i * 0.1 }}
                            className="glass p-6 group cursor-default hover:shadow-indigo-500/10 hover:border-indigo-500/30 transition-all duration-300"
                        >
                            <div className="flex items-center justify-between mb-4">
                                <div className={`p-3 rounded-xl ${stat.bg} ${stat.color} border border-white/5 group-hover:scale-110 transition-transform`}>
                                    <Icon className="w-5 h-5" />
                                </div>
                                <div className="flex items-center gap-1 text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-full border border-emerald-500/20">
                                    <TrendingUp className="w-3 h-3" /> {stat.trend}
                                </div>
                            </div>
                            <div className="text-3xl font-bold tracking-tight text-white mb-1">{stat.value}</div>
                            <div className="text-sm font-medium text-slate-400">{stat.label}</div>
                        </motion.div>
                    )
                })}
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-24">

                {/* Area Chart: Traffic */}
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="glass-panel p-6 flex flex-col h-96"
                >
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                            <Zap className="w-5 h-5 text-indigo-400" />
                            Queries Traffic
                        </h3>
                        <select className="bg-slate-900 border border-slate-700 text-sm rounded-lg px-3 py-1 text-slate-300 outline-none">
                            <option>Last 7 Days</option>
                            <option>Last 30 Days</option>
                        </select>
                    </div>

                    <div className="flex-1 w-full min-h-[250px] -ml-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={DATA_AREA} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorQuery" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.8} />
                                        <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="name" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${val}`} />
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc' }}
                                    itemStyle={{ color: '#818cf8', fontWeight: 'bold' }}
                                />
                                <Area type="monotone" dataKey="queries" stroke="#818cf8" strokeWidth={3} fillOpacity={1} fill="url(#colorQuery)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* Bar Chart: Top Indexed */}
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    className="glass-panel p-6 flex flex-col h-96"
                >
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                            <Search className="w-5 h-5 text-cyan-400" />
                            Top Searched Policies
                        </h3>
                    </div>

                    <div className="flex-1 w-full min-h-[250px] -ml-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={DATA_BAR} margin={{ top: 10, right: 10, left: 0, bottom: 0 }} layout="vertical">
                                <defs>
                                    <linearGradient id="colorViews" x1="0" y1="0" x2="1" y2="0">
                                        <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.6} />
                                        <stop offset="100%" stopColor="#06b6d4" stopOpacity={1} />
                                    </linearGradient>
                                </defs>
                                <XAxis type="number" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} hide />
                                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} width={100} />
                                <Tooltip
                                    cursor={{ fill: '#1e293b' }}
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc' }}
                                    itemStyle={{ color: '#22d3ee', fontWeight: 'bold' }}
                                />
                                <Bar dataKey="views" fill="url(#colorViews)" radius={[0, 4, 4, 0]} barSize={24} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

            </div>
        </div>
    )
}
