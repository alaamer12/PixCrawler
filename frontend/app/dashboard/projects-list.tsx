'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Project } from '@/lib/db/schema'

interface ProjectsListProps {
  userId: string
}

export function ProjectsList({ userId }: ProjectsListProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDescription, setNewProjectDescription] = useState('')
  const supabase = createClient()

  useEffect(() => {
    fetchProjects()
  }, [userId])

  const fetchProjects = async () => {
    try {
      const { data, error } = await supabase
        .from('projects')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })

      if (error) throw error
      setProjects(data || [])
    } catch (error) {
      console.error('Error fetching projects:', error)
    } finally {
      setLoading(false)
    }
  }

  const createProject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newProjectName.trim()) return

    try {
      const { data, error } = await supabase
        .from('projects')
        .insert({
          name: newProjectName,
          description: newProjectDescription,
          user_id: userId,
        })
        .select()
        .single()

      if (error) throw error
      
      setProjects([data, ...projects])
      setNewProjectName('')
      setNewProjectDescription('')
      setShowCreateForm(false)
    } catch (error) {
      console.error('Error creating project:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-medium text-gray-900">Your Projects</h2>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
        >
          New Project
        </button>
      </div>

      {showCreateForm && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Project</h3>
          <form onSubmit={createProject} className="space-y-4">
            <div>
              <label htmlFor="projectName" className="block text-sm font-medium text-gray-700">
                Project Name
              </label>
              <input
                type="text"
                id="projectName"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Enter project name"
                required
              />
            </div>
            <div>
              <label htmlFor="projectDescription" className="block text-sm font-medium text-gray-700">
                Description (optional)
              </label>
              <textarea
                id="projectDescription"
                value={newProjectDescription}
                onChange={(e) => setNewProjectDescription(e.target.value)}
                rows={3}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Describe your project"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Create Project
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {projects.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 text-4xl mb-4">📁</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
          <p className="text-gray-600 mb-4">Create your first project to start crawling images</p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
          >
            Create Your First Project
          </button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <div key={project.id} className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
              <h3 className="text-lg font-medium text-gray-900 mb-2">{project.name}</h3>
              {project.description && (
                <p className="text-gray-600 text-sm mb-4">{project.description}</p>
              )}
              <div className="flex justify-between items-center text-sm text-gray-500">
                <span>Created {new Date(project.createdAt).toLocaleDateString()}</span>
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                  {project.status}
                </span>
              </div>
              <div className="mt-4">
                <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  View Details →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
