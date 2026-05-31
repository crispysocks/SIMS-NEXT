import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { MainLayout } from '@/components/Layout/MainLayout';
import { LoginPage } from '@/pages/Login';
import { StudentsPage } from '@/pages/Students';
import { TeachersPage } from '@/pages/Teachers';
import { ClassesPage } from '@/pages/Classes';
import { ScoresPage } from '@/pages/Scores';
import { ChatPage } from '@/pages/Chat';
import { PredictionPage } from '@/pages/Prediction';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/students" replace />} />
          <Route path="students" element={<StudentsPage />} />
          <Route path="teachers" element={<TeachersPage />} />
          <Route path="classes" element={<ClassesPage />} />
          <Route path="scores" element={<ScoresPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="prediction" element={<PredictionPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;