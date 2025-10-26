import { useState, useCallback } from 'react';

export function useFilters() {
  const [filters, setFilters] = useState({
    cycle: 2026,
    chamber: 'both', // 'H', 'S', or 'both'
    state: 'all',
    district: 'all',
    candidates: [], // array of candidate IDs
    metrics: {
      totalRaised: true,
      totalDisbursed: true,
      cashOnHand: true
    }
  });

  const updateFilter = useCallback((key, value) => {
    setFilters(prev => {
      const updated = { ...prev, [key]: value };
      
      // Reset district when chamber changes to Senate or Both
      if (key === 'chamber' && value !== 'H') {
        updated.district = 'all';
      }
      
      // Reset district when state changes
      if (key === 'state') {
        updated.district = 'all';
      }
      
      return updated;
    });
  }, []);

  const updateMetric = useCallback((metric, value) => {
    setFilters(prev => ({
      ...prev,
      metrics: {
        ...prev.metrics,
        [metric]: value
      }
    }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({
      cycle: 2026,
      chamber: 'both',
      state: 'all',
      district: 'all',
      candidates: [],
      metrics: {
        totalRaised: true,
        totalDisbursed: true,
        cashOnHand: true
      }
    });
  }, []);

  return {
    filters,
    updateFilter,
    updateMetric,
    resetFilters
  };
}