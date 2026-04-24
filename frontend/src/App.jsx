import { useState } from 'react';
import Sidebar from './components/Sidebar';
import AIChatbot from './components/AIChatbot';
import Overview from './pages/Overview';
import DataExplorer from './pages/DataExplorer';
import Segmentation from './pages/Segmentation';
import SegmentBleeding from './pages/SegmentBleeding';
import RetentionPlanner from './pages/RetentionPlanner';
import BundleOpportunity from './pages/BundleOpportunity';
import SeasonalAnalysis from './pages/SeasonalAnalysis';

const PAGES = {
  overview: { component: Overview, label: 'Overview' },
  explorer: { component: DataExplorer, label: 'Data Explorer' },
  segmentation: { component: Segmentation, label: 'Segmentation' },
  bleeding: { component: SegmentBleeding, label: 'Segment Bleeding' },
  retention: { component: RetentionPlanner, label: 'Retention Planner' },
  bundle: { component: BundleOpportunity, label: 'Bundle Opportunity' },
  seasonal: { component: SeasonalAnalysis, label: 'Seasonal Analysis' },
};

export default function App() {
  const [currentPage, setCurrentPage] = useState('overview');
  const [chatOpen, setChatOpen] = useState(false);

  const PageComponent = PAGES[currentPage]?.component || Overview;

  return (
    <div className="flex h-screen bg-dark-900 text-gray-50 overflow-hidden">
      <Sidebar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        pages={PAGES}
      />
      <main className="flex-1 overflow-y-auto p-6 lg:p-8">
        <PageComponent />
      </main>
      {/* Floating chat button */}
      <button
        id="ai-chat-toggle"
        onClick={() => setChatOpen(true)}
        className="fixed bottom-6 right-6 z-40 w-14 h-14 bg-blue-600 hover:bg-blue-500 rounded-full shadow-lg shadow-blue-600/30 flex items-center justify-center transition-all duration-200 hover:scale-110"
      >
        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </button>
      <AIChatbot isOpen={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  );
}
