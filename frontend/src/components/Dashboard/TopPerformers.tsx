interface TopPerformer {
  employee_id: number;
  employee_name: string;
  amount: number;
}

interface TopPerformersProps {
  commissions: TopPerformer[];
}

export default function TopPerformers({ commissions }: TopPerformersProps) {
  if (!commissions || commissions.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No commission data available for this period.</p>
        <p className="text-sm mt-2">Run commission calculations to see top performers.</p>
      </div>
    );
  }

  return (
    <div className="flow-root">
      <ul className="-my-5 divide-y divide-gray-200">
        {commissions.slice(0, 5).map((performer, index) => (
          <li key={performer.employee_id} className="py-4">
            <div className="flex items-center space-x-4">
              <div className="flex-shrink-0">
                <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                  <span className="text-sm font-medium text-gray-600">
                    {index + 1}
                  </span>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {performer.employee_name}
                </p>
                <p className="text-sm text-gray-500">
                  Employee #{performer.employee_id}
                </p>
              </div>
              <div>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  ${performer.amount.toLocaleString()}
                </span>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}