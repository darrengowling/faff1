#!/usr/bin/env node

/**
 * Database Reset Script for E2E Testing
 * Resets MongoDB to clean state with test users
 */

const { MongoClient } = require('mongodb');

const MONGO_URL = process.env.MONGO_URL || 'mongodb://localhost:27017';
const DB_NAME = process.env.DB_NAME || 'test_db';

const TEST_USERS = [
  {
    id: 'commish-test-id',
    email: 'commish@test.local',
    display_name: 'Commissioner',
    verified: true,
    created_at: new Date()
  },
  {
    id: 'alice-test-id', 
    email: 'alice@test.local',
    display_name: 'Alice',
    verified: true,
    created_at: new Date()
  },
  {
    id: 'bob-test-id',
    email: 'bob@test.local', 
    display_name: 'Bob',
    verified: true,
    created_at: new Date()
  }
];

async function resetDatabase() {
  const client = new MongoClient(MONGO_URL);
  
  try {
    await client.connect();
    console.log('✅ Connected to MongoDB');
    
    const db = client.db(DB_NAME);
    
    // Drop all collections
    const collections = await db.listCollections().toArray();
    for (const collection of collections) {
      await db.collection(collection.name).drop();
      console.log(`🗑️  Dropped collection: ${collection.name}`);
    }
    
    // Create fresh test users
    if (TEST_USERS.length > 0) {
      await db.collection('users').insertMany(TEST_USERS);
      console.log(`👥 Created ${TEST_USERS.length} test users`);
    }
    
    console.log('✅ Database reset complete');
    
  } catch (error) {
    console.error('❌ Database reset failed:', error);
    process.exit(1);
  } finally {
    await client.close();
  }
}

if (require.main === module) {
  resetDatabase().catch(console.error);
}

module.exports = { resetDatabase };