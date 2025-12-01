import { config } from 'dotenv';
import postgres from 'postgres';
import fs from 'fs';
import path from 'path';

// Load environment variables
config({ path: '.env.local' });
config({ path: '.env' });

const run = async () => {
    const connectionString = process.env.POSTGRES_URL || process.env.DATABASE_URL;

    if (!connectionString) {
        console.error('POSTGRES_URL or DATABASE_URL is not defined');
        process.exit(1);
    }

    const sql = postgres(connectionString);

    try {
        const migrationPath = path.join(process.cwd(), 'supabase/migrations/20240101000000_fix_profiles_trigger.sql');
        console.log(`Reading migration file from: ${migrationPath}`);

        const migrationSql = fs.readFileSync(migrationPath, 'utf8');

        console.log('Executing migration...');
        await sql.unsafe(migrationSql);

        console.log('Migration applied successfully!');
    } catch (error) {
        console.error('Error applying migration:', error);
    } finally {
        await sql.end();
    }
};

run();
