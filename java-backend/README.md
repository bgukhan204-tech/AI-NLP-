# Enterprise RAG-Based Document Intelligence & RBAC — Java

Java/Spring Boot migration of the AI-NLP enterprise RAG/RBAC project.

## Stack
Java 21, Spring Boot 3.5.16, Spring Security, BCrypt, JWT, Spring Data JPA, PostgreSQL/H2, Apache PDFBox and Apache POI.

## Request flow
1. POST /api/auth/login with username/password.
2. BCrypt verifies the password hash.
3. Server issues a short-lived JWT containing username and role.
4. Client sends Authorization: Bearer TOKEN.
5. JwtAuthFilter validates the token and checks the database user is active.
6. RBAC maps the role to allowed departments.
7. Retrieval filters by allowed departments before context is used.
8. Only authorized context is eligible for RAG generation.

## Demo users
All seeded users initially use ChangeMe123!. Change or remove these credentials before deployment.

employee1 = EMPLOYEE
manager1 = MANAGER
hradmin = HR_ADMIN

## Run
From java-backend:
mvn spring-boot:run

Login endpoint:
POST http://localhost:8080/api/auth/login

RAG endpoint:
POST http://localhost:8080/api/rag/ask

## Migration note
The original Python application remains in the repository so the existing deployment is not broken. This Java backend is the migration path. The next step is replacing the temporary keyword retrieval in RagService with Qdrant embeddings/search and Groq generation, followed by React UI and production OIDC SSO.
