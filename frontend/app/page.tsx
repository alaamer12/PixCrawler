import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import {
	Navigation,
	Hero,
	Features,
	HowItWorks,
	UseCases,
	TrustedBy,
	Footer
} from '@/components/LandingPage'
import { HeroBackground } from '@/components/LandingPage/HeroBackground'

export default async function HomePage() {
	const supabase = await createClient()

	const {
		data: { user },
	} = await supabase.auth.getUser()

	// Redirect authenticated users to dashboard
	if (user) {
		redirect('/dashboard')
	}

	return (
		<div className="relative min-h-screen bg-background overflow-hidden">
			<HeroBackground />
			<div className="relative z-10">
				<Navigation />
				<Hero />
				<Features />
				<HowItWorks />
				<UseCases />
				<TrustedBy />
				<Footer />
			</div>
		</div>
	)
}
