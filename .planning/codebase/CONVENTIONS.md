# Coding Conventions

- **Frontend**: Functional React components with hooks. Styling heavily relies on Tailwind utility classes and custom glassmorphism effects (`glass-card`, `glass-input`).
- **Backend/Worker**: Procedural Python scripts with direct Supabase client initialization. Hardcoded polling loops (`while True` with `time.sleep`) instead of webhooks or triggers.
- **Error Handling**: Basic try/catch blocks that write error messages back to the database queue for the frontend to read.
