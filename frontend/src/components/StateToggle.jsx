import { useState, useMemo } from 'react';

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
];

export function StateToggle({ value, onChange }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const filteredStates = useMemo(() => {
    if (!searchTerm) return US_STATES;
    return US_STATES.filter(state =>
      state.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [searchTerm]);

  const handleSelect = (state) => {
    onChange(state);
    setSearchTerm('');
    setIsOpen(false);
  };

  return (
    <div className="flex flex-col gap-2 relative">
      <label className="text-sm font-medium text-gray-700">
        State
      </label>
      <div className="relative">
        <input
          type="text"
          value={isOpen ? searchTerm : (value === 'all' ? 'All States' : value)}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setTimeout(() => setIsOpen(false), 200)}
          placeholder="Search states..."
          className="w-40 h-[42px] px-3 py-2 text-sm font-semibold border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-rb-red focus:border-rb-red"
        />
        {isOpen && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
            <button
              type="button"
              onClick={() => handleSelect('all')}
              className="w-full px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
            >
              All States
            </button>
            {filteredStates.map(state => (
              <button
                key={state}
                type="button"
                onClick={() => handleSelect(state)}
                className="w-full px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
              >
                {state}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}