import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { AppLayout } from './components/layout/AppLayout';
import { AuthProvider } from './context/AuthContext';
import { FilterProvider } from './context/FilterContext';
import { CustomerIntelligencePage } from './pages/CustomerIntelligencePage';
import { DashboardPage } from './pages/DashboardPage';
import { DataScienceArenaPage } from './pages/DataScienceArenaPage';
import { DemandPricingPage } from './pages/DemandPricingPage';
import { HealthPage } from './pages/HealthPage';
import { LoginPage } from './pages/LoginPage';
import { MenuIntelligencePage } from './pages/MenuIntelligencePage';
import { PromotionsBasketPage } from './pages/PromotionsBasketPage';
import { RatingsAnomaliesPage } from './pages/RatingsAnomaliesPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { SalesOperationsPage } from './pages/SalesOperationsPage';
import { WastageInventoryPage } from './pages/WastageInventoryPage';
import { WhatIfPage } from './pages/WhatIfPage';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <FilterProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route
                index
                element={
                  <ProtectedRoute
                    allowedRoles={['Admin', 'StoreManager', 'DataScientist']}
                    pageTitle="Executive Overview"
                  >
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="menu"
                element={
                  <ProtectedRoute
                    allowedRoles={['Admin', 'StoreManager', 'DataScientist', 'Cashier']}
                    pageTitle="Menu Intelligence"
                  >
                    <MenuIntelligencePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="customers"
                element={
                  <ProtectedRoute
                    allowedRoles={['Admin', 'StoreManager', 'DataScientist']}
                    pageTitle="Customer & RFM Intelligence"
                  >
                    <CustomerIntelligencePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="sales"
                element={
                  <ProtectedRoute
                    allowedRoles={['Admin', 'StoreManager', 'DataScientist']}
                    pageTitle="Sales & Operations"
                  >
                    <SalesOperationsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="demand-pricing"
                element={
                  <ProtectedRoute
                    allowedRoles={['Admin', 'StoreManager', 'DataScientist']}
                    pageTitle="Demand & Pricing"
                  >
                    <DemandPricingPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="wastage"
                element={
                  <ProtectedRoute
                    allowedRoles={['Admin', 'StoreManager', 'DataScientist']}
                    pageTitle="Wastage & Inventory"
                  >
                    <WastageInventoryPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="promotions"
                element={
                  <ProtectedRoute
                    allowedRoles={['Admin', 'StoreManager', 'DataScientist']}
                    pageTitle="Promotions & Basket Analysis"
                  >
                    <PromotionsBasketPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="anomalies"
                element={
                  <ProtectedRoute
                    allowedRoles={['Admin', 'StoreManager', 'DataScientist']}
                    pageTitle="Ratings & Anomalies"
                  >
                    <RatingsAnomaliesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="arena"
                element={
                  <ProtectedRoute
                    allowedRoles={['Admin', 'DataScientist']}
                    pageTitle="Data Science Arena"
                  >
                    <DataScienceArenaPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="recommendations"
                element={
                  <ProtectedRoute
                    allowedRoles={['Admin', 'StoreManager', 'DataScientist']}
                    pageTitle="Strategic Recommendations"
                  >
                    <RecommendationsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="what-if"
                element={
                  <ProtectedRoute
                    allowedRoles={['Admin', 'StoreManager', 'DataScientist']}
                    pageTitle="What-If Scenario Simulation"
                  >
                    <WhatIfPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="health"
                element={
                  <ProtectedRoute
                    allowedRoles={['Admin', 'StoreManager', 'DataScientist', 'Cashier']}
                    pageTitle="Pipelines & Health"
                  >
                    <HealthPage />
                  </ProtectedRoute>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </FilterProvider>
    </AuthProvider>
  );
};

export default App;
