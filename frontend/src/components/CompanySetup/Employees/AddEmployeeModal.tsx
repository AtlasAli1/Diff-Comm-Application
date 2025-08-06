'use client';

import { Dialog } from '@headlessui/react';
import { Employee } from '@/types/employee';

interface AddEmployeeModalProps {
  isOpen: boolean;
  onClose: () => void;
  employee: Employee | null;
}

export default function AddEmployeeModal({ isOpen, onClose, employee }: AddEmployeeModalProps) {
  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
      
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-sm rounded bg-white p-6">
          <Dialog.Title className="text-lg font-medium text-gray-900">
            {employee ? 'Edit Employee' : 'Add New Employee'}
          </Dialog.Title>
          
          <div className="mt-4">
            <p className="text-sm text-gray-500">
              Employee form will be implemented here.
            </p>
          </div>
          
          <div className="mt-6 flex justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={onClose}
              className="btn-primary"
            >
              Save
            </button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
}