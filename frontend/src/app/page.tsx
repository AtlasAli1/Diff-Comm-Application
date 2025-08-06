'use client';

import { useState, useEffect } from 'react';
import { Tab } from '@headlessui/react';
import { cn } from '@/lib/utils';
import Dashboard from '@/components/Dashboard';
import CompanySetup from '@/components/CompanySetup';
import DataManagement from '@/components/DataManagement';
import CommissionCalc from '@/components/CommissionCalc';
import Reports from '@/components/Reports';
import PayPeriodSelector from '@/components/PayPeriodSelector';
import { useAppState } from '@/contexts/AppStateContext';
import { useQuery } from '@tanstack/react-query';
import { payPeriodService } from '@/lib/api/services';

const tabs = [
  { name: '🏠 Dashboard', component: Dashboard },
  { name: '⚙️ Company Setup', component: CompanySetup },
  { name: '📊 Data Management', component: DataManagement },
  { name: '🧮 Commission Calc', component: CommissionCalc },
  { name: '📈 Reports', component: Reports },
];

export default function Home() {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const { setCurrentPayPeriod } = useAppState();

  // Load current pay period on mount
  const { data: currentPayPeriod, isLoading } = useQuery({
    queryKey: ['currentPayPeriod'],
    queryFn: payPeriodService.getCurrentPayPeriod,
    onSuccess: (data) => {
      setCurrentPayPeriod(data);
    },
  });

  const CurrentComponent = tabs[selectedIndex].component;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-gray-900">
              Commission Calculator Pro
            </h1>
            <PayPeriodSelector />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Tab.Group selectedIndex={selectedIndex} onChange={setSelectedIndex}>
          <Tab.List className="flex space-x-1 rounded-xl bg-blue-900/20 p-1 mb-6">
            {tabs.map((tab) => (
              <Tab
                key={tab.name}
                className={({ selected }) =>
                  cn(
                    'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                    'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                    selected
                      ? 'bg-white text-blue-700 shadow'
                      : 'text-blue-100 hover:bg-white/[0.12] hover:text-white'
                  )
                }
              >
                {tab.name}
              </Tab>
            ))}
          </Tab.List>
          
          <Tab.Panels>
            {tabs.map((tab, idx) => (
              <Tab.Panel
                key={idx}
                className={cn(
                  'rounded-xl bg-white p-3',
                  'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2'
                )}
              >
                {selectedIndex === idx && <CurrentComponent />}
              </Tab.Panel>
            ))}
          </Tab.Panels>
        </Tab.Group>
      </main>
    </div>
  );
}