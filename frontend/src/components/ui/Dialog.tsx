import React from 'react';

interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export const Dialog: React.FC<DialogProps> = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-0">
      <div className="fixed inset-0 bg-black/80 transition-opacity" onClick={onClose}></div>
      <div className="relative bg-zinc-900 rounded-xl shadow-xl w-full max-w-md border border-zinc-800 overflow-hidden">
        <div className="p-6">
          <h3 className="text-lg font-medium text-white mb-4">{title}</h3>
          <div className="text-zinc-300">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};
