# Architecture Diagrams

This document contains visual diagrams for the Azure Doc Agent architecture.

## System Architecture

\`\`\`mermaid
graph TB
    subgraph "User Interface"
        UI[React Frontend<br/>SSE Streaming]
    end
    
    subgraph "Backend Services"
        API[FastAPI Server<br/>REST API + SSE]
        Agent[Azure Doc Agent<br/>Microsoft Agent Framework]
    end
    
    subgraph "Skill System"
        Registry[Skill Registry<br/>Metadata Cache]
        Matcher[LLM Skill Matcher<br/>91.3% Accuracy]
        Injector[Skill Injector<br/>Progressive Disclosure]
    end
    
    subgraph "MCP Integration"
        MCPClient[MCP Client<br/>Multi-Server Support]
        MCP1[Microsoft Learn MCP<br/>Docs + Code Samples]
        MCP2[GitHub MCP<br/>Future]
        MCP3[Internal Docs MCP<br/>Future]
    end
    
    subgraph "Skills Storage"
        Skill1["microsoft-docs<br/>SKILL.md"]
        Skill2["microsoft-code-reference<br/>SKILL.md"]
        Skill3["Future Skills<br/>SKILL.md"]
    end
    
    UI -->|HTTP/SSE| API
    API --> Agent
    Agent --> Registry
    Agent --> Matcher
    Agent --> Injector
    Agent --> MCPClient
    
    Registry -.->|Discover| Skill1
    Registry -.->|Discover| Skill2
    Registry -.->|Discover| Skill3
    
    Matcher -->|Select| Skill1
    Matcher -->|Select| Skill2
    
    Injector -.->|Load Full Content| Skill1
    Injector -.->|Load Full Content| Skill2
    
    MCPClient -->|Connect| MCP1
    MCPClient -.->|Future| MCP2
    MCPClient -.->|Future| MCP3
    
    style Agent fill:#4CAF50
    style Matcher fill:#2196F3
    style MCPClient fill:#FF9800
\`\`\`

## Query Processing Flow

\`\`\`mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Agent
    participant LLMMatcher
    participant SkillInjector
    participant MCPClient
    participant MCP
    
    User->>Frontend: "给我Azure Functions代码示例"
    Frontend->>API: POST /chat/stream
    API->>Agent: chat_stream_with_thinking()
    
    Note over Agent,LLMMatcher: Step 1: Skill Matching
    Agent->>LLMMatcher: match_skills(query, available_skills)
    LLMMatcher-->>Agent: microsoft-code-reference ✓
    
    Frontend-->>User: 💭 LLM matched skill: microsoft-code-reference
    
    Note over Agent,SkillInjector: Step 2: Progressive Disclosure
    Agent->>SkillInjector: activate_skill("microsoft-code-reference")
    SkillInjector-->>Agent: Full SKILL.md content
    
    Frontend-->>User: 📚 Loading skill instructions...
    
    Note over Agent,MCPClient: Step 3: Agent Processing
    Agent->>Agent: Inject SKILL.md into context
    Agent->>Agent: run_stream(context_message)
    
    Frontend-->>User: 🤖 Generating response...
    
    Note over Agent,MCP: Step 4: Tool Execution
    Agent->>MCPClient: Based on SKILL.md guidance
    MCPClient->>MCP: microsoft_code_sample_search("Azure Functions Python")
    MCP-->>MCPClient: Code examples
    MCPClient-->>Agent: Tool results
    
    Agent-->>API: Stream text chunks
    API-->>Frontend: SSE events
    Frontend-->>User: Display response with code examples
\`\`\`

## Progressive Disclosure Design

\`\`\`mermaid
graph LR
    subgraph "Initialization (Once)"
        A1[Load SKILL.md<br/>Metadata Only] -->|Name + Description| A2[Skill Registry]
        A3[Connect MCP Servers] --> A4[Get All Tools]
        A4 --> A5[Register ALL Tools<br/>to Agent]
        A2 -.->|Available for matching| A5
    end
    
    subgraph "Query Processing (Per Query)"
        B1[User Query] --> B2{LLM Skill<br/>Matching}
        B2 -->|Match Found| B3[Load Full SKILL.md]
        B2 -->|No Match| B4[Generic Response]
        B3 --> B5[Inject SKILL.md<br/>as Instructions]
        B5 --> B6[Agent Decides<br/>Which Tools to Use]
        B6 --> B7[Execute Tools]
        B7 --> B8[Generate Response]
    end
    
    A5 -.->|Tools Available| B6
    
    style A5 fill:#4CAF50
    style B3 fill:#2196F3
    style B6 fill:#FF9800
\`\`\`

## Multi-MCP Server Extensibility

\`\`\`mermaid
graph TB
    subgraph "Agent Core"
        Agent[Agent<br/>All Tools Registered]
    end
    
    subgraph "Skill 1: microsoft-docs"
        S1[SKILL.md] -->|Guides| T1["Use: microsoft_docs_search<br/>Use: microsoft_docs_fetch"]
    end
    
    subgraph "Skill 2: microsoft-code-reference"
        S2[SKILL.md] -->|Guides| T2["Use: microsoft_code_sample_search"]
    end
    
    subgraph "Skill 3: github-search (Future)"
        S3[SKILL.md] -->|Guides| T3["Use: github_search_repos<br/>Use: github_get_code"]
    end
    
    subgraph "MCP Server 1"
        MCP1[Microsoft Learn MCP] -.->|Provides| T1
        MCP1 -.->|Provides| T2
    end
    
    subgraph "MCP Server 2 (Future)"
        MCP2[GitHub MCP] -.->|Provides| T3
    end
    
    Agent -->|Has| T1
    Agent -->|Has| T2
    Agent -->|Has| T3
    
    S1 -.->|Injected when matched| Agent
    S2 -.->|Injected when matched| Agent
    S3 -.->|Injected when matched| Agent
    
    style Agent fill:#4CAF50
    style S1 fill:#2196F3
    style S2 fill:#2196F3
    style S3 fill:#2196F3
\`\`\`

## Session Management Architecture

\`\`\`mermaid
graph TB
    subgraph "Frontend State"
        S1["Session 1<br/>Messages: [m1, m2, m3]"]
        S2["Session 2<br/>Messages: [m4, m5]"]
        S3["Session 3<br/>Messages: [m6]"]
        
        Map["SessionMessages Map<br/>key: session_id<br/>value: Message[]"]
    end
    
    subgraph "User Actions"
        Switch["s4"] -->|Save current| Map
        Switch -->|Load target| Map
        Create["s5"] -->|New ID| Map
        Delete["s6"] -->|Remove| Map
    end
    
    Map -->|Store| S1
    Map -->|Store| S2
    Map -->|Store| S3
    
    S1 -.->|Restore| Display["s7"]
    S2 -.->|Restore| Display
    S3 -.->|Restore| Display
    
    style Map fill:#4CAF50
    style Switch fill:#2196F3
\`\`\`

## Skill Matching Comparison

\`\`\`mermaid
flowchart LR
    subgraph "Traditional Approach"
        Q1["Query:<br/>\"我想了解Cosmos DB\""] --> K1{Keyword<br/>Match}
        K1 -->|Not in keywords| F1["❌ No Match<br/>70% Accuracy"]
    end
    
    subgraph "LLM Approach"
        Q2["Query:<br/>\"我想了解Cosmos DB\""] --> L1{LLM<br/>Intent Analysis}
        L1 -->|"User wants to learn"| S1["✓ microsoft-docs<br/>91.3% Accuracy"]
    end
    
    subgraph "Hybrid (Current)"
        Q3["Query"] --> L2{LLM Match}
        L2 -->|Success| S2["Use LLM Result"]
        L2 -->|Fail| K2{Keyword Fallback}
        K2 --> S3["Use Keyword Result"]
    end
    
    style S1 fill:#4CAF50
    style S2 fill:#4CAF50
    style S3 fill:#FF9800
    style F1 fill:#f44336
\`\`\`
