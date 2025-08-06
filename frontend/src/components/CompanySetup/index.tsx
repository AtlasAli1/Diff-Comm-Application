'use client';

import { useState } from 'react';
import { Tab } from '@headlessui/react';
import { cn } from '@/lib/utils';
import PayPeriods from './PayPeriods';
import Employees from './Employees';
import BusinessUnits from './BusinessUnits';
import AdvancedSettings from './AdvancedSettings';

const tabs = [
  { name: '📅 Pay Periods', component: PayPeriods },
  { name: '👥 Employees', component: Employees },
  { name: '🏢 Business Units', component: BusinessUnits },
  { name: '🔧 Advanced Settings', component: AdvancedSettings },
];

export default function CompanySetup() {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const CurrentComponent = tabs[selectedIndex].component;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Company Setup</h2>
        <p className="mt-1 text-sm text-gray-600">
          Configure your company settings, employees, and commission structures.
        </p>
      </div>

      <Tab.Group selectedIndex={selectedIndex} onChange={setSelectedIndex}>
        <Tab.List className="flex space-x-1 rounded-xl bg-gray-100 p-1">
          {tabs.map((tab) => (
            <Tab
              key={tab.name}
              className={({ selected }) =>
                cn(
                  'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                  'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                  selected
                    ? 'bg-white text-blue-700 shadow'
                    : 'text-gray-700 hover:bg-white/[0.12] hover:text-gray-900'
                )
              }
            >
              {tab.name}
            </Tab>
          ))}
        </Tab.List>
        
        <Tab.Panels className="mt-4">
          {tabs.map((tab, idx) => (
            <Tab.Panel
              key={idx}
              className={cn(
                'rounded-xl bg-white p-6',
                'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2'
              )}
            >
              {selectedIndex === idx && <CurrentComponent />}
            </Tab.Panel>
          ))}
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
}