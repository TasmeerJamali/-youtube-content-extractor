import React, { useState } from 'react';
import { SearchFormData } from '../types/api';

interface SearchFormProps {
  onSearch: (params: SearchFormData) => void;
  isLoading: boolean;
  suggestions: string[];
  loadingSuggestions: boolean;
  initialValues?: Partial<SearchFormData>;
}

interface ApiKeyValidation {
  isValid: boolean | null;
  isValidating: boolean;
  error?: string;
}

const SearchForm: React.FC<SearchFormProps> = ({
  onSearch,
  isLoading,
  suggestions,
  loadingSuggestions,
  initialValues = {}
}) => {
  const [formData, setFormData] = useState<SearchFormData>({
    idea: '',
    max_results: 50,
    content_types: [],
    language: 'en',
    region: 'US',
    include_transcripts: false,
    include_comments: false,
    api_key: '',
    ...initialValues
  });

  const [showSuggestions, setShowSuggestions] = useState(false);
  const [apiKeyValidation, setApiKeyValidation] = useState<ApiKeyValidation>({
    isValid: null,
    isValidating: false
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.idea.trim()) {
      onSearch(formData);
      setShowSuggestions(false);
    }
  };

  const handleIdeaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setFormData(prev => ({ ...prev, idea: value }));
    setShowSuggestions(value.length > 2);
  };

  const selectSuggestion = (suggestion: string) => {
    setFormData(prev => ({ ...prev, idea: suggestion }));
    setShowSuggestions(false);
  };

  const validateApiKey = async (apiKey: string) => {
    if (!apiKey || !apiKey.trim()) {
      setApiKeyValidation({ isValid: null, isValidating: false });
      return;
    }

    setApiKeyValidation({ isValid: null, isValidating: true });

    try {
      const response = await fetch(`/api/v1/search/validate-api-key?api_key=${encodeURIComponent(apiKey)}`, {
        method: 'POST'
      });
      const result = await response.json();

      setApiKeyValidation({
        isValid: result.valid,
        isValidating: false,
        error: result.error
      });
    } catch (error) {
      setApiKeyValidation({
        isValid: false,
        isValidating: false,
        error: 'Failed to validate API key'
      });
    }
  };

  const handleApiKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setFormData(prev => ({ ...prev, api_key: value }));
    
    // Debounce validation
    if (value.trim()) {
      const timeoutId = setTimeout(() => validateApiKey(value), 1000);
      return () => clearTimeout(timeoutId);
    } else {
      setApiKeyValidation({ isValid: null, isValidating: false });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="form-label">
          Video Idea or Concept
        </label>
        <div className="relative">
          <textarea
            value={formData.idea}
            onChange={handleIdeaChange}
            placeholder="Describe the type of YouTube content you're looking for..."
            className="form-input h-24 resize-none"
            required
          />
          
          {/* Suggestions Dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="search-suggestions">
              {suggestions.slice(0, 5).map((suggestion, idx) => (
                <div
                  key={idx}
                  className="search-suggestion-item"
                  onClick={() => selectSuggestion(suggestion)}
                >
                  {suggestion}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="form-label">
            Max Results
          </label>
          <select
            value={formData.max_results}
            onChange={(e) => setFormData(prev => ({ ...prev, max_results: parseInt(e.target.value) }))}
            className="form-input"
          >
            <option value={25}>25 results</option>
            <option value={50}>50 results</option>
            <option value={100}>100 results</option>
            <option value={200}>200 results</option>
          </select>
        </div>

        <div>
          <label className="form-label">
            Language
          </label>
          <select
            value={formData.language}
            onChange={(e) => setFormData(prev => ({ ...prev, language: e.target.value }))}
            className="form-input"
          >
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="ja">Japanese</option>
            <option value="ko">Korean</option>
          </select>
        </div>
      </div>

      <div className="space-y-4">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-yellow-900 mb-2">🔑 YouTube API Key (Optional)</h4>
          <div className="relative">
            <input
              type="password"
              value={formData.api_key || ''}
              onChange={handleApiKeyChange}
              placeholder="Enter your YouTube API key (leave empty to use default)"
              className={`form-input w-full pr-10 ${
                apiKeyValidation.isValid === true ? 'border-green-500' :
                apiKeyValidation.isValid === false ? 'border-red-500' : ''
              }`}
            />
            
            {/* Validation Status */}
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              {apiKeyValidation.isValidating && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
              )}
              {apiKeyValidation.isValid === true && (
                <div className="text-green-600">✅</div>
              )}
              {apiKeyValidation.isValid === false && (
                <div className="text-red-600">❌</div>
              )}
            </div>
          </div>
          
          {/* Validation Error */}
          {apiKeyValidation.error && (
            <p className="text-xs text-red-600 mt-1">
              ⚠️ {apiKeyValidation.error}
            </p>
          )}
          
          <p className="text-xs text-yellow-700 mt-2">
            💡 <strong>Optional:</strong> Use your own YouTube API key for unlimited quota. 
            <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer" className="underline hover:text-yellow-800">Get your free API key here</a>
          </p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Advanced Options</h4>
          
          <label className="custom-checkbox">
            <input
              type="checkbox"
              checked={formData.include_transcripts}
              onChange={(e) => setFormData(prev => ({ ...prev, include_transcripts: e.target.checked }))}
            />
            <span className="font-medium">Include video transcripts</span>
          </label>
          <p className="text-xs text-blue-700 mt-1 ml-6">
            📝 Extracts full video captions/subtitles • View & download transcripts • Slower but more accurate results
          </p>
        </div>

        <label className="custom-checkbox">
          <input
            type="checkbox"
            checked={formData.include_comments}
            onChange={(e) => setFormData(prev => ({ ...prev, include_comments: e.target.checked }))}
          />
          <span>Include top comments</span>
        </label>
      </div>

      <button
        type="submit"
        disabled={isLoading || !formData.idea.trim()}
        className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            Searching...
          </div>
        ) : (
          'Search Content'
        )}
      </button>
    </form>
  );
};

export default SearchForm;