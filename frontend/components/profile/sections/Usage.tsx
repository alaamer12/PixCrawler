'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Activity,
  Database,
  Download,
  Upload,
  Image,
  FileText,
  Clock,
  Calendar,
  AlertCircle,
  Info,
  Zap,
  HardDrive,
  Cpu,
  Network,
  Users,
  Package,
  ArrowUp,
  ArrowDown,
  Minus,
  ChevronRight,
  ExternalLink,
} from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface UsageMetric {
  name: string
  current: number
  limit: number
  unit: string
  trend: 'up' | 'down' | 'stable'
  trendValue: number
}

interface UsageData {
  date: string
  images: number
  storage: number
  bandwidth: number
  apiCalls: number
}

export function Usage() {
  const [timeRange, setTimeRange] = useState('30d')
  const [selectedMetric, setSelectedMetric] = useState('all')

  const metrics: UsageMetric[] = [
    {
      name: 'Images Processed',
      current: 7523,
      limit: 10000,
      unit: 'images',
      trend: 'up',
      trendValue: 12.5,
    },
    {
      name: 'Storage Used',
      current: 42.7,
      limit: 100,
      unit: 'GB',
      trend: 'up',
      trendValue: 8.3,
    },
    {
      name: 'API Calls',
      current: 15234,
      limit: 50000,
      unit: 'calls',
      trend: 'down',
      trendValue: -5.2,
    },
    {
      name: 'Bandwidth',
      current: 127.3,
      limit: 500,
      unit: 'GB',
      trend: 'stable',
      trendValue: 0.8,
    },
    {
      name: 'Crawl Jobs',
      current: 89,
      limit: 200,
      unit: 'jobs',
      trend: 'up',
      trendValue: 15.7,
    },
    {
      name: 'Datasets Created',
      current: 23,
      limit: 50,
      unit: 'datasets',
      trend: 'up',
      trendValue: 21.3,
    },
  ]

  const dailyUsage: UsageData[] = Array.from({ length: 30 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - (29 - i))
    return {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      images: Math.floor(Math.random() * 500) + 100,
      storage: Math.floor(Math.random() * 5) + 1,
      bandwidth: Math.floor(Math.random() * 10) + 2,
      apiCalls: Math.floor(Math.random() * 2000) + 300,
    }
  })

  const categoryUsage = [
    { name: 'Images', value: 45, color: '#3b82f6' },
    { name: 'Storage', value: 25, color: '#10b981' },
    { name: 'API', value: 20, color: '#f59e0b' },
    { name: 'Other', value: 10, color: '#6b7280' },
  ]

  const topProjects = [
    { name: 'Cat Breeds Dataset', usage: 2341, percentage: 31 },
    { name: 'Product Images', usage: 1823, percentage: 24 },
    { name: 'Nature Landscapes', usage: 1456, percentage: 19 },
    { name: 'Vehicle Detection', usage: 987, percentage: 13 },
    { name: 'Food Classification', usage: 916, percentage: 12 },
  ]

  const getUsageColor = (percentage: number) => {
    if (percentage < 50) return 'text-green-600 dark:text-green-400'
    if (percentage < 80) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getProgressColor = (percentage: number) => {
    if (percentage < 50) return 'bg-green-600'
    if (percentage < 80) return 'bg-yellow-600'
    return 'bg-red-600'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Usage</h1>
          <p className="text-muted-foreground">
            Monitor your resource consumption and limits
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
              <SelectItem value="12m">Last 12 months</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {metrics.map((metric) => {
          const percentage = (metric.current / metric.limit) * 100
          const TrendIcon = metric.trend === 'up' ? ArrowUp : metric.trend === 'down' ? ArrowDown : Minus
          
          return (
            <Card key={metric.name}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {metric.name}
                  </CardTitle>
                  <Badge
                    variant="outline"
                    className={cn(
                      "px-2.5 py-1",
                      metric.trend === 'up' && 'text-green-600 dark:text-green-400',
                      metric.trend === 'down' && 'text-red-600 dark:text-red-400',
                      metric.trend === 'stable' && 'text-gray-600 dark:text-gray-400'
                    )}
                  >
                    <TrendIcon className="h-3 w-3 mr-1" />
                    {Math.abs(metric.trendValue) >= 100 
                      ? Math.abs(metric.trendValue).toFixed(0)
                      : Math.abs(metric.trendValue) >= 10
                      ? Math.abs(metric.trendValue).toFixed(1)
                      : Math.abs(metric.trendValue).toFixed(2)
                    }%
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-baseline justify-between">
                    <span className="text-2xl font-bold">
                      {metric.current.toLocaleString()}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      / {metric.limit.toLocaleString()} {metric.unit}
                    </span>
                  </div>
                  <Progress 
                    value={percentage} 
                    className="h-2"
                    indicatorClassName={getProgressColor(percentage)}
                  />
                  <p className={cn("text-xs", getUsageColor(percentage))}>
                    {percentage.toFixed(1)}% used
                  </p>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Usage Charts */}
      <Tabs defaultValue="timeline" className="space-y-4">
        <TabsList>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="breakdown">Breakdown</TabsTrigger>
          <TabsTrigger value="projects">By Project</TabsTrigger>
        </TabsList>

        <TabsContent value="timeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Usage Over Time</CardTitle>
              <CardDescription>
                Track your resource consumption trends
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={dailyUsage}>
                  <defs>
                    <linearGradient id="colorImages" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="date" className="text-xs" />
                  <YAxis className="text-xs" />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="images"
                    stroke="#3b82f6"
                    fillOpacity={1}
                    fill="url(#colorImages)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Storage Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={dailyUsage}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="date" className="text-xs" />
                    <YAxis className="text-xs" />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="storage"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">API Calls</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={dailyUsage.slice(-7)}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="date" className="text-xs" />
                    <YAxis className="text-xs" />
                    <Tooltip />
                    <Bar dataKey="apiCalls" fill="#f59e0b" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="breakdown" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Resource Distribution</CardTitle>
                <CardDescription>
                  How your usage is distributed across categories
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={categoryUsage}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent as number * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {categoryUsage.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Usage by Type</CardTitle>
                <CardDescription>
                  Detailed breakdown of resource consumption
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { icon: Image, label: 'Images', value: '7,523', percentage: 75 },
                    { icon: Database, label: 'Storage', value: '42.7 GB', percentage: 43 },
                    { icon: Network, label: 'Bandwidth', value: '127.3 GB', percentage: 25 },
                    { icon: Cpu, label: 'Processing', value: '892 hrs', percentage: 62 },
                  ].map((item, index) => {
                    const Icon = item.icon
                    return (
                      <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Icon className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium">{item.label}</span>
                          </div>
                          <span className="text-sm text-muted-foreground">{item.value}</span>
                        </div>
                        <Progress value={item.percentage} className="h-1.5" />
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="projects" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Projects by Usage</CardTitle>
              <CardDescription>
                Projects consuming the most resources
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topProjects.map((project, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{index + 1}.</span>
                        <span className="text-sm font-medium">{project.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">
                          {project.usage.toLocaleString()} images
                        </span>
                        <Badge variant="outline">{project.percentage}%</Badge>
                      </div>
                    </div>
                    <Progress value={project.percentage} className="h-2" />
                  </div>
                ))}
              </div>
              <Button variant="outline" className="w-full mt-4">
                View All Projects
                <ChevronRight className="h-4 w-4 ml-2" />
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Usage Alerts */}
      <div className="space-y-4">
        <Card className="bg-yellow-50 dark:bg-yellow-950/20 border-yellow-200 dark:border-yellow-800">
          <CardContent className="pt-6">
            <div className="flex gap-3">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium text-yellow-900 dark:text-yellow-100">
                  Approaching image limit
                </p>
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  You've used 75% of your monthly image processing quota. Consider upgrading your plan for more resources.
                </p>
                <Button variant="link" className="h-auto p-0 text-yellow-700 dark:text-yellow-300">
                  Upgrade plan →
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
          <CardContent className="pt-6">
            <div className="flex gap-3">
              <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                  Usage tip
                </p>
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  Enable image compression to reduce storage usage by up to 40% without significant quality loss.
                </p>
                <Button variant="link" className="h-auto p-0 text-blue-700 dark:text-blue-300">
                  Learn more →
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}
