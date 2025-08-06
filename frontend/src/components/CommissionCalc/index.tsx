'use client';

export default function CommissionCalc() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Commission Calculator</h2>
        <p className="mt-1 text-sm text-gray-600">
          Calculate commissions for your employees based on the current pay period.
        </p>
      </div>
      
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800">
          Commission Calculator component is being developed. This will include:
        </p>
        <ul className="list-disc list-inside mt-2 text-yellow-700">
          <li>Select pay period and employees</li>
          <li>Run commission calculations</li>
          <li>View calculation progress</li>
          <li>Preview results before finalizing</li>
        </ul>
      </div>
    </div>
  );
}