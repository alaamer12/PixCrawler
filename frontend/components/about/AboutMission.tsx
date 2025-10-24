import {memo} from 'react'
import {Target, Users, Database} from 'lucide-react'

interface MissionCard {
  icon: typeof Target
  title: string
  description: string
}

const MISSIONS: MissionCard[] = [
  {
    icon: Target,
    title: 'Real-World Focus',
    description: 'Addressing practical challenges in ML/AI dataset creation that researchers and developers face daily.'
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description: 'Built by a dedicated data engineering team working together to create accessible AI tools.'
  },
  {
    icon: Database,
    title: 'DEPI Initiative',
    description: 'Proudly sponsored by Digital Egypt Pioneers Initiative, empowering Egyptian tech innovation.'
  }
]

const MissionCard = memo(({icon: Icon, title, description}: MissionCard) => (
  <div className="text-center">
    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
      <Icon className="w-8 h-8 text-primary"/>
    </div>
    <h3 className="text-xl font-semibold mb-3">{title}</h3>
    <p className="text-muted-foreground">{description}</p>
  </div>
))
MissionCard.displayName = 'MissionCard'

export const AboutMission = memo(() => {
  return (
    <section className="py-16 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Our Mission</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Tackling real-world challenges through innovative data engineering solutions
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {MISSIONS.map((mission) => (
              <MissionCard key={mission.title} {...mission} />
            ))}
          </div>
        </div>
      </div>
    </section>
  )
})

AboutMission.displayName = 'AboutMission'
