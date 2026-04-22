import { useState, useCallback, useRef, useEffect } from "react"
import { motion } from "framer-motion"
import ForceGraph2D from "react-force-graph-2d"
import { Network, ZoomIn, ZoomOut, Maximize } from "lucide-react"

export default function GraphPage() {
    const fgRef = useRef()
    const [dimensions, setDimensions] = useState({ width: 800, height: 600 })
    const containerRef = useRef()

    const [gData, setGData] = useState({ nodes: [], links: [] })

    useEffect(() => {
        fetch("http://localhost:8000/graph")
            .then(res => res.json())
            .then(data => {
                setGData({ nodes: data.nodes, links: data.edges })
            })
            .catch(err => console.error(err))
    }, [])

    useEffect(() => {
        let timeoutId;
        const updateSize = () => {
            if (containerRef.current) {
                setDimensions({
                    width: containerRef.current.clientWidth,
                    height: containerRef.current.clientHeight
                })
            }
        }

        // Initial size
        updateSize()

        // Handle resize with debounce
        const handleResize = () => {
            clearTimeout(timeoutId)
            timeoutId = setTimeout(updateSize, 100)
        }

        window.addEventListener("resize", handleResize)
        return () => {
            window.removeEventListener("resize", handleResize)
            clearTimeout(timeoutId)
        }
    }, [])

    const handleZoomIn = () => fgRef.current?.zoom(fgRef.current.zoom() * 1.5, 400)
    const handleZoomOut = () => fgRef.current?.zoom(fgRef.current.zoom() / 1.5, 400)
    const handleFit = () => fgRef.current?.zoomToFit(400, 50)

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)] min-h-[600px] w-full pt-4">

            <div className="flex items-center justify-between mb-6 px-2">
                <div>
                    <h2 className="text-2xl font-bold flex items-center gap-2">
                        <Network className="w-6 h-6 text-indigo-400" />
                        Knowledge Graph Explorer
                    </h2>
                    <p className="text-slate-400 text-sm mt-1">Interactive visualization of policy structures, criteria, and benefits.</p>
                </div>

                <div className="flex gap-2">
                    <button onClick={handleZoomOut} className="p-2 bg-slate-800 rounded-lg hover:bg-slate-700 transition-colors text-slate-300 border border-slate-700">
                        <ZoomOut className="w-5 h-5" />
                    </button>
                    <button onClick={handleZoomIn} className="p-2 bg-slate-800 rounded-lg hover:bg-slate-700 transition-colors text-slate-300 border border-slate-700">
                        <ZoomIn className="w-5 h-5" />
                    </button>
                    <button onClick={handleFit} className="p-2 bg-slate-800 rounded-lg hover:bg-slate-700 transition-colors text-slate-300 border border-slate-700">
                        <Maximize className="w-5 h-5" />
                    </button>
                </div>
            </div>

            <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex-1 w-full bg-[#0b1120] rounded-2xl border border-indigo-500/20 shadow-2xl overflow-hidden relative"
                ref={containerRef}
            >
                <div className="absolute top-4 left-4 z-10 bg-slate-900/80 backdrop-blur-md p-4 rounded-xl border border-white/5 text-xs text-slate-300 pointer-events-none flex flex-col gap-2 shadow-lg">
                    <div className="font-semibold text-slate-100 mb-1">Legend</div>
                    <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-indigo-500" /> Scheme
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-cyan-500" /> Criterion
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-emerald-500" /> Benefit
                    </div>
                </div>

                <ForceGraph2D
                    ref={fgRef}
                    width={dimensions.width}
                    height={dimensions.height}
                    graphData={gData}
                    nodeAutoColorBy="group"
                    nodeRelSize={6}
                    linkColor={() => 'rgba(99, 102, 241, 0.4)'}
                    linkWidth={1.5}
                    linkDirectionalParticles={2}
                    linkDirectionalParticleSpeed={0.005}
                    nodeCanvasObject={(node, ctx, globalScale) => {
                        const label = node.label
                        const fontSize = 12 / globalScale
                        ctx.font = `${fontSize}px Sans-Serif`
                        const textWidth = ctx.measureText(label).width
                        const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2)

                        let color = '#4f46e5' // indigo
                        if (node.group === "EligibilityCriterion") color = '#06b6d4' // cyan
                        if (node.group === "Benefit") color = '#10b981' // emerald
                        if (node.group === "State") color = '#f59e0b' // amber
                        if (node.group === "TargetGroup" || node.group === "Category") color = '#db2777' // pink

                        ctx.beginPath()
                        ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false)
                        ctx.fillStyle = color
                        ctx.fill()

                        // Glow effect
                        ctx.shadowBlur = 10
                        ctx.shadowColor = color

                        ctx.textAlign = 'center'
                        ctx.textBaseline = 'middle'
                        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)'
                        ctx.fillText(label, node.x, node.y + 10)
                    }}
                    enableNodeDrag={true}
                    enableZoomInteraction={true}
                    enablePanInteraction={true}
                />
            </motion.div>
        </div>
    )
}
