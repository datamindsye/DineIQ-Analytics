import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { FilterProvider } from './context/FilterContext';
import { CustomerIntelligencePage } from './pages/CustomerIntelligencePage';
import { DashboardPage } from './pages/DashboardPage';
import { DataScienceArenaPage } from './pages/DataScienceArenaPage';
import { DemandPricingPage } from './pages/DemandPricingPage';
import { HealthPage } from './pages/HealthPage';
import { MenuIntelligencePage } from './pages/MenuIntelligencePage';
import { PromotionsBasketPage } from './pages/PromotionsBasketPage';
import { RatingsAnomaliesPage } from './pages/RatingsAnomaliesPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { SalesOperationsPage } from './pages/SalesOperationsPage';
import { WastageInventoryPage } from './pages/WastageInventoryPage';
import { WhatIfPage } from './pages/WhatIfPage';

export const App: React.FC = () => {
  return (
    <FilterProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="menu" element={<MenuIntelligencePage />} />
            <Route path="customers" element={<CustomerIntelligencePage />} />
            <Route path="sales" element={<SalesOperationsPage />} />
            <Route path="demand-pricing" element={<DemandPricingPage />} />
            <Route path="wastage" element={<WastageInventoryPage />} />
            <Route path="promotions" element={<PromotionsBasketPage />} />
            <Route path="anomalies" element={<RatingsAnomaliesPage />} />
            <Route path="arena" element={<DataScienceArenaPage />} />
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="what-if" element={<WhatIfPage />} />
            <Route path="health" element={<HealthPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </FilterProvider>
  );
};

export default App;
