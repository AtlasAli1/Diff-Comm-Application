'use client';

export default function DataManagement() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Data Management</h2>
        <p className="mt-1 text-sm text-gray-600">
          Upload and manage your revenue and timesheet data.
        </p>
      </div>
      
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800">
          Data Management component is being developed. This will include:
        </p>
        <ul className="list-disc list-inside mt-2 text-yellow-700">
          <li>File upload for revenue and timesheet data</li>
          <li>Data validation and error reporting</li>
          <li>View and edit uploaded data</li>
          <li>Download CSV templates</li>
        </ul>
      </div>
    </div>
  );
}