export function CycleToggle({ value, onChange }) {
  const cycles = [2026, 2024, 2022, 2020];

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-gray-700">
        Election Cycle
      </label>
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-28 h-[42px] px-3 py-2 text-sm font-semibold border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-rb-red focus:border-rb-red"
      >
        {cycles.map(cycle => (
          <option key={cycle} value={cycle}>
            {cycle}
          </option>
        ))}
      </select>
    </div>
  );
}