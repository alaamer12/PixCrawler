'use client'

import { memo, useMemo } from 'react'

interface Step {
	num: string
	title: string
	desc: string
}

const steps: Step[] = [
	{
		num: '1',
		title: 'Configure',
		desc: 'Define your dataset requirements using our intuitive interface or JSON schema'
	},
	{
		num: '2',
		title: 'Process',
		desc: 'Our AI-powered system discovers, validates, and organizes your images automatically'
	},
	{
		num: '3',
		title: 'Download',
		desc: 'Get your processed dataset in optimized formats ready for immediate use'
	}
]

const StepCard = memo(({ num, title, desc }: Step) => {
	return (
		<div className="flex-1 text-center">
			<div className="w-16 h-16 rounded-full border-2 border-foreground mx-auto mb-4 flex items-center justify-center text-2xl font-bold bg-background">
				{num}
			</div>
			<h3 className="font-bold text-xl mb-2">{title}</h3>
			<p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
		</div>
	)
})
StepCard.displayName = 'StepCard'

const StepArrow = memo(() => {
	return (
		<div className="hidden md:block text-3xl text-muted-foreground">→</div>
	)
})
StepArrow.displayName = 'StepArrow'

export const HowItWorks = memo(() => {
	const stepElements = useMemo(() => 
		steps.map((step, i) => (
			<>
				<StepCard key={i} {...step} />
				{i < steps.length - 1 && <StepArrow key={`arrow-${i}`} />}
			</>
		)),
		[]
	)

	return (
		<section id="how-it-works" className="border-b border-border py-16 md:py-24 bg-muted/30">
			<div className="container mx-auto px-4 lg:px-8">
				<h2 className="text-3xl md:text-4xl font-bold text-center mb-12 md:mb-16">
					How It Works
				</h2>
				
				<div className="flex flex-col md:flex-row gap-8 md:gap-12 max-w-4xl mx-auto items-center">
					{stepElements}
				</div>
			</div>
		</section>
	)
})
HowItWorks.displayName = 'HowItWorks'
