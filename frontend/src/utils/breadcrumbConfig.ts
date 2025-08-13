export interface BreadcrumbItem {
  label: string;
  path: string;
}

interface DynamicData {
  instanceName?: string;
  workflowName?: string;
  templateName?: string;
}

export function getBreadcrumbConfig(
  pathname: string, 
  params: Record<string, string | undefined>,
  dynamicData: DynamicData
): BreadcrumbItem[] {
  const breadcrumbs: BreadcrumbItem[] = [];
  
  // Always start with Dashboard as home
  breadcrumbs.push({
    label: 'Dashboard',
    path: '/dashboard'
  });

  // Parse the pathname
  const segments = pathname.split('/').filter(Boolean);
  
  // Build breadcrumbs based on route segments
  for (let i = 0; i < segments.length; i++) {
    const segment = segments[i];
    const nextSegment = segments[i + 1];
    
    // Skip certain segments that are already handled
    if (segment === 'dashboard') continue;
    
    // Build the path up to this point
    const currentPath = '/' + segments.slice(0, i + 1).join('/');
    
    switch (segment) {
      case 'instances':
        breadcrumbs.push({
          label: 'AMC Instances',
          path: '/instances'
        });
        
        // Handle instance detail pages
        if (nextSegment && nextSegment !== 'new') {
          const instanceName = dynamicData.instanceName || 'Loading...';
          breadcrumbs.push({
            label: instanceName,
            path: `/instances/${nextSegment}`
          });
          i++; // Skip the next segment since we handled it
        }
        break;
        
      case 'campaigns':
        breadcrumbs.push({
          label: 'Campaigns',
          path: '/campaigns'
        });
        break;
        
      case 'executions':
        breadcrumbs.push({
          label: 'Executions',
          path: '/executions'
        });
        
        if (nextSegment) {
          breadcrumbs.push({
            label: `Execution ${nextSegment.substring(0, 8)}...`,
            path: currentPath
          });
          i++;
        }
        break;
        
      case 'query-library':
        breadcrumbs.push({
          label: 'Query Library',
          path: '/query-library'
        });
        break;
        
      case 'my-queries':
        breadcrumbs.push({
          label: 'Workflows',
          path: '/my-queries'
        });
        break;
        
      case 'workflows':
        breadcrumbs.push({
          label: 'Workflows',
          path: '/my-queries'
        });
        
        // Handle workflow detail/edit pages
        if (nextSegment && nextSegment !== 'new') {
          const workflowName = dynamicData.workflowName || 'Loading...';
          breadcrumbs.push({
            label: workflowName,
            path: `/workflows/${nextSegment}`
          });
          i++;
          
          // Check for edit mode
          if (segments[i + 1] === 'edit') {
            breadcrumbs.push({
              label: 'Edit',
              path: `/workflows/${nextSegment}/edit`
            });
            i++;
          }
        }
        break;
        
      case 'query-builder':
        // Don't add query-builder itself as a breadcrumb
        if (nextSegment === 'new') {
          breadcrumbs.push({
            label: 'New Query',
            path: '/query-builder/new'
          });
          i++;
        } else if (nextSegment === 'edit' && segments[i + 2]) {
          const workflowName = dynamicData.workflowName || 'Loading...';
          breadcrumbs.push({
            label: 'Workflows',
            path: '/my-queries'
          });
          breadcrumbs.push({
            label: workflowName,
            path: `/workflows/${segments[i + 2]}`
          });
          breadcrumbs.push({
            label: 'Edit',
            path: currentPath
          });
          i += 2;
        } else if (nextSegment === 'copy' && segments[i + 2]) {
          const workflowName = dynamicData.workflowName || 'Loading...';
          breadcrumbs.push({
            label: 'Workflows',
            path: '/my-queries'
          });
          breadcrumbs.push({
            label: `Copy of ${workflowName}`,
            path: currentPath
          });
          i += 2;
        } else if (nextSegment === 'template' && segments[i + 2]) {
          const templateName = dynamicData.templateName || 'Loading...';
          breadcrumbs.push({
            label: 'Query Library',
            path: '/query-library'
          });
          breadcrumbs.push({
            label: `New from ${templateName}`,
            path: currentPath
          });
          i += 2;
        }
        break;
        
      case 'query-templates':
        breadcrumbs.push({
          label: 'Query Templates',
          path: '/query-templates'
        });
        break;
        
      case 'profile':
        breadcrumbs.push({
          label: 'Profile',
          path: '/profile'
        });
        break;
        
      default:
        // Handle any other segments generically
        if (!['new', 'edit', 'copy', 'template'].includes(segment)) {
          // Capitalize first letter and replace hyphens with spaces
          const label = segment
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
          
          breadcrumbs.push({
            label,
            path: currentPath
          });
        }
    }
  }
  
  return breadcrumbs;
}