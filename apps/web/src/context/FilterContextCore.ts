import { createContext, useContext } from 'react';
import type { GlobalFilterOptions } from '../types';

export interface FilterContextType {
  selectedLocation: string;
  setSelectedLocation: (loc: string) => void;
  selectedCategory: string;
  setSelectedCategory: (cat: string) => void;
  options: GlobalFilterOptions;
  isLoading: boolean;
  refreshFilters: () => void;
}

export const defaultOptions: GlobalFilterOptions = {
  locations: [],
  categories: [],
  channels: [],
  segments: ['Champions', 'Loyal', 'At Risk', 'Lost'],
  classifications: ['Profit Driver', 'Volume Driver', 'Hidden Opportunity', 'Low Performer'],
};

export const FilterContext = createContext<FilterContextType>({
  selectedLocation: '',
  setSelectedLocation: () => {},
  selectedCategory: '',
  setSelectedCategory: () => {},
  options: defaultOptions,
  isLoading: false,
  refreshFilters: () => {},
});

export const useFilters = () => useContext(FilterContext);
