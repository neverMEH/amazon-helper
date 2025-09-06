# Design Reference - Reports & Analytics UI Components

## Overview
This document contains reference React/TypeScript components for the Reports & Analytics feature UI implementation. These components demonstrate the intended user interface design and interaction patterns.

## Component Structure

### Core App Components

#### `index.tsx`
```tsx
import './index.css'
import React from "react";
import { render } from "react-dom";
import { App } from "./App";

render(<App />, document.getElementById("root"));
```

#### `App.tsx`
```tsx
import React from 'react'
import { DashboardLayout } from './components/dashboard/DashboardLayout'
import { ReportsNavigation } from './components/dashboard/ReportsNavigation'
import { ReportsList } from './components/reports/ReportsList'

export function App() {
  return (
    <div className="w-full min-h-screen bg-gray-50">
      <DashboardLayout
        navigation={<ReportsNavigation activeReport="reports" />}
        main={<ReportsList />}
      />
    </div>
  )
}
```

#### `AppRouter.tsx`
```tsx
import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { App } from "./App";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### Configuration Files

#### `tailwind.config.js`
```javascript
export default {}
```

#### `index.css`
```css
/* PLEASE NOTE: THESE TAILWIND IMPORTS SHOULD NEVER BE DELETED */
@import 'tailwindcss/base';
@import 'tailwindcss/components';
@import 'tailwindcss/utilities';
/* DO NOT DELETE THESE TAILWIND IMPORTS, OTHERWISE THE STYLING WILL NOT RENDER AT ALL */
```

### Dashboard Layout Components

#### `components/dashboard/DashboardLayout.tsx`
```tsx
import React from 'react'
import { BellIcon, SettingsIcon, UserIcon } from 'lucide-react'

interface DashboardLayoutProps {
  navigation: ReactNode
  main: ReactNode
  sidebar?: ReactNode
}

export function DashboardLayout({
  navigation,
  main,
  sidebar,
}: DashboardLayoutProps) {
  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <h1 className="text-xl font-bold text-gray-900">RecomAMP</h1>
          </div>
          <div className="flex items-center space-x-4">
            <button className="p-2 text-gray-500 hover:text-gray-700 rounded-full hover:bg-gray-100">
              <BellIcon size={20} />
            </button>
            <button className="p-2 text-gray-500 hover:text-gray-700 rounded-full hover:bg-gray-100">
              <SettingsIcon size={20} />
            </button>
            <button className="flex items-center text-sm font-medium text-gray-700 hover:text-gray-900">
              <span className="h-8 w-8 rounded-full bg-purple-600 flex items-center justify-center text-white mr-2">
                <UserIcon size={16} />
              </span>
              <span>John Doe</span>
            </button>
          </div>
        </div>
      </header>
      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Navigation sidebar */}
        <div className="w-64 bg-white border-r border-gray-200 flex-shrink-0 overflow-y-auto">
          {navigation}
        </div>
        {/* Main content area */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50">{main}</div>
        {/* Insights sidebar (optional) */}
        {sidebar && (
          <div className="w-80 bg-white border-l border-gray-200 flex-shrink-0 overflow-y-auto">
            {sidebar}
          </div>
        )}
      </div>
    </div>
  )
}
```

#### `components/dashboard/ReportsNavigation.tsx`
```tsx
import React from 'react'
import {
  BarChartIcon,
  UsersIcon,
  LineChartIcon,
  TrendingUpIcon,
  SettingsIcon,
  HistoryIcon,
  ClipboardListIcon,
} from 'lucide-react'

interface ReportsNavigationProps {
  activeReport: string
  onReportChange?: (report: string) => void
}

export function ReportsNavigation({
  activeReport,
  onReportChange,
}: ReportsNavigationProps) {
  const handleReportChange = (reportId: string) => {
    if (onReportChange) {
      onReportChange(reportId)
    }
  }

  const reports = [
    {
      id: 'reports',
      name: 'All Reports',
      icon: <ClipboardListIcon size={18} />,
    },
    {
      id: 'attribution',
      name: 'Attribution Reports',
      icon: <LineChartIcon size={18} />,
    },
    {
      id: 'audience',
      name: 'Audience Performance',
      icon: <UsersIcon size={18} />,
    },
    {
      id: 'campaign',
      name: 'Campaign Analytics',
      icon: <BarChartIcon size={18} />,
    },
    {
      id: 'brand',
      name: 'Brand Health',
      icon: <TrendingUpIcon size={18} />,
    },
  ]

  const utilities = [
    {
      id: 'history',
      name: 'Report History',
      icon: <HistoryIcon size={18} />,
    },
    {
      id: 'settings',
      name: 'Report Settings',
      icon: <SettingsIcon size={18} />,
    },
  ]

  return (
    <div className="py-6 flex flex-col h-full">
      <div className="px-6 mb-6">
        <h2 className="text-xl font-bold text-gray-900">Reports & Analytics</h2>
        <p className="text-sm text-gray-500 mt-1">AMC workflow insights</p>
      </div>
      <div className="px-3 space-y-1 mb-6">
        {reports.map((report) => (
          <button
            key={report.id}
            className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md ${
              activeReport === report.id
                ? 'bg-purple-100 text-purple-600'
                : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
            }`}
            onClick={() => handleReportChange(report.id)}
          >
            <span className="mr-3">{report.icon}</span>
            {report.name}
          </button>
        ))}
      </div>
      <div className="px-6 mb-2">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Utilities
        </h3>
      </div>
      <div className="px-3 space-y-1">
        {utilities.map((utility) => (
          <button
            key={utility.id}
            className="w-full flex items-center px-3 py-2 text-sm font-medium rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-100"
          >
            <span className="mr-3">{utility.icon}</span>
            {utility.name}
          </button>
        ))}
      </div>
      <div className="mt-auto px-6 py-4">
        <button className="w-full px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-md hover:bg-purple-700">
          Create New Report
        </button>
      </div>
    </div>
  )
}
```

### Dashboard Components

#### `components/dashboard/ReportCard.tsx`
```tsx
import React from 'react'

interface ReportCardProps {
  title: string
  children: ReactNode
  height?: 'sm' | 'md' | 'lg'
}

export function ReportCard({
  title,
  children,
  height = 'md',
}: ReportCardProps) {
  const heightClass = {
    sm: 'h-64',
    md: 'h-80',
    lg: 'h-96',
  }

  return (
    <div
      className={`bg-white border border-gray-200 rounded-lg shadow-sm ${heightClass[height]}`}
    >
      <div className="px-5 py-4 border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-700">{title}</h3>
      </div>
      <div className="p-5 h-[calc(100%-57px)]">{children}</div>
    </div>
  )
}
```

#### `components/dashboard/MetricCard.tsx`
```tsx
import React from 'react'
import { TrendingUpIcon, TrendingDownIcon } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string
  change: string
  trend: 'up' | 'down' | 'neutral'
}

export function MetricCard({ title, value, change, trend }: MetricCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
      <h3 className="text-sm font-medium text-gray-500">{title}</h3>
      <div className="mt-2 flex items-baseline">
        <p className="text-2xl font-semibold text-gray-900">{value}</p>
        <div
          className={`ml-2 flex items-center text-sm font-medium ${
            trend === 'up'
              ? 'text-green-600'
              : trend === 'down'
              ? 'text-red-600'
              : 'text-gray-500'
          }`}
        >
          {trend === 'up' ? (
            <TrendingUpIcon size={16} className="mr-1" />
          ) : trend === 'down' ? (
            <TrendingDownIcon size={16} className="mr-1" />
          ) : null}
          {change}
        </div>
      </div>
      <div className="mt-3 h-10">
        {/* Sparkline would go here */}
        <div className="h-full bg-gray-100 rounded-sm"></div>
      </div>
    </div>
  )
}
```

#### `components/dashboard/FilterControls.tsx`
```tsx
import React from 'react'
import { FilterIcon } from 'lucide-react'

interface FilterControlsProps {
  dateRange: string
  onDateRangeChange: (range: string) => void
}

export function FilterControls({
  dateRange,
  onDateRangeChange,
}: FilterControlsProps) {
  const dateRanges = [
    { id: '4w', label: 'Last 4 Weeks' },
    { id: '12w', label: 'Last 12 Weeks' },
    { id: '26w', label: 'Last 26 Weeks' },
    { id: '52w', label: 'Last 52 Weeks' },
    { id: 'ytd', label: 'Year to Date' },
    { id: 'custom', label: 'Custom Range' },
  ]

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between">
      <div className="flex space-x-4">
        <div>
          <label
            htmlFor="date-range"
            className="block text-xs font-medium text-gray-700 mb-1"
          >
            Date Range
          </label>
          <select
            id="date-range"
            value={dateRange}
            onChange={(e) => onDateRangeChange(e.target.value)}
            className="block w-40 pl-3 pr-10 py-2 text-sm border-gray-300 focus:outline-none focus:ring-purple-500 focus:border-purple-500 rounded-md"
          >
            {dateRanges.map((range) => (
              <option key={range.id} value={range.id}>
                {range.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label
            htmlFor="brand-filter"
            className="block text-xs font-medium text-gray-700 mb-1"
          >
            Brand
          </label>
          <select
            id="brand-filter"
            defaultValue="all"
            className="block w-40 pl-3 pr-10 py-2 text-sm border-gray-300 focus:outline-none focus:ring-purple-500 focus:border-purple-500 rounded-md"
          >
            <option value="all">All Brands</option>
            <option value="brand1">Brand 1</option>
            <option value="brand2">Brand 2</option>
            <option value="brand3">Brand 3</option>
          </select>
        </div>
        <div>
          <label
            htmlFor="campaign-filter"
            className="block text-xs font-medium text-gray-700 mb-1"
          >
            Campaign
          </label>
          <select
            id="campaign-filter"
            defaultValue="all"
            className="block w-40 pl-3 pr-10 py-2 text-sm border-gray-300 focus:outline-none focus:ring-purple-500 focus:border-purple-500 rounded-md"
          >
            <option value="all">All Campaigns</option>
            <option value="campaign1">Q2 Promotion</option>
            <option value="campaign2">Summer Sale</option>
            <option value="campaign3">New Product Launch</option>
          </select>
        </div>
      </div>
      <button className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
        <FilterIcon size={16} className="mr-2" />
        More Filters
      </button>
    </div>
  )
}
```

### Chart Components

#### `components/dashboard/TrendChart.tsx`
```tsx
import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface TrendChartProps {
  reportType: string
}

export function TrendChart({ reportType }: TrendChartProps) {
  // This would come from your API in a real application
  const generateData = () => {
    const data = []
    for (let i = 0; i < 52; i++) {
      const week = `W${i + 1}`
      if (reportType === 'attribution') {
        data.push({
          week,
          conversions: Math.floor(Math.random() * 1000) + 500,
          revenue: Math.floor(Math.random() * 50000) + 20000,
          roas: (Math.random() * 2 + 2).toFixed(1),
        })
      } else if (reportType === 'audience') {
        data.push({
          week,
          reach: Math.floor(Math.random() * 100000) + 50000,
          engagement: (Math.random() * 2 + 2).toFixed(1),
          conversion: (Math.random() * 1 + 0.5).toFixed(1),
        })
      } else if (reportType === 'campaign') {
        data.push({
          week,
          impressions: Math.floor(Math.random() * 200000) + 100000,
          clicks: Math.floor(Math.random() * 10000) + 5000,
          ctr: (Math.random() * 2 + 1).toFixed(1),
        })
      } else if (reportType === 'brand') {
        data.push({
          week,
          newToBrand: (Math.random() * 10 + 25).toFixed(1),
          repeatPurchase: (Math.random() * 10 + 35).toFixed(1),
          marketShare: (Math.random() * 5 + 15).toFixed(1),
        })
      }
    }
    return data
  }

  const data = generateData()

  // Define chart configuration based on report type
  const getChartConfig = () => {
    if (reportType === 'attribution') {
      return {
        lines: [
          { dataKey: 'conversions', stroke: '#8884d8', name: 'Conversions' },
          { dataKey: 'revenue', stroke: '#82ca9d', name: 'Revenue ($)' },
          { dataKey: 'roas', stroke: '#ffc658', name: 'ROAS' },
        ],
      }
    } else if (reportType === 'audience') {
      return {
        lines: [
          { dataKey: 'reach', stroke: '#8884d8', name: 'Reach' },
          { dataKey: 'engagement', stroke: '#82ca9d', name: 'Engagement (%)' },
          { dataKey: 'conversion', stroke: '#ffc658', name: 'Conversion (%)' },
        ],
      }
    } else if (reportType === 'campaign') {
      return {
        lines: [
          { dataKey: 'impressions', stroke: '#8884d8', name: 'Impressions' },
          { dataKey: 'clicks', stroke: '#82ca9d', name: 'Clicks' },
          { dataKey: 'ctr', stroke: '#ffc658', name: 'CTR (%)' },
        ],
      }
    } else if (reportType === 'brand') {
      return {
        lines: [
          { dataKey: 'newToBrand', stroke: '#8884d8', name: 'New-to-Brand (%)' },
          { dataKey: 'repeatPurchase', stroke: '#82ca9d', name: 'Repeat Purchase (%)' },
          { dataKey: 'marketShare', stroke: '#ffc658', name: 'Market Share (%)' },
        ],
      }
    }
    return { lines: [] }
  }

  const config = getChartConfig()

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart
        data={data}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="week" />
        <YAxis />
        <Tooltip />
        <Legend />
        {config.lines.map((line, index) => (
          <Line
            key={index}
            type="monotone"
            dataKey={line.dataKey}
            stroke={line.stroke}
            name={line.name}
            activeDot={{ r: 8 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
```

#### `components/dashboard/ComparisonChart.tsx`
```tsx
import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface ComparisonChartProps {
  reportType: string
}

export function ComparisonChart({ reportType }: ComparisonChartProps) {
  // This would come from your API in a real application
  const generateData = () => {
    const metrics = {
      attribution: ['Conversions', 'Revenue', 'ROAS', 'CPA'],
      audience: ['Reach', 'Engagement', 'Conversion', 'Growth'],
      campaign: ['Impressions', 'Clicks', 'CTR', 'ACOS'],
      brand: ['New-to-Brand', 'Repeat Purchase', 'Market Share', 'Brand Searches'],
    }

    const activeMetrics = metrics[reportType as keyof typeof metrics] || []

    return activeMetrics.map((metric) => ({
      name: metric,
      thisWeek: Math.floor(Math.random() * 100) + 50,
      lastWeek: Math.floor(Math.random() * 100) + 50,
    }))
  }

  const data = generateData()

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="thisWeek" name="This Week" fill="#8884d8" />
        <Bar dataKey="lastWeek" name="Last Week" fill="#82ca9d" />
      </BarChart>
    </ResponsiveContainer>
  )
}
```

### AI Insights Component

#### `components/dashboard/InsightsPanel.tsx`
```tsx
import React from 'react'
import {
  TrendingUpIcon,
  AlertCircleIcon,
  BrainIcon,
  ZapIcon,
} from 'lucide-react'

interface InsightsPanelProps {
  reportType: string
}

export function InsightsPanel({ reportType }: InsightsPanelProps) {
  // This would come from your AI analysis in a real application
  const insights = {
    attribution: [
      {
        type: 'trend',
        title: 'Conversion Trend',
        message:
          'Conversions have increased by 12.3% over the past 4 weeks, primarily driven by improved performance in sponsored product campaigns.',
      },
      {
        type: 'anomaly',
        title: 'Revenue Spike',
        message:
          'Unusual revenue spike detected in week 32. This coincides with your Prime Day promotions and resulted in 28% higher conversions than forecasted.',
      },
      {
        type: 'forecast',
        title: 'ROAS Forecast',
        message:
          'Based on current trends, ROAS is projected to increase by 0.4 points over the next 4 weeks if current campaign settings are maintained.',
      },
      {
        type: 'action',
        title: 'Recommended Action',
        message:
          'Consider increasing budget allocation to your top-performing sponsored brand campaigns to capitalize on their strong ROAS of 4.2x.',
      },
    ],
    // ... other report types
  }

  const activeInsights = insights[reportType as keyof typeof insights] || []

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'trend':
        return <TrendingUpIcon size={18} className="text-blue-500" />
      case 'anomaly':
        return <AlertCircleIcon size={18} className="text-amber-500" />
      case 'forecast':
        return <BrainIcon size={18} className="text-purple-500" />
      case 'action':
        return <ZapIcon size={18} className="text-green-500" />
      default:
        return null
    }
  }

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="flex items-center mb-6">
        <BrainIcon size={24} className="text-purple-600 mr-3" />
        <h2 className="text-lg font-semibold text-gray-900">AI Insights</h2>
      </div>
      <div className="space-y-6">
        {activeInsights.map((insight, index) => (
          <div
            key={index}
            className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"
          >
            <div className="flex items-center mb-2">
              {getInsightIcon(insight.type)}
              <h3 className="ml-2 text-sm font-medium text-gray-900">
                {insight.title}
              </h3>
            </div>
            <p className="text-sm text-gray-600">{insight.message}</p>
          </div>
        ))}
      </div>
      <div className="mt-6">
        <div className="relative">
          <input
            type="text"
            placeholder="Ask a question about your data..."
            className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
          />
          <button className="absolute right-3 top-2 text-gray-400 hover:text-gray-600">
            <BrainIcon size={18} />
          </button>
        </div>
        <div className="mt-2 text-xs text-gray-500">
          Try: "What drove the conversion spike in week 32?" or "How does this
          quarter compare to last year?"
        </div>
      </div>
    </div>
  )
}
```

### Reports List Components

#### `components/reports/ReportsList.tsx`
```tsx
import React, { useState } from 'react'
import { ReportsHeader } from './ReportsHeader'
import { ReportsFilters } from './ReportsFilters'
import { ReportsTable } from './ReportsTable'

export function ReportsList() {
  const [searchQuery, setSearchQuery] = useState('')
  const [brandFilter, setBrandFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')

  // Mock data for the reports table
  const reports = [
    {
      id: '1',
      reportName: 'Q2 Attribution Analysis',
      brandName: 'Amazon Basics',
      instanceName: 'US-West',
      reportType: 'attribution',
      status: 'active',
      lastRun: '2023-06-15T14:30:00Z',
      createdBy: 'john.doe@example.com',
    },
    // ... more reports
  ]

  // Filter the reports based on the search query and filters
  const filteredReports = reports.filter((report) => {
    const matchesSearch =
      searchQuery === '' ||
      report.reportName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      report.brandName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      report.instanceName.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesBrand =
      brandFilter === 'all' || report.brandName === brandFilter
    const matchesStatus =
      statusFilter === 'all' || report.status === statusFilter
    const matchesType = typeFilter === 'all' || report.reportType === typeFilter

    return matchesSearch && matchesBrand && matchesStatus && matchesType
  })

  // Get unique brand names for the filter
  const brands = Array.from(new Set(reports.map((report) => report.brandName)))

  return (
    <div className="space-y-6">
      <ReportsHeader />
      <ReportsFilters
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        brandFilter={brandFilter}
        onBrandFilterChange={setBrandFilter}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        typeFilter={typeFilter}
        onTypeFilterChange={setTypeFilter}
        brands={brands}
      />
      <ReportsTable reports={filteredReports} />
    </div>
  )
}
```

#### `components/reports/ReportsTable.tsx`
```tsx
import React from 'react'
import {
  EyeIcon,
  EditIcon,
  TrashIcon,
  MoreVerticalIcon,
  CheckCircleIcon,
  XCircleIcon,
  BarChartIcon,
  UsersIcon,
  LineChartIcon,
  TrendingUpIcon,
} from 'lucide-react'

interface Report {
  id: string
  reportName: string
  brandName: string
  instanceName: string
  reportType: string
  status: string
  lastRun: string
  createdBy: string
}

interface ReportsTableProps {
  reports: Report[]
}

export function ReportsTable({ reports }: ReportsTableProps) {
  // Format the date to a more readable format
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    }).format(date)
  }

  // Get the appropriate icon for the report type
  const getReportTypeIcon = (type: string) => {
    switch (type) {
      case 'attribution':
        return <LineChartIcon size={16} className="text-purple-600" />
      case 'audience':
        return <UsersIcon size={16} className="text-blue-600" />
      case 'campaign':
        return <BarChartIcon size={16} className="text-green-600" />
      case 'brand':
        return <TrendingUpIcon size={16} className="text-amber-600" />
      default:
        return null
    }
  }

  // Get the formatted report type name
  const getReportTypeName = (type: string) => {
    switch (type) {
      case 'attribution':
        return 'Attribution'
      case 'audience':
        return 'Audience'
      case 'campaign':
        return 'Campaign'
      case 'brand':
        return 'Brand Health'
      default:
        return type
    }
  }

  return (
    <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
      {reports.length === 0 ? (
        <div className="p-6 text-center">
          <p className="text-gray-500">
            No reports found. Try adjusting your filters.
          </p>
        </div>
      ) : (
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Report Name
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Brand
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Instance
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Run
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {reports.map((report) => (
              <tr key={report.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {report.reportName}
                  </div>
                  <div className="text-xs text-gray-500">
                    {report.createdBy}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {report.brandName}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {report.instanceName}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {getReportTypeIcon(report.reportType)}
                    <span className="ml-2 text-sm text-gray-900">
                      {getReportTypeName(report.reportType)}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      report.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {report.status === 'active' ? (
                      <CheckCircleIcon size={12} className="mr-1.5" />
                    ) : (
                      <XCircleIcon size={12} className="mr-1.5" />
                    )}
                    {report.status === 'active' ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {formatDate(report.lastRun)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex items-center justify-end space-x-2">
                    <button className="text-indigo-600 hover:text-indigo-900 p-1 rounded-full hover:bg-indigo-50">
                      <EyeIcon size={18} />
                    </button>
                    <button className="text-blue-600 hover:text-blue-900 p-1 rounded-full hover:bg-blue-50">
                      <EditIcon size={18} />
                    </button>
                    <button className="text-red-600 hover:text-red-900 p-1 rounded-full hover:bg-red-50">
                      <TrashIcon size={18} />
                    </button>
                    <button className="text-gray-500 hover:text-gray-700 p-1 rounded-full hover:bg-gray-100">
                      <MoreVerticalIcon size={18} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div className="bg-gray-50 px-6 py-3 border-t border-gray-200 flex items-center justify-between">
        <div className="text-sm text-gray-500">
          Showing {reports.length} reports
        </div>
        <div className="flex items-center space-x-2">
          <button
            className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            disabled
          >
            Previous
          </button>
          <span className="text-sm text-gray-700">Page 1</span>
          <button className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50">
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
```

## Key Design Features

### Layout Structure
- **Three-panel layout**: Navigation sidebar, main content area, optional AI insights sidebar
- **Responsive design**: Mobile-friendly with Tailwind CSS
- **Consistent spacing**: Using Tailwind's spacing scale

### Visual Design
- **Color scheme**: Purple primary (#8B5CF6), gray neutrals
- **Card-based layouts**: White cards on gray-50 background
- **Subtle shadows**: Using `shadow-sm` for depth
- **Rounded corners**: `rounded-lg` for modern feel

### Interactive Elements
- **Hover states**: All interactive elements have hover feedback
- **Active states**: Clear indication of selected navigation items
- **Loading states**: Placeholder content for async data
- **Tooltips**: Using Recharts built-in tooltips for charts

### Data Visualization
- **52-week trends**: Line charts for historical analysis
- **Week-over-week comparisons**: Bar charts for period comparisons
- **KPI cards**: Metric cards with sparklines
- **Performance heatmaps**: Visual matrices for pattern recognition

### AI Integration
- **Conversational interface**: Natural language input field
- **Insight cards**: Categorized AI insights with icons
- **Proactive suggestions**: Context-aware recommendations
- **Query examples**: Helper text for user guidance

## Implementation Notes

1. **Component Architecture**: All components are functional React components with TypeScript
2. **State Management**: Using React hooks (useState) for local state
3. **Chart Library**: Recharts for data visualization (consistent with existing codebase)
4. **Icons**: Lucide React for consistent iconography
5. **Styling**: Tailwind CSS for utility-first styling approach
6. **Data Flow**: Props-based communication between components
7. **Type Safety**: TypeScript interfaces for all component props
8. **Mock Data**: Includes realistic mock data generators for development

## Integration Points

These components are designed to integrate with:
- Existing authentication system (user context)
- Current API endpoints (extend with new /reports endpoints)
- Existing workflow system (workflows table)
- Current AMC instance management (instances table)
- Existing brand management (instance_brands table)

## Next Steps

To implement these designs:
1. Set up the routing structure in the existing React app
2. Create the new database tables for reports configuration
3. Implement the backend API endpoints
4. Build the components progressively, starting with the list view
5. Add the dashboard visualization components
6. Integrate with real data from the backend
7. Add the AI insights functionality
8. Implement export and sharing features