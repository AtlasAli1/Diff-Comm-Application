'use client';

import { Dialog } from '@headlessui/react';

interface SmartAddModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SmartAddModal({ isOpen, onClose }: SmartAddModalProps) {
  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
      
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-lg rounded bg-white p-6">
          <Dialog.Title className="text-lg font-medium text-gray-900">
            Smart Add from Timesheet
          </Dialog.Title>
          
          <div className="mt-4">
            <p className="text-sm text-gray-500">
              Smart employee detection from timesheet data will be implemented here.
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
              Add Selected
            </button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
}