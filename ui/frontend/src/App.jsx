import { BrowserRouter, Routes, Route } from "react-router-dom"
import { Layout } from "./components/layout/Layout"
import Landing from "./pages/Landing"
import Search from "./pages/Search"
import Eligibility from "./pages/Eligibility"
import GraphPage from "./pages/GraphPage"
import Dashboard from "./pages/Dashboard"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Landing />} />
          <Route path="/search" element={<Search />} />
          <Route path="/eligibility" element={<Eligibility />} />
          <Route path="/graph" element={<GraphPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
