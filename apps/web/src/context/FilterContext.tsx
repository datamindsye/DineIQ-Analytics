import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import type { GlobalFilterOptions } from '../types';
import { FilterContext, defaultOptions } from './FilterContextCore';

export const FilterProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedLocation, setSelectedLocation] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [options, setOptions] = useState<GlobalFilterOptions>(defaultOptions);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const loadFilters = React.useCallback(() => {
    let isMounted = true;
    apiService
      .getFilters()
      .then((opts) => {
        if (isMounted) {
          setOptions(opts);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.warn('Failed loading global filters, using defaults:', err);
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    return loadFilters();
  }, [loadFilters]);

  const handleRefresh = React.useCallback(() => {
    setIsLoading(true);
    loadFilters();
  }, [loadFilters]);

  return (
    <FilterContext.Provider
      value={{
        selectedLocation,
        setSelectedLocation,
        selectedCategory,
        setSelectedCategory,
        options,
        isLoading,
        refreshFilters: handleRefresh,
      }}
    >
      {children}
    </FilterContext.Provider>
  );
};
