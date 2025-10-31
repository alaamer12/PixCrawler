'use client'

import React, { useState } from 'react'
import { ProfileLayout } from '@/components/profile/ProfileLayout'
import {
  AccountProfile,
  NotificationSettings,
  Settings,
  Subscription,
  Usage,
  ApiKeys,
} from '@/components/profile/sections'

export default function ProfilePage() {
  const [activeSection, setActiveSection] = useState('account')

  const renderSection = () => {
    switch (activeSection) {
      case 'account':
        return <AccountProfile />
      case 'notifications':
        return <NotificationSettings />
      case 'settings':
        return <Settings />
      case 'subscription':
        return <Subscription />
      case 'usage':
        return <Usage />
        // Will be used later, but not now
      // case 'auto-refills':
      // case 'credit-history':
      // case 'manage-plan':
      //   return <CreditManagement />
      case 'api-keys':
        return <ApiKeys />
        // Will be used later, but not now
      // case 'referrals':
      //   return <Referrals />
      default:
        return <AccountProfile />
    }
  }

  return (
    <ProfileLayout activeSection={activeSection} onSectionChange={setActiveSection}>
      {renderSection()}
    </ProfileLayout>
  )
}
