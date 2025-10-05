'use client'

import { memo, useMemo } from 'react'

const partnerLogos = [1, 2, 3, 4, 5]

const PartnerLogo = memo(({ index }: { index: number }) => {
	return (
		<div className="w-28 h-12 border border-border bg-background rounded flex items-center justify-center text-xs text-muted-foreground">
			Logo {index}
		</div>
	)
})
PartnerLogo.displayName = 'PartnerLogo'

export const TrustedBy = memo(() => {
	const logos = useMemo(() => 
		partnerLogos.map((i) => (
			<PartnerLogo key={i} index={i} />
		)),
		[]
	)

	return (
		<section className="border-b border-border py-12 md:py-16 bg-muted/30">
			<div className="container mx-auto px-4 lg:px-8">
				<p className="text-center text-xs uppercase tracking-wider text-muted-foreground mb-8">
					Trusted by teams at
				</p>
				<div className="flex flex-wrap justify-center items-center gap-8 md:gap-12">
					{logos}
				</div>
			</div>
		</section>
	)
})
TrustedBy.displayName = 'TrustedBy'
