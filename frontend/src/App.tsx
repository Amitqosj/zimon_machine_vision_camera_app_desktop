import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth } from './components/RequireAuth'
import { AuthProvider } from './context/AuthContext'
import { DashboardLayoutProvider } from './context/DashboardLayoutContext'
import { HardwareStatusProvider } from './context/HardwareStatusContext'
import { ZimonWorkspaceProvider } from './context/ZimonWorkspaceContext'
import { AppLayout } from './layouts/AppLayout'
import { AccountPage } from './pages/AccountPage'
import { AdultPage } from './pages/AdultPage'
import { DashboardPage } from './pages/DashboardPage'
import { EnvironmentPage } from './pages/EnvironmentPage'
import { ExperimentsModulePage } from './pages/ExperimentsModulePage'
import { LarvalPage } from './pages/LarvalPage'
import { ProtocolBuilderPage } from './pages/ProtocolBuilderPage'
import { ForgotPasswordPage } from './pages/ForgotPasswordPage'
import { LoginPage } from './pages/LoginPage'
import { SettingsPage } from './pages/SettingsPage'
import { SplashPage } from './pages/SplashPage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<SplashPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route element={<RequireAuth />}>
            <Route
              path="/app"
              element={
                <DashboardLayoutProvider>
                  <ZimonWorkspaceProvider>
                    <HardwareStatusProvider>
                      <AppLayout />
                    </HardwareStatusProvider>
                  </ZimonWorkspaceProvider>
                </DashboardLayoutProvider>
              }
            >
              <Route index element={<Navigate to="adult" replace />} />
              <Route path="adult" element={<AdultPage />} />
              <Route path="larval" element={<LarvalPage />} />
              <Route path="environment" element={<EnvironmentPage />} />
              <Route path="protocol-builder" element={<ProtocolBuilderPage />} />
              <Route path="experiments" element={<ExperimentsModulePage />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="experiment" element={<Navigate to="../experiments" replace />} />
              <Route path="presets" element={<Navigate to="/app/adult" replace />} />
              <Route path="analysis" element={<Navigate to="/app/adult" replace />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="account" element={<AccountPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
