# 001: Use Shared Supabase Database

---

- **Status:** Accepted
- **Date:** 2025-10-03
- **Authors:** PixCrawler Team

### 1. Summary

This ADR approves the use of a shared Supabase PostgreSQL database for the new FastAPI backend, allowing both the Next.js frontend and the backend to connect directly to the same database instance. This approach enables rapid development by leveraging the existing investment in Supabase and Drizzle ORM, providing a single source of truth for all application data.

### 2. Context

The PixCrawler application is evolving from a frontend-centric application to a full-stack system with a dedicated Python backend for computationally intensive image crawling and dataset generation. The existing architecture consists of a Next.js 15 frontend using TypeScript, Drizzle ORM, and a Supabase PostgreSQL database. A mature Python "Builder" package exists for the core crawling logic.

The key requirement is to integrate a new FastAPI backend to execute these crawling jobs asynchronously without disrupting the existing frontend user experience, which relies heavily on Supabase's real-time features for job status updates. The decision must balance development speed, system complexity, and the ability to leverage existing infrastructure. Stakeholders include the frontend and backend development teams, product management, and operations.

### 3. Decision

We have decided to implement a **Shared Supabase Database** architecture. The FastAPI backend will connect directly to the same Supabase PostgreSQL instance used by the Next.js frontend, using a service role key for administrative access. The frontend will continue using the Supabase JS client with its existing RLS policies.

```
+------------------+          +-----------------------+
|                  |          |                       |
|  Next.js         |          |  FastAPI              |
|  Frontend        |          |  Backend              |
|                  |          |                       |
+------------------+          +-----------------------+
         |                              |
         | @supabase/supabase-js        | asyncpg/SQLAlchemy
         | (Anon Key + RLS)             | (Service Role Key)
         v                              v
        +------------------------------------+
        |                                    |
        |      Supabase PostgreSQL           |
        |                                    |
        +------------------------------------+

```

### 4. Rationale

The decision was driven by the need for a fast, low-risk path to a Minimum Viable Product (MVP) that leverages our current, well-functioning stack.

- **Maximizes Development Velocity and Minimizes Migration Risk:** The existing frontend code, Drizzle schema, and database infrastructure require zero changes. This allows the backend team to begin implementation immediately and deliver a functional integrated system within 1-2 weeks, compared to 4-6 weeks for a full API-first rewrite. The frontend team remains unblocked.
- **Leverages Existing Supabase Investment:** We already pay for and rely on Supabase features such as Auth, Row Level Security (RLS), and real-time subscriptions. This architecture allows us to continue using these battle-tested features directly in the frontend, avoiding the significant cost and complexity of re-implementing them in a custom backend.
- **Single Source of Truth Eliminates Data Synchronization Complexity:** With only one database, there is no risk of data drift, eventual consistency issues, or the complexity of building and maintaining a synchronization layer between two data stores. This simplifies the logic for both reading and writing data.
- **Direct Database Access Ensures High Performance for Backend Jobs:** The backend's primary role is processing crawl jobs, which involves intensive database writes for image metadata and job status updates. A direct connection to PostgreSQL is the highest-performance option, avoiding the overhead of an additional HTTP/API layer for these internal operations.

**Trade-offs Accepted**

- **Vendor Lock-in to Supabase:** We are accepting a dependency on Supabase's platform, including its connection pooling limits and pricing model. This is acceptable because the productivity gains and accelerated time-to-market currently outweigh the long-term flexibility of a vendor-agnostic system. Furthermore, Supabase uses standard PostgreSQL, making a future migration feasible if necessary.
- **Mixed Data Access Patterns:** The architecture uses two different clients and ORMs (Drizzle in frontend, SQLAlchemy in backend) to access the same database. We accept the risk of slight behavioral differences or schema drift. This will be mitigated by careful code review and by using the shared Drizzle schema as the canonical source for any new table definitions.
- **Security Complexity of Service Role Key:** The backend will use a privileged service role key that bypasses RLS. We accept the responsibility of securing this key and ensuring the backend code itself implements robust authorization checks. This risk is mitigated by strict key management and code review processes.

### 5. Alternatives Considered

**Alternative 2: Database Schema Sharing**

- **Pros:** Guarantees type safety across Frontend (TypeScript) and Backend (Python) through a shared schema package and automated code generation. Reduces the risk of schema drift and serves as a living API contract.
- **Cons:** Introduces significant complexity with a new build pipeline, synchronization tooling, and dependency management. Adds an estimated 2-3 weeks of development time and ongoing maintenance overhead.
- **Rejected because:** The marginal benefit of guaranteed type safety does not justify the high initial and ongoing cost for our current team size and project stage. The faster, simpler approach of manually keeping models in sync is preferable for now.

**Alternative 3: API-First Architecture**

- **Pros:** Creates a clean separation of concerns with a well-defined API contract. Provides the backend with full control over all data access, simplifying security and monitoring. Reduces vendor lock-in.
- **Cons:** Requires a complete refactoring of the frontend to remove the Supabase client, replacing it with calls to custom FastAPI endpoints. We would lose built-in Supabase features like real-time, necessitating a custom WebSocket implementation. This was estimated to take 4-6 weeks.
- **Rejected because:** The development cost and timeline are prohibitive for achieving our near-term goals. It would actively remove functionality (seamless real-time updates) that we currently have for free, forcing us to rebuild it. This is an over-engineered solution for our current needs.

### 6. Consequences

- **Positive**
    - The backend can be integrated and processing jobs within two weeks, dramatically accelerating our timeline.
    - The frontend team experiences zero disruption and continues to use all existing Supabase features.
    - Operational complexity remains low, as we are managing only one primary database instance.
    - Total cost of development and initial infrastructure is the lowest among the options.
- **Negative**
    - The backend team must manually ensure their SQLAlchemy models remain synchronized with the frontend's Drizzle schema.
    - We must carefully monitor and manage database connections to stay within Supabase's connection pool limits as traffic grows.
    - Future decoupling from Supabase would require a significant migration effort, similar to implementing Alternative 3 at a later date.

### 7. Success Criteria

- **Functional Integration:** A crawl job created in the Next.js frontend is successfully picked up and processed by the FastAPI backend, with its status updated in the database and reflected in the frontend via real-time subscription, within 2 weeks of development start.
- **Performance:** Database query performance from the backend remains under 100ms for 95% of queries under expected load (e.g., concurrent execution of 10+ crawl jobs).
- **Stability:** The system operates for 30 days without incidents caused by connection pool exhaustion or schema mismatches between the backend and frontend.
- **Developer Experience:** Backend developers can create new database entities by referencing the Drizzle schema and creating corresponding SQLAlchemy models without a formal synchronization process, without introducing errors.

### 8. Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| **Supabase Connection Pool Exhaustion** | Medium | Implement robust connection pooling in the FastAPI backend using `asyncpg`; Monitor database connection metrics actively in Supabase dashboard; Implement query timeouts and retry logic. |
| **Schema Drift between Drizzle and SQLAlchemy** | Low | Use the existing Drizzle schema as the source of truth for all new tables; Implement a manual review step for new model definitions where backend and frontend developers cross-check the schemas. |
| **Improper use of Service Role Key bypassing business logic** | High | The service role key will be stored securely in backend environment variables only. Backend application logic will include explicit authorization checks, treating the service role as a system user with specific privileges, not a free pass. |
| **Vendor-specific Supabase features causing future lock-in** | Low | Deliberately avoid using Supabase-specific SQL extensions or features in the core application logic. Confine Supabase-specific code (e.g., auth client) to the frontend and well-isolated parts of the backend. |

## References

[Database Architecture Options](https://www.notion.so/Database-Architecture-Options-275461aa270580369aedc3aa4289816f?pvs=21)