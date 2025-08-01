// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

// Create the database
db = db.getSiblingDB('pinterest_agent');

// Create collections with proper indexes
db.createCollection('pinterest_accounts');
db.createCollection('prompts');
db.createCollection('sessions');
db.createCollection('pins');

// Create indexes for better performance
db.pinterest_accounts.createIndex({ "email": 1 }, { unique: true });
db.pinterest_accounts.createIndex({ "username": 1 });
db.pinterest_accounts.createIndex({ "is_active": 1 });

db.prompts.createIndex({ "created_at": -1 });
db.prompts.createIndex({ "status": 1 });

db.sessions.createIndex({ "prompt_id": 1 });
db.sessions.createIndex({ "created_at": -1 });
db.sessions.createIndex({ "status": 1 });

db.pins.createIndex({ "prompt_id": 1 });
db.pins.createIndex({ "created_at": -1 });
db.pins.createIndex({ "status": 1 });
db.pins.createIndex({ "match_score": -1 });

// Create a user for the application (optional, using root user for simplicity)
// db.createUser({
//   user: "pinterest_app",
//   pwd: "app_password",
//   roles: [
//     { role: "readWrite", db: "pinterest_agent" }
//   ]
// });

print("MongoDB initialization completed successfully!"); 