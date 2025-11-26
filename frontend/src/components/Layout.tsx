import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Database, Tag, BookOpen, LogOut, User, History, Book, CalendarClock, GraduationCap, Package, Calendar, BarChart3 } from 'lucide-react';
import { authService } from '../services/auth';
import AuthStatusBanner from './common/AuthStatusBanner';
import Breadcrumb from './common/Breadcrumb';
import AppLogo from './common/AppLogo';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'AMC Instances', href: '/instances', icon: Database },
  { name: 'Schedules', href: '/schedules', icon: CalendarClock },
  { name: 'Executions', href: '/executions', icon: History },
  // Hidden pages - still accessible via direct URL:
  // { name: 'Campaigns', href: '/campaigns', icon: Tag },
  // { name: 'ASINs', href: '/asins', icon: Package },
  // { name: 'Data Sources', href: '/data-sources', icon: Book },
  // { name: 'Build Guides', href: '/build-guides', icon: GraduationCap },
  // { name: 'Query Library', href: '/query-library', icon: BookOpen },
  // { name: 'Data Collections', href: '/data-collections', icon: Calendar },
  // { name: 'Report Builder', href: '/report-builder', icon: BarChart3 },
];

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const user = authService.getStoredUser();

  const handleLogout = async () => {
    await authService.logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-gray-900">
        <div className="flex h-16 items-center px-6 gap-3">
          <AppLogo variant="icon" height={32} />
          <AppLogo variant="wordmark" height={20} />
        </div>

        <nav className="mt-6 px-3">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`
                  mb-1 flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors
                  ${isActive
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }
                `}
              >
                <item.icon className="mr-3 h-5 w-5" />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* User section at bottom */}
        <div className="absolute bottom-0 left-0 right-0 p-3">
          <div className="rounded-lg bg-gray-800 px-3 py-2">
            <div className="flex items-center justify-between">
              <Link 
                to="/profile" 
                className="flex items-center hover:bg-gray-700 rounded px-2 py-1 transition-colors"
              >
                <User className="h-5 w-5 text-gray-400" />
                <span className="ml-2 text-sm text-gray-300">
                  {user?.email || 'User'}
                </span>
              </Link>
              <button
                onClick={handleLogout}
                className="text-gray-400 hover:text-white"
                title="Logout"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="pl-64">
        {/* Auth Status Banner - appears at the very top when auth is disconnected */}
        <AuthStatusBanner />
        
        {/* Breadcrumb Navigation */}
        <Breadcrumb />
        
        <main className="min-h-screen">
          <Outlet />
        </main>
      </div>
    </div>
  );
}