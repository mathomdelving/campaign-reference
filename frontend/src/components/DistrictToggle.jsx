import { useState, useEffect } from 'react';
import { supabase } from '../utils/supabaseClient';

// Valid district counts per state (as of 2022 redistricting)
const VALID_DISTRICT_COUNTS = {
  'AL': 7, 'AK': 1, 'AZ': 9, 'AR': 4, 'CA': 52, 'CO': 8, 'CT': 5, 'DE': 1,
  'FL': 28, 'GA': 14, 'HI': 2, 'ID': 2, 'IL': 17, 'IN': 9, 'IA': 4, 'KS': 4,
  'KY': 6, 'LA': 6, 'ME': 2, 'MD': 8, 'MA': 9, 'MI': 13, 'MN': 8, 'MS': 4,
  'MO': 8, 'MT': 2, 'NE': 3, 'NV': 4, 'NH': 2, 'NJ': 12, 'NM': 3, 'NY': 26,
  'NC': 14, 'ND': 1, 'OH': 15, 'OK': 5, 'OR': 6, 'PA': 17, 'RI': 2, 'SC': 7,
  'SD': 1, 'TN': 9, 'TX': 38, 'UT': 4, 'VT': 1, 'VA': 11, 'WA': 10, 'WV': 2,
  'WI': 8, 'WY': 1, 'DC': 0
};

export function DistrictToggle({ value, onChange, state, chamber }) {
  const [districts, setDistricts] = useState([]);
  const [senateSeatClasses, setSenateSeatClasses] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function fetchDistricts() {
      if (state === 'all') {
        setDistricts([]);
        setSenateSeatClasses([]);
        return;
      }

      if (chamber === 'H') {
        // Fetch House districts
        setLoading(true);
        try {
          const { data, error } = await supabase
            .from('candidates')
            .select('district')
            .eq('state', state)
            .eq('office', 'H')
            .not('district', 'is', null)
            .order('district');

          if (error) throw error;

          // Get unique districts and filter out invalid ones
          const maxDistricts = VALID_DISTRICT_COUNTS[state] || 0;
          const uniqueDistricts = [...new Set(data.map(d => d.district))]
            .filter(d => {
              const districtNum = parseInt(d, 10);
              return !isNaN(districtNum) && districtNum > 0 && districtNum <= maxDistricts;
            })
            .sort((a, b) => parseInt(a, 10) - parseInt(b, 10));

          setDistricts(uniqueDistricts);
          setSenateSeatClasses([]);
        } catch (err) {
          console.error('Error fetching districts:', err);
        } finally {
          setLoading(false);
        }
      } else if (chamber === 'S') {
        // Fetch Senate seat classes for this state
        setLoading(true);
        try {
          const { data, error } = await supabase
            .from('candidates')
            .select('candidate_id')
            .eq('state', state)
            .eq('office', 'S')
            .eq('cycle', 2026);

          if (error) throw error;

          // Extract Senate class from candidate_id (second character)
          // S0 = Class II (2020/2026), S4 = Class I (2024/2030), S6 = Class III (2022/2028), S8 = Special
          const classMap = {
            '0': 'II',
            '4': 'I',
            '6': 'III',
            '8': 'Special'
          };

          const classes = [...new Set(
            data.map(c => {
              const classChar = c.candidate_id.charAt(1);
              return classMap[classChar] || 'Unknown';
            })
          )].sort();

          setSenateSeatClasses(classes);
          setDistricts([]);
        } catch (err) {
          console.error('Error fetching Senate seats:', err);
        } finally {
          setLoading(false);
        }
      }
    }

    fetchDistricts();
  }, [state, chamber]);

  if (chamber !== 'H' && chamber !== 'S') {
    return null;
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-gray-700">
        District
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={loading || state === 'all' || (chamber === 'H' && districts.length === 0) || (chamber === 'S' && senateSeatClasses.length === 0)}
        className="w-48 h-[42px] px-3 py-2 text-sm font-semibold border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-rb-red focus:border-rb-red disabled:bg-gray-100 disabled:cursor-not-allowed"
      >
        <option value="all">
          {chamber === 'H' ? 'All Districts' : 'All Senate Seats'}
        </option>
        {chamber === 'H' && districts.map(district => (
          <option key={district} value={district}>
            District {district}
          </option>
        ))}
        {chamber === 'S' && senateSeatClasses.map(seatClass => (
          <option key={seatClass} value={seatClass}>
            Class {seatClass}
          </option>
        ))}
      </select>
    </div>
  );
}