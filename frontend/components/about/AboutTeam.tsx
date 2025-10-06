'use client'

import { memo } from 'react'
import { Github, Linkedin, Twitter } from 'lucide-react'

interface TeamMember {
  name: string
  role: string
  bio: string
  avatar: string
  social: {
    github?: string
    linkedin?: string
    twitter?: string
  }
}

const TEAM_MEMBERS: TeamMember[] = [
  {
    name: 'Alex Chen',
    role: 'Co-Founder & CEO',
    bio: 'Former ML engineer at Google. PhD in Computer Vision from Stanford. Passionate about democratizing AI development.',
    avatar: '/api/placeholder/150/150',
    social: {
      github: '#',
      linkedin: '#',
      twitter: '#'
    }
  },
  {
    name: 'Sarah Rodriguez',
    role: 'Co-Founder & CTO',
    bio: 'Ex-Meta AI researcher. Built large-scale data pipelines for computer vision models. Loves solving complex technical challenges.',
    avatar: '/api/placeholder/150/150',
    social: {
      github: '#',
      linkedin: '#'
    }
  },
  {
    name: 'Marcus Johnson',
    role: 'Head of Engineering',
    bio: 'Full-stack engineer with 10+ years experience. Previously at Stripe and Airbnb. Expert in scalable distributed systems.',
    avatar: '/api/placeholder/150/150',
    social: {
      github: '#',
      linkedin: '#',
      twitter: '#'
    }
  },
  {
    name: 'Dr. Emily Watson',
    role: 'Head of AI Research',
    bio: 'AI researcher and professor. Published 50+ papers on computer vision and machine learning. Advisor to multiple AI startups.',
    avatar: '/api/placeholder/150/150',
    social: {
      linkedin: '#',
      twitter: '#'
    }
  },
  {
    name: 'David Kim',
    role: 'Head of Product',
    bio: 'Product leader with experience at Microsoft and Adobe. Focused on building intuitive tools that developers love to use.',
    avatar: '/api/placeholder/150/150',
    social: {
      linkedin: '#',
      twitter: '#'
    }
  },
  {
    name: 'Lisa Zhang',
    role: 'Head of Design',
    bio: 'Design systems expert. Previously at Figma and Notion. Believes great design makes complex technology accessible to everyone.',
    avatar: '/api/placeholder/150/150',
    social: {
      linkedin: '#',
      twitter: '#'
    }
  }
]

interface TeamMemberCardProps {
  member: TeamMember
}

const TeamMemberCard = memo(({ member }: TeamMemberCardProps) => {
  return (
    <div className="bg-card border border-border rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
      <img
        src={member.avatar}
        alt={member.name}
        className="w-24 h-24 rounded-full mx-auto mb-4 object-cover"
      />
      <h3 className="text-lg font-semibold mb-1">{member.name}</h3>
      <p className="text-primary text-sm font-medium mb-3">{member.role}</p>
      <p className="text-muted-foreground text-sm mb-4 leading-relaxed">{member.bio}</p>
      
      <div className="flex justify-center gap-3">
        {member.social.github && (
          <a
            href={member.social.github}
            className="p-2 text-muted-foreground hover:text-foreground transition-colors"
            aria-label={`${member.name} GitHub`}
          >
            <Github className="w-4 h-4" />
          </a>
        )}
        {member.social.linkedin && (
          <a
            href={member.social.linkedin}
            className="p-2 text-muted-foreground hover:text-foreground transition-colors"
            aria-label={`${member.name} LinkedIn`}
          >
            <Linkedin className="w-4 h-4" />
          </a>
        )}
        {member.social.twitter && (
          <a
            href={member.social.twitter}
            className="p-2 text-muted-foreground hover:text-foreground transition-colors"
            aria-label={`${member.name} Twitter`}
          >
            <Twitter className="w-4 h-4" />
          </a>
        )}
      </div>
    </div>
  )
})

TeamMemberCard.displayName = 'TeamMemberCard'

export const AboutTeam = memo(() => {
  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Meet Our Team
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            We're a diverse group of engineers, researchers, and designers united by our passion 
            for making AI development more accessible and efficient.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {TEAM_MEMBERS.map((member) => (
            <TeamMemberCard key={member.name} member={member} />
          ))}
        </div>
      </div>
    </section>
  )
})

AboutTeam.displayName = 'AboutTeam'