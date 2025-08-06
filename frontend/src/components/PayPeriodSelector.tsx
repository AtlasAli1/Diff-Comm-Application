'use client';

import { Fragment } from 'react';
import { Listbox, Transition } from '@headlessui/react';
import { CheckIcon, ChevronUpDownIcon } from '@heroicons/react/20/solid';
import { useQuery } from '@tanstack/react-query';
import { payPeriodService } from '@/lib/api/services';
import { useAppState } from '@/contexts/AppStateContext';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

export default function PayPeriodSelector() {
  const { currentPayPeriod, setCurrentPayPeriod } = useAppState();

  const { data: payPeriods, isLoading } = useQuery({
    queryKey: ['payPeriods'],
    queryFn: () => payPeriodService.getPayPeriods({ limit: 50 }),
  });

  const handleChange = (period: any) => {
    setCurrentPayPeriod(period);
  };

  if (isLoading) {
    return <div className="animate-pulse h-10 w-64 bg-gray-200 rounded"></div>;
  }

  return (
    <Listbox value={currentPayPeriod} onChange={handleChange}>
      <div className="relative">
        <Listbox.Button className="relative w-full cursor-pointer rounded-lg bg-white py-2 pl-3 pr-10 text-left shadow-md focus:outline-none focus-visible:border-indigo-500 focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-opacity-75 focus-visible:ring-offset-2 focus-visible:ring-offset-orange-300 sm:text-sm">
          <span className="block truncate">
            {currentPayPeriod ? (
              <>
                {format(new Date(currentPayPeriod.start_date), 'MMM d')} -{' '}
                {format(new Date(currentPayPeriod.end_date), 'MMM d, yyyy')}
                <span className="ml-2 text-xs text-gray-500">
                  ({currentPayPeriod.status})
                </span>
              </>
            ) : (
              'Select Pay Period'
            )}
          </span>
          <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
            <ChevronUpDownIcon
              className="h-5 w-5 text-gray-400"
              aria-hidden="true"
            />
          </span>
        </Listbox.Button>
        <Transition
          as={Fragment}
          leave="transition ease-in duration-100"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
            {payPeriods?.items.map((period) => (
              <Listbox.Option
                key={period.id}
                className={({ active }) =>
                  cn(
                    'relative cursor-pointer select-none py-2 pl-10 pr-4',
                    active ? 'bg-amber-100 text-amber-900' : 'text-gray-900'
                  )
                }
                value={period}
              >
                {({ selected }) => (
                  <>
                    <span
                      className={cn(
                        'block truncate',
                        selected ? 'font-medium' : 'font-normal'
                      )}
                    >
                      {format(new Date(period.start_date), 'MMM d')} -{' '}
                      {format(new Date(period.end_date), 'MMM d, yyyy')}
                      <span
                        className={cn(
                          'ml-2 text-xs',
                          period.status === 'Active'
                            ? 'text-green-600'
                            : period.status === 'Completed'
                            ? 'text-gray-500'
                            : 'text-blue-600'
                        )}
                      >
                        ({period.status})
                      </span>
                    </span>
                    {selected ? (
                      <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-amber-600">
                        <CheckIcon className="h-5 w-5" aria-hidden="true" />
                      </span>
                    ) : null}
                  </>
                )}
              </Listbox.Option>
            ))}
          </Listbox.Options>
        </Transition>
      </div>
    </Listbox>
  );
}