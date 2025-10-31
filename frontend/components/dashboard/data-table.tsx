'use client'

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { 
  MoreHorizontal, 
  Eye, 
  Edit, 
  Trash2, 
  Download,
  Play,
  Pause,
  RotateCw,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle
} from 'lucide-react'
import { ReactNode } from 'react'

export interface Column<T> {
  key: string
  header: string
  cell?: (item: T) => ReactNode
  className?: string
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  loading?: boolean
  emptyMessage?: string
  onView?: (item: T) => void
  onEdit?: (item: T) => void
  onDelete?: (item: T) => void
  actions?: Array<{
    label: string
    icon?: ReactNode
    onClick: (item: T) => void
    variant?: 'default' | 'destructive'
  }>
  className?: string
}

export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  loading = false,
  emptyMessage = 'No data available',
  onView,
  onEdit,
  onDelete,
  actions,
  className
}: DataTableProps<T>) {
  if (loading) {
    return <DataTableSkeleton columns={columns.length} rows={5} />
  }

  return (
    <div className={cn('rounded-lg border bg-card/50 backdrop-blur-sm overflow-hidden', className)}>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent border-b border-border/50">
            {columns.map((column) => (
              <TableHead key={column.key} className={cn('font-semibold', column.className)}>
                {column.header}
              </TableHead>
            ))}
            {(onView || onEdit || onDelete || actions) && (
              <TableHead className="w-[100px] text-right">Actions</TableHead>
            )}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length === 0 ? (
            <TableRow>
              <TableCell 
                colSpan={columns.length + (onView || onEdit || onDelete || actions ? 1 : 0)} 
                className="h-32 text-center text-muted-foreground"
              >
                {emptyMessage}
              </TableCell>
            </TableRow>
          ) : (
            data.map((item, index) => (
              <TableRow key={index} className="hover:bg-muted/30 transition-colors">
                {columns.map((column) => (
                  <TableCell key={column.key} className={column.className}>
                    {column.cell ? column.cell(item) : item[column.key]}
                  </TableCell>
                ))}
                {(onView || onEdit || onDelete || actions) && (
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon-sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-[160px]">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        {onView && (
                          <DropdownMenuItem onClick={() => onView(item)}>
                            <Eye className="mr-2 h-4 w-4" />
                            View
                          </DropdownMenuItem>
                        )}
                        {onEdit && (
                          <DropdownMenuItem onClick={() => onEdit(item)}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                        )}
                        {actions?.map((action, idx) => (
                          <DropdownMenuItem 
                            key={idx} 
                            onClick={() => action.onClick(item)}
                            className={action.variant === 'destructive' ? 'text-destructive' : ''}
                          >
                            {action.icon}
                            {action.label}
                          </DropdownMenuItem>
                        ))}
                        {onDelete && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              onClick={() => onDelete(item)}
                              className="text-destructive"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                )}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}

function DataTableSkeleton({ columns, rows }: { columns: number; rows: number }) {
  return (
    <div className="rounded-lg border bg-card/50 backdrop-blur-sm">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            {Array.from({ length: columns }).map((_, i) => (
              <TableHead key={i}>
                <Skeleton className="h-4 w-20" />
              </TableHead>
            ))}
            <TableHead>
              <Skeleton className="h-4 w-16 ml-auto" />
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Array.from({ length: rows }).map((_, i) => (
            <TableRow key={i}>
              {Array.from({ length: columns }).map((_, j) => (
                <TableCell key={j}>
                  <Skeleton className="h-4 w-full" />
                </TableCell>
              ))}
              <TableCell>
                <Skeleton className="h-8 w-8 ml-auto" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

// Status badge component for consistent status display
export function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: ReactNode }> = {
    pending: { variant: 'outline', icon: <Clock className="mr-1 h-3 w-3" /> },
    running: { variant: 'default', icon: <Play className="mr-1 h-3 w-3" /> },
    completed: { variant: 'secondary', icon: <CheckCircle className="mr-1 h-3 w-3" /> },
    failed: { variant: 'destructive', icon: <XCircle className="mr-1 h-3 w-3" /> },
    paused: { variant: 'outline', icon: <Pause className="mr-1 h-3 w-3" /> },
    active: { variant: 'default', icon: <CheckCircle className="mr-1 h-3 w-3" /> },
    archived: { variant: 'outline', icon: <AlertCircle className="mr-1 h-3 w-3" /> }
  }

  const config = variants[status.toLowerCase()] || { variant: 'outline', icon: null }

  return (
    <Badge variant={config.variant} className="font-medium">
      {config.icon}
      {status}
    </Badge>
  )
}
