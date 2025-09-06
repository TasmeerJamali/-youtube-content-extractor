import React from 'react';
import { SearchFiltersProps } from '../types/api';

const SearchFilters: React.FC<SearchFiltersProps> = ({
  filters,
  onChange,
  onApply
}) => {
  const contentTypes = [
    'tutorial', 'review', 'vlog', 'animation', 'music', 
    'gaming', 'news', 'comedy', 'documentary', 'educational'
  ];

  const durations = [
    { label: 'Any duration', min: undefined, max: undefined },
    { label: 'Short (< 5 min)', min: undefined, max: 300 },
    { label: 'Medium (5-20 min)', min: 300, max: 1200 },
    { label: 'Long (> 20 min)', min: 1200, max: undefined }
  ];

  const publishedRanges = [
    { label: 'Any time', value: '' },
    { label: 'Last 24 hours', value: '1d' },
    { label: 'Last week', value: '7d' },
    { label: 'Last month', value: '30d' },
    { label: 'Last year', value: '365d' }
  ];

  const handleContentTypeChange = (type: string, checked: boolean) => {
    const currentTypes = filters.content_types || [];
    const newTypes = checked
      ? [...currentTypes, type]
      : currentTypes.filter(t => t !== type);
    
    onChange({ content_types: newTypes });
  };

  const handleDurationChange = (duration: typeof durations[0]) => {
    onChange({
      min_duration: duration.min,
      max_duration: duration.max
    });
  };

  return (
    <div className="space-y-6">
      {/* Content Types */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3">Content Types</h4>
        <div className="space-y-2">
          {contentTypes.map(type => (
            <label key={type} className="custom-checkbox">
              <input
                type="checkbox"
                checked={filters.content_types?.includes(type) || false}
                onChange={(e) => handleContentTypeChange(type, e.target.checked)}
              />
              <span className="capitalize">{type}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Duration */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3">Duration</h4>
        <div className="space-y-2">
          {durations.map((duration, idx) => (
            <label key={idx} className="flex items-center">
              <input
                type="radio"
                name="duration"
                className="mr-2"
                checked={
                  filters.min_duration === duration.min && 
                  filters.max_duration === duration.max
                }
                onChange={() => handleDurationChange(duration)}
              />
              {duration.label}
            </label>
          ))}
        </div>
      </div>

      {/* Published Date */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3">Published</h4>
        <select
          value={filters.published_after || ''}
          onChange={(e) => {
            const value = e.target.value;
            if (value) {
              const date = new Date();
              const days = parseInt(value);
              date.setDate(date.getDate() - days);
              onChange({ published_after: date.toISOString() });
            } else {
              onChange({ published_after: undefined });
            }
          }}
          className="form-input w-full"
        >
          {publishedRanges.map(range => (
            <option key={range.value} value={range.value}>
              {range.label}
            </option>
          ))}
        </select>
      </div>

      {/* Region */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3">Region</h4>
        <select
          value={filters.region || 'US'}
          onChange={(e) => onChange({ region: e.target.value })}
          className="form-input w-full"
        >
          <option value="US">United States</option>
          <option value="GB">United Kingdom</option>
          <option value="CA">Canada</option>
          <option value="AU">Australia</option>
          <option value="DE">Germany</option>
          <option value="FR">France</option>
          <option value="JP">Japan</option>
          <option value="KR">South Korea</option>
        </select>
      </div>

      {/* Apply Button */}
      <button
        onClick={onApply}
        className="btn-primary w-full"
      >
        Apply Filters
      </button>
    </div>
  );
};

export default SearchFilters;