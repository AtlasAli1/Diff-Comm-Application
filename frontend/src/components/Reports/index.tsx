'use client';

export default function Reports() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Reports</h2>
        <p className="mt-1 text-sm text-gray-600">
          View and export detailed commission reports and analytics.
        </p>
      </div>
      
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800">
          Reports component is being developed. This will include:
        </p>
        <ul className="list-disc list-inside mt-2 text-yellow-700">
          <li>Detailed commission reports per employee</li>
          <li>Revenue analysis by business unit</li>
          <li>Employee performance tracking</li>
          <li>Export to PDF and CSV</li>
        </ul>
      </div>
    </div>
  );
}