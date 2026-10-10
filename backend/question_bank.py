"""
NextHire - Question Bank & Personalization Engine
Manages technical questions and dynamic question selection based on role and resume skills.
"""
from typing import List, Dict, Any

QUESTION_STORE: List[Dict[str, Any]] = [
    # Python Developer
    {
        "id": 1,
        "question_code": "PL001",
        "target_role": "Python Developer",
        "category": "Python Core & Internals",
        "difficulty": "Intermediate",
        "question_text": "How does Python handle memory management and garbage collection, and what role does reference counting play?",
        "reference_answer": "Python manages memory using a private heap space. Primary memory reclamation is handled via reference counting, where an object is deallocated when its reference count drops to zero. To resolve cyclic references, Python includes a cyclic garbage collector using generational collection.",
        "key_concepts": ["memory management", "private heap", "garbage collection", "reference counting", "cyclic references", "generation"]
    },
    {
        "id": 2,
        "question_code": "PL002",
        "target_role": "Python Developer",
        "category": "Python Concurrency",
        "difficulty": "Advanced",
        "question_text": "What is the Global Interpreter Lock (GIL) in CPython, and how does it impact multi-threaded CPU-bound programs?",
        "reference_answer": "The GIL is a mutex that protects access to Python objects, preventing multiple native threads from executing Python bytecodes at once. For CPU-bound tasks, multi-threading offers no performance boost; developers use the multiprocessing module or asynchronous programming instead.",
        "key_concepts": ["GIL", "mutex", "CPython", "concurrency", "multi-threading", "multiprocessing", "CPU-bound"]
    },
    {
        "id": 3,
        "question_code": "PL003",
        "target_role": "Python Developer",
        "category": "Backend Frameworks",
        "difficulty": "Intermediate",
        "question_text": "Compare Flask and Django in terms of architecture, flexibility, and default database ORM capabilities.",
        "reference_answer": "Flask is a micro-framework that provides minimalism and complete flexibility to choose database ORMs like SQLAlchemy. Django is a batteries-included framework providing a built-in ORM, admin panel, authentication, and an opinionated MVT structure.",
        "key_concepts": ["Flask", "Django", "micro-framework", "ORM", "SQLAlchemy", "batteries-included", "MVT"]
    },

    # Java Developer
    {
        "id": 4,
        "question_code": "JA001",
        "target_role": "Java Developer",
        "category": "JVM Architecture",
        "difficulty": "Intermediate",
        "question_text": "Explain the JVM memory model, distinguishing between Heap Memory and Stack Memory.",
        "reference_answer": "Heap memory stores all instantiated objects and JRE classes across threads. Stack memory stores temporary variables, primitive types, and method call execution frames local to each thread. Stack is thread-safe and faster, while Heap requires garbage collection.",
        "key_concepts": ["JVM", "Heap memory", "Stack memory", "thread safety", "garbage collection", "method frames"]
    },
    {
        "id": 5,
        "question_code": "JA002",
        "target_role": "Java Developer",
        "category": "Java OOP & Collections",
        "difficulty": "Intermediate",
        "question_text": "What is the internal working of HashMap in Java, and how are hash collisions resolved in Java 8?",
        "reference_answer": "HashMap operates on hashing using buckets (array of Nodes). When collisions occur, entries are stored in a linked list. In Java 8+, once a bucket reaches the TREEIFY_THRESHOLD (8 entries), it converts to a Red-Black balanced tree, improving search from O(n) to O(log n).",
        "key_concepts": ["HashMap", "hashing", "bucket", "collision", "linked list", "Red-Black tree", "O(log n)"]
    },
    {
        "id": 6,
        "question_code": "JA003",
        "target_role": "Java Developer",
        "category": "Spring Boot & Enterprise",
        "difficulty": "Advanced",
        "question_text": "What is Dependency Injection and Inversion of Control in Spring Boot, and what are the primary bean scopes?",
        "reference_answer": "IoC is a design principle where control of object creation and lifetime is transferred to the Spring container. Dependency Injection is the mechanism used to implement IoC. Common bean scopes include Singleton (default) and Prototype.",
        "key_concepts": ["Dependency Injection", "Inversion of Control", "IoC container", "Spring Boot", "Singleton", "Prototype"]
    },

    # Web Developer
    {
        "id": 7,
        "question_code": "WD001",
        "target_role": "Web Developer",
        "category": "Frontend Core",
        "difficulty": "Intermediate",
        "question_text": "Explain the JavaScript Event Loop, Call Stack, Microtask Queue, and Callback Queue.",
        "reference_answer": "JavaScript is single-threaded. Synchronous code executes on the Call Stack. Asynchronous callbacks reside in queues. The Event Loop monitors the call stack; when empty, it processes microtasks (Promises) first, then macrotasks/callbacks from the Callback Queue (setTimeout, DOM events).",
        "key_concepts": ["Event Loop", "Call Stack", "Microtask Queue", "Callback Queue", "Promises", "single-threaded"]
    },
    {
        "id": 8,
        "question_code": "WD002",
        "target_role": "Web Developer",
        "category": "Modern Web & CSS",
        "difficulty": "Intermediate",
        "question_text": "What is the Critical Rendering Path in web browsers, and how do CSS and JavaScript impact page render times?",
        "reference_answer": "The Critical Rendering Path is the sequence of steps the browser takes to convert HTML, CSS, and JS into pixels: DOM, CSSOM, Render Tree, Layout, and Painting. CSS is render-blocking, and scripts can block HTML parsing unless deferred or asynchronous.",
        "key_concepts": ["Critical Rendering Path", "DOM", "CSSOM", "Render Tree", "Layout", "Painting", "render-blocking"]
    },
    {
        "id": 9,
        "question_code": "WD003",
        "target_role": "Web Developer",
        "category": "Web Security & Performance",
        "difficulty": "Advanced",
        "question_text": "What are Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF), and how do you protect against them?",
        "reference_answer": "XSS involves injecting malicious client-side scripts, mitigated by escaping user input and Content Security Policy (CSP). CSRF forces an authenticated user to execute unwanted actions, mitigated using SameSite cookie attributes and anti-CSRF tokens.",
        "key_concepts": ["XSS", "CSRF", "Content Security Policy", "SameSite cookies", "anti-CSRF tokens", "input sanitization"]
    },

    # Full Stack Developer
    {
        "id": 10,
        "question_code": "FS001",
        "target_role": "Full Stack Developer",
        "category": "System Design & Architecture",
        "difficulty": "Intermediate",
        "question_text": "Explain the architectural difference between monolithic systems and microservices, and how inter-service communication is typically handled.",
        "reference_answer": "A monolith bundles UI, business logic, and database access in a single codebase and deployable unit. Microservices split functionality into independently deployable domain services. Inter-service communication happens via synchronous REST/gRPC or asynchronous message brokers like RabbitMQ or Kafka.",
        "key_concepts": ["monolith", "microservices", "REST API", "gRPC", "message broker", "Kafka", "scalability"]
    },
    {
        "id": 11,
        "question_code": "FS002",
        "target_role": "Full Stack Developer",
        "category": "Database Architecture",
        "difficulty": "Intermediate",
        "question_text": "When would you choose a Relational Database (SQL) over a NoSQL database, and what are the trade-offs of ACID vs BASE?",
        "reference_answer": "SQL is preferred when complex relationships, schema integrity, and ACID transactions are required (e.g. finance, orders). NoSQL (e.g. MongoDB) fits flexible schemas, unstructured data, and massive horizontal write scaling under BASE consistency.",
        "key_concepts": ["SQL", "NoSQL", "ACID", "BASE", "transactions", "schema integrity", "horizontal scaling"]
    },
    {
        "id": 12,
        "question_code": "FS003",
        "target_role": "Full Stack Developer",
        "category": "API Design & State",
        "difficulty": "Advanced",
        "question_text": "Explain the differences between RESTful APIs and GraphQL, and compare session cookies with JWT token authentication.",
        "reference_answer": "REST uses fixed endpoints and standard HTTP verbs, often leading to over-fetching or under-fetching. GraphQL allows clients to request exact fields via a single endpoint. Session cookies store state server-side, whereas JWT tokens are stateless cryptographically signed payloads.",
        "key_concepts": ["REST", "GraphQL", "over-fetching", "JWT", "session cookies", "stateless authentication", "HTTP methods"]
    },

    # Data Analyst
    {
        "id": 13,
        "question_code": "DA001",
        "target_role": "Data Analyst",
        "category": "SQL & Data Aggregation",
        "difficulty": "Intermediate",
        "question_text": "Explain the difference between WHERE and HAVING clauses in SQL, and how window functions like ROW_NUMBER() and RANK() work.",
        "reference_answer": "WHERE filters rows before aggregation, while HAVING filters groups after GROUP BY aggregation. Window functions compute metrics across a set of rows without collapsing them, using PARTITION BY and ORDER BY clauses.",
        "key_concepts": ["WHERE", "HAVING", "GROUP BY", "aggregation", "window functions", "ROW_NUMBER", "PARTITION BY"]
    },
    {
        "id": 14,
        "question_code": "DA002",
        "target_role": "Data Analyst",
        "category": "Data Modeling & Cleaning",
        "difficulty": "Intermediate",
        "question_text": "What steps do you take when handling missing data in an analytical dataset, and what is the difference between Mean, Median, and Mode imputation?",
        "reference_answer": "Handling missing data begins with understanding the missingness mechanism (MCAR, MAR, MNAR). Options include dropping rows, indicator variables, or imputation. Mean imputation is sensitive to outliers, Median is robust for skewed distributions, and Mode handles categorical data.",
        "key_concepts": ["missing data", "imputation", "Mean", "Median", "Mode", "skewness", "outliers"]
    },
    {
        "id": 15,
        "question_code": "DA003",
        "target_role": "Data Analyst",
        "category": "Statistical Analysis",
        "difficulty": "Advanced",
        "question_text": "Explain the difference between correlation and causation, and what a P-value represents in hypothesis testing.",
        "reference_answer": "Correlation measures linear association between variables without implying one causes the other. Causation requires controlled experiments. The P-value is the probability of observing results as extreme as the sample data under the null hypothesis.",
        "key_concepts": ["correlation", "causation", "P-value", "hypothesis testing", "null hypothesis", "statistical significance"]
    },

    # Software Developer (General / Custom)
    {
        "id": 16,
        "question_code": "SE001",
        "target_role": "Software Developer",
        "category": "Data Structures & Algorithms",
        "difficulty": "Intermediate",
        "question_text": "What is the difference between Array and LinkedList in memory layout, lookup speed, and insertion complexity?",
        "reference_answer": "Arrays store elements in contiguous memory, allowing O(1) random access via index, but resizing and insertions require O(n). LinkedLists store nodes with pointers anywhere in memory, offering O(1) insertions at head/tail but O(n) sequential lookup.",
        "key_concepts": ["Array", "LinkedList", "contiguous memory", "pointers", "O(1) lookup", "insertion complexity", "cache locality"]
    },
    {
        "id": 17,
        "question_code": "SE002",
        "target_role": "Software Developer",
        "category": "Software Engineering Principles",
        "difficulty": "Intermediate",
        "question_text": "Explain the SOLID design principles in object-oriented software engineering.",
        "reference_answer": "SOLID stands for Single Responsibility, Open/Closed (open for extension, closed for modification), Liskov Substitution, Interface Segregation, and Dependency Inversion. They ensure maintainable, decoupled, and testable code.",
        "key_concepts": ["SOLID", "Single Responsibility", "Open Closed", "Liskov Substitution", "Interface Segregation", "Dependency Inversion"]
    },
    {
        "id": 18,
        "question_code": "SE003",
        "target_role": "Software Developer",
        "category": "Version Control & CI/CD",
        "difficulty": "Intermediate",
        "question_text": "What is Git Rebase vs Git Merge, and how does a modern CI/CD pipeline ensure software deployment quality?",
        "reference_answer": "Merge creates a new commit preserving the complete commit history branch topology. Rebase rewrites commit history onto the target branch tip, creating a linear history. CI/CD runs automated unit tests, linters, and integration checks on each pull request before deployment.",
        "key_concepts": ["Git Merge", "Git Rebase", "commit history", "CI/CD pipeline", "automated testing", "linear history"]
    }
]

def prepare_interview_questions(target_role: str, extracted_skills: List[str] = None, count: int = 3) -> List[Dict[str, Any]]:
    """
    Selects and personalizes questions for a given role and skill set.
    """
    if extracted_skills is None:
        extracted_skills = []

    skills_lower = [s.lower() for s in extracted_skills]
    target_lower = target_role.strip().lower()

    # Find role matches
    role_matched = []
    for q in QUESTION_STORE:
        q_role = q["target_role"].lower()
        if q_role == target_lower or (target_lower in q_role) or (q_role in target_lower):
            role_matched.append(q)

    # If no direct role match (e.g. custom role), check skill relevance
    if not role_matched:
        for q in QUESTION_STORE:
            # Check if any concepts match candidate skills
            if any(concept.lower() in skills_lower for concept in q["key_concepts"]):
                role_matched.append(q)

    # Fallback to general Software Developer questions
    if not role_matched:
        role_matched = [q for q in QUESTION_STORE if q["target_role"] == "Software Developer"]

    # Select requested count
    selected = role_matched[:count]

    # Return formatted questions (without reference answers sent to candidate client)
    return selected
