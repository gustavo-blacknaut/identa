import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import { Navbar } from "./components/Navbar";
import { ToastProvider } from "./components/Toast";
import { DashboardPage } from "./pages/DashboardPage";
import { DocumentPage } from "./pages/DocumentPage";
import { LoginPage } from "./pages/LoginPage";
import { PeoplePage } from "./pages/PeoplePage";
import { UploadPage } from "./pages/UploadPage";
import "./styles.css";

function App() {
  const { user, loading } = useAuth();
  if (loading) return <div className="spinner page-spinner" />;
  if (!user) return <LoginPage />;
  return (
    <>
      <Navbar />
      <main className="container">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/enviar" element={<UploadPage />} />
          <Route path="/documentos/:id" element={<DocumentPage />} />
          <Route path="/pessoas" element={<PeoplePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <App />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
