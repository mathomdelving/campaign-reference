import { CycleToggle } from './CycleToggle';
import { ChamberToggle } from './ChamberToggle';
import { StateToggle } from './StateToggle';
import { DistrictToggle } from './DistrictToggle';
import { MetricToggle } from './MetricToggle';

export function ToggleBar({ filters, updateFilter, updateMetric, resetFilters }) {
  return (
    <div className="bg-white border-b border-gray-200 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
          <button
            onClick={resetFilters}
            className="text-sm text-rb-red hover:text-rb-blue font-medium"
          >
            Reset All
          </button>
        </div>

        <div className="flex items-end gap-4 flex-wrap">
          <CycleToggle
            value={filters.cycle}
            onChange={(value) => updateFilter('cycle', value)}
          />

          <ChamberToggle
            value={filters.chamber}
            onChange={(value) => updateFilter('chamber', value)}
          />

          <StateToggle
            value={filters.state}
            onChange={(value) => updateFilter('state', value)}
          />

          <DistrictToggle
            value={filters.district}
            onChange={(value) => updateFilter('district', value)}
            state={filters.state}
            chamber={filters.chamber}
          />

          <MetricToggle
            metrics={filters.metrics}
            onChange={updateMetric}
          />
        </div>
      </div>
    </div>
  );
}