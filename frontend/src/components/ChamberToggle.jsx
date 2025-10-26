export function ChamberToggle({ value, onChange }) {
  const options = [
    { value: 'both', label: 'Both' },
    { value: 'H', label: 'House' },
    { value: 'S', label: 'Senate' }
  ];

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-gray-700">
        Chamber
      </label>
      <div className="inline-flex rounded-md shadow-sm h-[42px]" role="group">
        {options.map(option => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={`
              px-4 py-2 text-sm font-semibold border
              ${option.value === 'both' ? 'rounded-l-md' : ''}
              ${option.value === 'S' ? 'rounded-r-md' : ''}
              ${option.value !== 'both' && option.value !== 'S' ? '-ml-px' : ''}
              ${value === option.value
                ? 'bg-rb-red text-white border-rb-red z-10'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }
              focus:z-10 focus:outline-none focus:ring-2 focus:ring-rb-red
            `}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}