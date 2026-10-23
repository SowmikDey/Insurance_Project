import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { GlossaryProvider } from './context/GlossaryContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { GlossaryPopover } from './components/GlossaryPopover';
import { GlossaryModal } from './components/GlossaryModal';

// Retained Core Feature Pages
import { HomePage } from './pages/HomePage';
import { LearnPage } from './pages/LearnPage';
import { ExplorerPage } from './pages/ExplorerPage';
import { PolicyDetailsPage } from './pages/PolicyDetailsPage';
import { AssistantPage } from './pages/AssistantPage';
import { GlossaryPage } from './pages/GlossaryPage';
import { AdminPage } from './pages/AdminPage';

export function App() {
  return (
    <GlossaryProvider>
      <Router>
        <div className="min-h-screen flex flex-col bg-[#F6F7F4] text-[#25313B]">
          <Navbar />

          <main className="flex-1">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/learn" element={<LearnPage />} />
              <Route path="/learn/:moduleSlug" element={<LearnPage />} />
              <Route path="/explore" element={<ExplorerPage />} />
              <Route path="/policies/:policySlug" element={<PolicyDetailsPage />} />
              <Route path="/assistant" element={<AssistantPage />} />
              <Route path="/glossary" element={<GlossaryPage />} />
              <Route path="/glossary/:termSlug" element={<GlossaryPage />} />
              <Route path="/admin" element={<AdminPage />} />
            </Routes>
          </main>

          <Footer />

          {/* Global Zerodha Varsity-Style Contextual Popover & Modal */}
          <GlossaryPopover />
          <GlossaryModal />
        </div>
      </Router>
    </GlossaryProvider>
  );
}

export default App;
