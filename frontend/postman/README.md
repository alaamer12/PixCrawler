# PixCrawler Frontend Mock Server

This directory contains Postman collections to set up a mock API server for frontend development. This allows developers to work on the frontend without running the full Python backend.

# PixCrawler Frontend Mock Server

This directory contains Postman collections to set up a mock API server for frontend development. This allows developers to work on the frontend without running the full Python backend.

## Contents

- `PixCrawler_Frontend_Mock.json`: The main collection containing all required API endpoints for the frontend.

## Setup Instructions

We use [Prism](https://stoplight.io/open-source/prism) to run a local mock server based on the OpenAPI specification.

1.  **Install Dependencies**:
    The project already includes the necessary tools. If you haven't installed them globally, you can run:
    ```bash
    npm install -g @stoplight/prism-cli
    ```

2.  **Run Mock Server**:
    Run the following command in the `frontend` directory:
    ```bash
    prism mock postman/openapi.json -p 4010
    ```
    This will start a mock server at `http://127.0.0.1:4010`.

3.  **Configure Frontend**:
    Create or update your `.env.local` file in the `frontend` directory:
    ```env
    NEXT_PUBLIC_API_URL=http://127.0.0.1:4010/api/v1
    ```

4.  **Start Development**:
    Restart the Next.js development server (`npm run dev` or `bun dev`).

## Available Endpoints

The mock server provides responses for the following resources based on the `openapi.json` definition:

### Auth
- `GET /auth/me`: Get current user profile
- `POST /auth/verify-token`: Verify JWT token
- `POST /auth/sync-profile`: Sync user profile

### Projects
- `GET /projects`: List all projects
- `GET /projects/:id`: Get a specific project
- `POST /projects`: Create a new project
- `PATCH /projects/:id`: Update a project
- `DELETE /projects/:id`: Delete a project

### Datasets
- `GET /projects/:projectId/datasets`: List datasets for a project
- `GET /projects/:projectId/datasets/:datasetId`: Get a specific dataset
- `POST /projects/:projectId/datasets`: Create a new dataset
- `GET /datasets/stats`: Get global dataset statistics
- `POST /datasets/:id/build`: Start a dataset build job
- `GET /datasets/:id/status`: Get build status

### Jobs
- `GET /jobs`: List crawl jobs
- `GET /jobs/:id/logs`: Get job logs

### Notifications
- `GET /notifications`: List notifications
- `PATCH /notifications/:id`: Mark notification as read
- `POST /notifications/mark-all-read`: Mark all notifications as read

## Notes

- The mock server returns static JSON data defined in `openapi.json`.
- State is not persisted (e.g., creating a project won't actually add it to the list returned by `GET /projects`).
- Use this for UI development and testing API integration flows.
