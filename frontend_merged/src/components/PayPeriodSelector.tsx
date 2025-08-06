'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { Badge } from '@/components/ui/badge';
import { Calendar, Check, ChevronsUpDown, Clock } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { payPeriodService } from '@/lib/api/services';
import { useAppState } from '@/contexts/AppStateContext';
import { formatPayPeriodRange, isPayPeriodActive } from '@/lib/utils';
import { cn } from '@/lib/utils';

export function PayPeriodSelector() {
  const [open, setOpen] = useState(false);
  const { currentPayPeriod, setCurrentPayPeriod } = useAppState();

  // Get all pay periods - this is central to our system
  const { data: payPeriods, isLoading } = useQuery({
    queryKey: ['payPeriods'],
    queryFn: () => payPeriodService.getPayPeriods({ limit: 50 }),
  });

  const handleSelect = (period: any) => {
    setCurrentPayPeriod(period);
    setOpen(false);
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2">
        <Calendar className="h-4 w-4 animate-pulse" />
        <div className="h-6 w-48 bg-muted animate-pulse rounded" />
      </div>
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-[280px] justify-between"
        >
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            {currentPayPeriod ? (
              <span className="truncate">
                {formatPayPeriodRange(currentPayPeriod.start_date, currentPayPeriod.end_date)}
              </span>
            ) : (
              "Select pay period..."
            )}
          </div>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[320px] p-0">
        <Command>
          <CommandInput placeholder="Search pay periods..." />
          <CommandList>
            <CommandEmpty>No pay periods found.</CommandEmpty>
            <CommandGroup>
              {payPeriods?.items.map((period) => {
                const isActive = isPayPeriodActive(period);
                const isCurrent = currentPayPeriod?.id === period.id;
                
                return (
                  <CommandItem
                    key={period.id}
                    value={`${period.period_number} ${formatPayPeriodRange(period.start_date, period.end_date)}`}
                    onSelect={() => handleSelect(period)}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <Check
                        className={cn(
                          "h-4 w-4",
                          isCurrent ? "opacity-100" : "opacity-0"
                        )}
                      />
                      <div>
                        <div className="font-medium">
                          Period #{period.period_number}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {formatPayPeriodRange(period.start_date, period.end_date)}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-1">
                      {isActive && (
                        <Badge variant="default" className="gap-1">
                          <Clock className="h-3 w-3" />
                          Current
                        </Badge>
                      )}
                      <Badge 
                        variant={
                          period.status === 'Active' ? 'default' :
                          period.status === 'Completed' ? 'secondary' : 'outline'
                        }
                        className="text-xs"
                      >
                        {period.status}
                      </Badge>
                    </div>
                  </CommandItem>
                );
              })}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}