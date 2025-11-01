import {db} from './index';
import {profiles, projects, crawlJobs, notifications} from './schema';

// NOTE: This seed file is for development/testing only.
// In production, profiles are created automatically via Supabase Auth triggers.

async function seedProjects(userId: string) {
  console.log('Creating sample projects...');

  const [project1, project2] = await db
    .insert(projects)
    .values([
      {
        name: 'ML Training Dataset',
        description: 'Image dataset for computer vision model training',
        userId: userId,
        status: 'active',
      },
      {
        name: 'Product Photography',
        description: 'E-commerce product images collection',
        userId: userId,
        status: 'active',
      },
    ])
    .returning();

  console.log('Sample projects created.');
  return [project1, project2];
}

async function seedCrawlJobs(projectId: number) {
  console.log('Creating sample crawl jobs...');

  await db.insert(crawlJobs).values([
    {
      projectId: projectId,
      name: 'Cat Images Collection',
      keywords: ['cats', 'kittens', 'felines'],
      maxImages: 500,
      status: 'completed',
      progress: 100,
      totalImages: 487,
      downloadedImages: 487,
      validImages: 452,
      totalChunks: 5,
      completedChunks: 5,
      activeChunks: 0,
      failedChunks: 0,
      taskIds: [],
    },
    {
      projectId: projectId,
      name: 'Dog Breeds Dataset',
      keywords: ['dogs', 'puppies', 'canines'],
      maxImages: 1000,
      status: 'running',
      progress: 45,
      totalImages: 450,
      downloadedImages: 450,
      validImages: 423,
      totalChunks: 10,
      completedChunks: 4,
      activeChunks: 1,
      failedChunks: 0,
      taskIds: ['task-123', 'task-456'],
    },
  ]);

  console.log('Sample crawl jobs created.');
}

async function seedNotifications(userId: string) {
  console.log('Creating sample notifications...');

  await db.insert(notifications).values([
    {
      userId: userId,
      type: 'success',
      category: 'crawl_job',
      title: 'Crawl Job Completed',
      message: 'Your "Cat Images Collection" job has finished successfully with 452 valid images.',
      icon: 'circle-check-big',
      color: 'green',
      actionUrl: '/dashboard/projects/1',
      actionLabel: 'View Project',
      isRead: false,
    },
    {
      userId: userId,
      type: 'info',
      category: 'system',
      title: 'Welcome to PixCrawler',
      message: 'Start by creating your first project and crawl job.',
      icon: 'info',
      color: 'blue',
      isRead: true,
    },
  ]);

  console.log('Sample notifications created.');
}

async function seed() {
  console.log('Starting seed process...');
  console.log('⚠️  Note: User profiles should be created via Supabase Auth, not directly.');
  console.log('⚠️  This seed assumes a test user already exists in Supabase Auth.');
  
  // Replace with actual user UUID from your Supabase Auth
  const testUserId = '00000000-0000-0000-0000-000000000000';
  
  console.log('\n⚠️  IMPORTANT: Update testUserId with a real UUID from your Supabase Auth users!');
  console.log('You can get this from: Supabase Dashboard → Authentication → Users\n');
  
  try {
    // Seed projects
    const [project1, project2] = await seedProjects(testUserId);
    
    // Seed crawl jobs for first project
    await seedCrawlJobs(project1.id);
    
    // Seed notifications
    await seedNotifications(testUserId);
    
    console.log('\n✅ Seed completed successfully!');
    console.log('Sample data created:');
    console.log('  - 2 projects');
    console.log('  - 2 crawl jobs');
    console.log('  - 2 notifications');
  } catch (error) {
    console.error('\n❌ Seed failed:', error);
    throw error;
  }
}

// Run seed if executed directly
if (require.main === module) {
  seed()
    .catch((error) => {
      console.error('Seed process failed:', error);
      process.exit(1);
    })
    .finally(() => {
      console.log('Seed process finished. Exiting...');
      process.exit(0);
    });
}

export {seed};
