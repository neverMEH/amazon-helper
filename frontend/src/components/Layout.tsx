import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Database, Tag, BookOpen, FileText, LogOut, User } from 'lucide-react';
import { authService } from '../services/auth';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'AMC Instances', href: '/instances', icon: Database },
  { name: 'Campaigns', href: '/campaigns', icon: Tag },
  { name: 'Query Library', href: '/query-library', icon: BookOpen },
  { name: 'My Queries', href: '/my-queries', icon: FileText },
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
        <div className="flex h-16 items-center px-6">
          <h1 className="text-xl font-semibold text-white">AMC Manager</h1>
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
        <main className="min-h-screen">
          <Outlet />
        </main>
      </div>
    </div>
  );
}