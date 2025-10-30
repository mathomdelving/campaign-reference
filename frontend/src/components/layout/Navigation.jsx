import { Link, useLocation } from 'react-router-dom';
import { AuthButton } from '../auth/AuthButton';

export function Navigation() {
  const location = useLocation();

  const navItems = [
    { path: '/leaderboard', label: 'Leaderboard', icon: 'trophy' },
    { path: '/district', label: 'By District', icon: 'map' },
    { path: '/candidate', label: 'By Candidate', icon: 'user' },
  ];

  const isActive = (path) => location.pathname === path || (path === '/leaderboard' && location.pathname === '/');

  const getIcon = (iconName) => {
    const icons = {
      trophy: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />,
      map: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />,
      user: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />,
      chart: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />,
    };
    return icons[iconName];
  };

  return (
    <nav className="bg-rb-navy border-b border-rb-blue">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Title */}
          <Link to="/" className="flex items-center gap-2">
            <div className="text-2xl font-bold text-rb-yellow">
              Campaign Reference
            </div>
          </Link>

          {/* Navigation Links and Auth */}
          <div className="flex items-center gap-4">
            {/* Navigation Links */}
            <div className="flex items-center gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`
                    px-4 py-2 rounded-md text-sm font-medium transition-colors
                    flex items-center gap-2
                    ${isActive(item.path)
                      ? 'bg-rb-red text-white'
                      : 'text-gray-300 hover:bg-rb-blue hover:text-white'
                    }
                  `}
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {getIcon(item.icon)}
                  </svg>
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              ))}
            </div>

            {/* Auth Button */}
            <AuthButton />
          </div>
        </div>
      </div>
    </nav>
  );
}
