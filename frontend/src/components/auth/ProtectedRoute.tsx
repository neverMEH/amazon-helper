import { Navigate, Outlet } from 'react-router-dom';
import { authService } from '../../services/auth';

export default function ProtectedRoute() {
  const isAuthenticated = authService.isAuthenticated();

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}