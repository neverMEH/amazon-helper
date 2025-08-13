import { useMemo } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { getBreadcrumbConfig } from '../../utils/breadcrumbConfig';

interface DynamicBreadcrumbData {
  instanceName?: string;
  workflowName?: string;
  templateName?: string;
}

export default function Breadcrumb() {
  const location = useLocation();
  const params = useParams();

  // Fetch dynamic data for breadcrumbs
  const { data: instanceData } = useQuery({
    queryKey: ['instance-breadcrumb', params.instanceId],
    queryFn: async () => {
      if (!params.instanceId) return null;
      const response = await api.get(`/instances/${params.instanceId}`);
      return response.data;
    },
    enabled: !!params.instanceId,
    staleTime: 5 * 60 * 1000,
  });

  const { data: workflowData } = useQuery({
    queryKey: ['workflow-breadcrumb', params.workflowId],
    queryFn: async () => {
      if (!params.workflowId) return null;
      const response = await api.get(`/workflows/${params.workflowId}`);
      return response.data;
    },
    enabled: !!params.workflowId,
    staleTime: 5 * 60 * 1000,
  });

  const { data: templateData } = useQuery({
    queryKey: ['template-breadcrumb', params.templateId],
    queryFn: async () => {
      if (!params.templateId) return null;
      const response = await api.get(`/query-templates/${params.templateId}`);
      return response.data;
    },
    enabled: !!params.templateId,
    staleTime: 5 * 60 * 1000,
  });

  const breadcrumbs = useMemo(() => {
    const dynamicData: DynamicBreadcrumbData = {
      instanceName: instanceData?.instanceName || instanceData?.name,
      workflowName: workflowData?.name,
      templateName: templateData?.name,
    };

    return getBreadcrumbConfig(location.pathname, params, dynamicData);
  }, [location.pathname, params, instanceData, workflowData, templateData]);

  // Don't show breadcrumbs on login or auth pages
  if (location.pathname.includes('/login') || location.pathname.includes('/auth')) {
    return null;
  }

  // Don't show if only one item (home/dashboard)
  if (breadcrumbs.length <= 1) {
    return null;
  }

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-3">
      <nav className="flex" aria-label="Breadcrumb">
        <ol className="flex items-center space-x-2">
          {breadcrumbs.map((item, index) => {
            const isLast = index === breadcrumbs.length - 1;
            const isFirst = index === 0;

            return (
              <li key={item.path || index} className="flex items-center">
                {!isFirst && (
                  <ChevronRight className="flex-shrink-0 h-4 w-4 text-gray-400 mx-2" />
                )}
                
                {isLast ? (
                  <span className="text-sm font-medium text-gray-900">
                    {item.label}
                  </span>
                ) : (
                  <Link
                    to={item.path}
                    className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    {isFirst && (
                      <span className="flex items-center">
                        <Home className="flex-shrink-0 h-4 w-4 mr-1" />
                        {item.label}
                      </span>
                    )}
                    {!isFirst && item.label}
                  </Link>
                )}
              </li>
            );
          })}
        </ol>
      </nav>
    </div>
  );
}