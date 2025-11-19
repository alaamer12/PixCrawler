'use client'

import {useParams} from 'next/navigation'
import {DatasetDashboard} from '@/components/dataset/dashboard'

export default function DatasetDetailPage() {
  const params = useParams()
  const datasetId = params.id as string

  return <DatasetDashboard datasetId={datasetId}/>
}
