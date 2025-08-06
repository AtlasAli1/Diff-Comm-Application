'use client';

export default function BusinessUnits() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Business Unit Setup</h3>
        <p className="mt-1 text-sm text-gray-600">
          Configure business units and their commission rates.
        </p>
      </div>
      
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800">
          Business Units component is being developed. This will include:
        </p>
        <ul className="list-disc list-inside mt-2 text-yellow-700">
          <li>Add/edit business units</li>
          <li>Set commission rates for lead gen, sales, and work done</li>
          <li>Smart detect units from revenue data</li>
          <li>Bulk operations</li>
        </ul>
      </div>
    </div>
  );
}