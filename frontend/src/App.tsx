import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { WizardProvider } from './context/WizardContext';
import { WizardPage } from './pages/WizardPage';
import { HistoryPage } from './pages/HistoryPage';
import { Scissors, History, PlusCircle } from 'lucide-react';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const isHistory = location.pathname === '/history';

  return (
    <div className="min-h-screen bg-zinc-950 text-white flex flex-col">
      <header className="border-b border-zinc-800 bg-zinc-950/80 sticky top-0 z-10 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-xl font-bold hover:text-red-500 transition-colors">
            <Scissors className="text-red-600" />
            <span>YouTube Cutter</span>
          </Link>
          <nav className="flex items-center gap-4">
            <Link 
              to="/" 
              className={`flex items-center gap-2 text-sm font-medium transition-colors ${!isHistory ? 'text-red-500' : 'text-zinc-400 hover:text-zinc-200'}`}
            >
              <PlusCircle size={18} />
              Novo Trabalho
            </Link>
            <Link 
              to="/history" 
              className={`flex items-center gap-2 text-sm font-medium transition-colors ${isHistory ? 'text-red-500' : 'text-zinc-400 hover:text-zinc-200'}`}
            >
              <History size={18} />
              Histórico
            </Link>
          </nav>
        </div>
      </header>
      <main className="flex-1 w-full max-w-6xl mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  );
};

function App() {
  return (
    <WizardProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<WizardPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </Layout>
      </Router>
    </WizardProvider>
  );
}

export default App;
