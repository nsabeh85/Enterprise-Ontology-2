import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import Overview from './pages/Overview';
import QueryRewriter from './pages/QueryRewriter';
import Adoption from './pages/Adoption';
import Feedback from './pages/Feedback';
import ContentHealth from './pages/ContentHealth';

// Color palette (shared across app)
export const COLORS = {
  purple: 'oklch(0.488 0.243 264.376)',
  cyan: 'oklch(0.696 0.17 162.48)',
  orange: 'oklch(0.769 0.188 70.08)',
  pink: 'oklch(0.627 0.265 303.9)',
  red: 'oklch(0.645 0.246 16.439)',
  green: 'oklch(0.723 0.219 142.18)',
  background: '#0f0f1a',
  surface: '#1a1a2e',
  textPrimary: '#fafafa',
  textMuted: '#9ca3af',
};

function App() {
  return (
    <Router>
      <div className="min-h-screen" style={{ background: COLORS.background }}>
        <Navigation />
        <main className="p-6 md:p-8 lg:p-10">
          <div className="max-w-7xl mx-auto">
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/query-rewriter" element={<QueryRewriter />} />
              <Route path="/adoption" element={<Adoption />} />
              <Route path="/feedback" element={<Feedback />} />
              <Route path="/content-health" element={<ContentHealth />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
