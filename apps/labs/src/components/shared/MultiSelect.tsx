'use client';

import { useState, useRef, useEffect } from 'react';

export interface MultiSelectOption {
  value: string;
  label: string;
}

interface MultiSelectProps {
  label: string;
  options: MultiSelectOption[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder?: string;
}

export function MultiSelect({
  label,
  options,
  selected,
  onChange,
  placeholder = 'Select...',
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  const displayText = selected.length === 0
    ? placeholder
    : selected.length === options.length
    ? 'All'
    : selected
        .map((val) => options.find((opt) => opt.value === val)?.label)
        .filter(Boolean)
        .join(', ');

  return (
    <div ref={containerRef} className="relative flex flex-col gap-2">
      <label className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
        {label}
      </label>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="h-[42px] w-full border border-gray-300 bg-white px-4 text-left text-sm font-medium text-gray-900 focus:border-rb-brand-navy focus:outline-none flex items-center justify-between"
      >
        <span className="truncate">{displayText}</span>
        <svg
          className={`h-4 w-4 flex-shrink-0 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 z-50 mt-1 w-full border-2 border-rb-brand-navy bg-white shadow-lg">
          {options.map((option) => {
            const isSelected = selected.includes(option.value);
            return (
              <label
                key={option.value}
                className="flex cursor-pointer items-center gap-3 px-4 py-3 text-sm text-gray-900 transition hover:bg-gray-100"
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => handleToggle(option.value)}
                  className="h-4 w-4 border-gray-300 text-rb-brand-navy focus:ring-rb-brand-navy"
                />
                <span>{option.label}</span>
              </label>
            );
          })}
        </div>
      )}
    </div>
  );
}
