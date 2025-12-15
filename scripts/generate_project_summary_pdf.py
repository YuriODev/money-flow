#!/usr/bin/env python3
"""Generate a 10-page PDF summary of the Money Flow project."""

import os
from datetime import datetime

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Colors
PRIMARY = HexColor("#6366f1")  # Indigo
SECONDARY = HexColor("#8b5cf6")  # Violet
ACCENT = HexColor("#06b6d4")  # Cyan
SUCCESS = HexColor("#10b981")  # Emerald
WARNING = HexColor("#f59e0b")  # Amber
DARK = HexColor("#1e293b")  # Slate 800
LIGHT = HexColor("#f1f5f9")  # Slate 100
MUTED = HexColor("#64748b")  # Slate 500


def create_styles():
    """Create custom styles for the document."""
    styles = getSampleStyleSheet()

    # Title style
    styles.add(
        ParagraphStyle(
            name="MainTitle",
            parent=styles["Title"],
            fontSize=42,
            textColor=PRIMARY,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
    )

    # Subtitle
    styles.add(
        ParagraphStyle(
            name="Subtitle",
            parent=styles["Normal"],
            fontSize=18,
            textColor=MUTED,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName="Helvetica",
        )
    )

    # Section header
    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=PRIMARY,
            spaceBefore=20,
            spaceAfter=15,
            fontName="Helvetica-Bold",
        )
    )

    # Subsection header
    styles.add(
        ParagraphStyle(
            name="SubsectionHeader",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=SECONDARY,
            spaceBefore=15,
            spaceAfter=10,
            fontName="Helvetica-Bold",
        )
    )

    # Body text
    styles.add(
        ParagraphStyle(
            name="BodyParagraph",
            parent=styles["Normal"],
            fontSize=11,
            textColor=DARK,
            spaceAfter=10,
            alignment=TA_JUSTIFY,
            leading=16,
        )
    )

    # Bullet point
    styles.add(
        ParagraphStyle(
            name="BulletItem",
            parent=styles["Normal"],
            fontSize=11,
            textColor=DARK,
            leftIndent=20,
            spaceAfter=5,
            leading=14,
        )
    )

    # Code/technical
    styles.add(
        ParagraphStyle(
            name="CodeBlock",
            parent=styles["Normal"],
            fontSize=10,
            textColor=DARK,
            backColor=LIGHT,
            fontName="Courier",
            leftIndent=10,
            rightIndent=10,
            spaceAfter=10,
        )
    )

    # Footer
    styles.add(
        ParagraphStyle(
            name="Footer", parent=styles["Normal"], fontSize=9, textColor=MUTED, alignment=TA_CENTER
        )
    )

    return styles


def create_table_style():
    """Create a modern table style."""
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("TOPPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), white),
            ("TEXTCOLOR", (0, 1), (-1, -1), DARK),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, MUTED),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT]),
            ("TOPPADDING", (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]
    )


def build_pdf():
    """Build the complete PDF document."""
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "Money_Flow_Project_Summary.pdf"
    )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1 * inch,
        leftMargin=1 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = create_styles()
    story = []

    # ==================== PAGE 1: COVER PAGE ====================
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("Money Flow", styles["MainTitle"]))
    story.append(Paragraph("Comprehensive Recurring Payment Management", styles["Subtitle"]))
    story.append(Spacer(1, 0.5 * inch))
    story.append(
        Paragraph(
            "A modern, AI-powered application for tracking all types of recurring "
            "financial obligations with natural language commands and intelligent insights.",
            styles["BodyParagraph"],
        )
    )
    story.append(Spacer(1, 1 * inch))

    # Project info box
    info_data = [
        ["Version", "2.0 (Money Flow Complete)"],
        ["Last Updated", datetime.now().strftime("%B %d, %Y")],
        ["Status", "Production Ready"],
        ["Tests", "400+ passing"],
    ]
    info_table = Table(info_data, colWidths=[2 * inch, 3 * inch])
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
                ("TEXTCOLOR", (1, 0), (1, -1), DARK),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, MUTED),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 15),
                ("RIGHTPADDING", (0, 0), (-1, -1), 15),
            ]
        )
    )
    story.append(info_table)
    story.append(PageBreak())

    # ==================== PAGE 2: EXECUTIVE SUMMARY ====================
    story.append(Paragraph("Executive Summary", styles["SectionHeader"]))

    story.append(Paragraph("Project Overview", styles["SubsectionHeader"]))
    story.append(
        Paragraph(
            "Money Flow (formerly Subscription Tracker) is a comprehensive recurring payment management "
            "application featuring an agentic interface that allows natural language commands to manage "
            "all types of recurring payments. The system combines a modern Next.js frontend with a FastAPI "
            "backend, PostgreSQL database, Redis caching, and Qdrant vector database for RAG capabilities.",
            styles["BodyParagraph"],
        )
    )

    story.append(Paragraph("Key Achievements", styles["SubsectionHeader"]))
    achievements = [
        "Multi-container Docker setup with 5 services (PostgreSQL, FastAPI, Next.js, Redis, Qdrant)",
        "Agentic interface with Claude Haiku 4.5 and XML-based prompting",
        "Support for 9 payment types (subscriptions, housing, utilities, debts, savings, etc.)",
        "RAG implementation complete with semantic search and conversation context",
        "Modern glassmorphism UI with Tailwind CSS v4 and Framer Motion animations",
        "Payment card tracking with funding chain support",
        "Import/Export functionality (JSON & CSV v2.0 format)",
        "400+ automated tests with comprehensive coverage",
    ]
    for item in achievements:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Business Value", styles["SubsectionHeader"]))
    story.append(
        Paragraph(
            "Money Flow provides users with a unified view of all recurring financial obligations, "
            "enabling better financial planning and management. The natural language interface reduces "
            "friction in data entry, while AI-powered insights help identify spending patterns and "
            "optimization opportunities.",
            styles["BodyParagraph"],
        )
    )
    story.append(PageBreak())

    # ==================== PAGE 3: TECH STACK ====================
    story.append(Paragraph("Technology Stack", styles["SectionHeader"]))

    story.append(Paragraph("Backend Technologies", styles["SubsectionHeader"]))
    backend_data = [
        ["Technology", "Version", "Purpose"],
        ["Python", "3.11+", "Core backend language"],
        ["FastAPI", "Latest", "REST API framework"],
        ["SQLAlchemy", "2.0", "Async ORM with PostgreSQL"],
        ["Pydantic", "v2", "Data validation and schemas"],
        ["PostgreSQL", "15", "Primary database"],
        ["Redis", "Latest", "Caching and session storage"],
        ["Qdrant", "1.7+", "Vector database for RAG"],
    ]
    backend_table = Table(backend_data, colWidths=[1.8 * inch, 1 * inch, 2.5 * inch])
    backend_table.setStyle(create_table_style())
    story.append(backend_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Frontend Technologies", styles["SubsectionHeader"]))
    frontend_data = [
        ["Technology", "Version", "Purpose"],
        ["Next.js", "16.0.5", "React framework with Turbopack"],
        ["React", "19.2.0", "UI component library"],
        ["TypeScript", "Strict", "Type-safe JavaScript"],
        ["Tailwind CSS", "4.1.17", "CSS-first utility classes"],
        ["Framer Motion", "12.23.24", "Animation library"],
        ["React Query", "5.90.11", "Server state management"],
    ]
    frontend_table = Table(frontend_data, colWidths=[1.8 * inch, 1 * inch, 2.5 * inch])
    frontend_table.setStyle(create_table_style())
    story.append(frontend_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("AI & Machine Learning", styles["SubsectionHeader"]))
    ai_data = [
        ["Technology", "Model/Version", "Purpose"],
        ["Claude API", "Haiku 4.5", "Intent classification & NL parsing"],
        ["Sentence Transformers", "all-MiniLM-L6-v2", "Text embeddings (384 dim)"],
        ["Qdrant", "1.7+", "Vector similarity search"],
    ]
    ai_table = Table(ai_data, colWidths=[2 * inch, 1.5 * inch, 2 * inch])
    ai_table.setStyle(create_table_style())
    story.append(ai_table)
    story.append(PageBreak())

    # ==================== PAGE 4: ARCHITECTURE ====================
    story.append(Paragraph("System Architecture", styles["SectionHeader"]))

    story.append(Paragraph("6-Layer Architecture", styles["SubsectionHeader"]))
    story.append(
        Paragraph(
            "The application follows Domain-Driven Design principles with a clean separation of concerns "
            "across six distinct layers:",
            styles["BodyParagraph"],
        )
    )

    layers_data = [
        ["Layer", "Technology", "Responsibility"],
        ["Presentation", "Next.js + React", "User interface, client state"],
        ["API Gateway", "FastAPI", "Request handling, validation"],
        ["Business Logic", "Python Services", "Domain logic, transactions"],
        ["Agentic", "Claude AI + RAG", "NL parsing, context, insights"],
        ["Data Access", "SQLAlchemy 2.0", "ORM, queries, relationships"],
        ["Database", "PostgreSQL + Qdrant", "Data persistence, vectors"],
    ]
    layers_table = Table(layers_data, colWidths=[1.3 * inch, 1.7 * inch, 2.5 * inch])
    layers_table.setStyle(create_table_style())
    story.append(layers_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Docker Services", styles["SubsectionHeader"]))
    docker_data = [
        ["Service", "Container", "Port", "Purpose"],
        ["Database", "subscription-db", "5433", "PostgreSQL data storage"],
        ["Backend", "subscription-backend", "8001", "FastAPI application"],
        ["Frontend", "subscription-frontend", "3001", "Next.js web app"],
        ["Cache", "subscription-redis", "6379", "Redis caching"],
        ["Vectors", "subscription-qdrant", "6333", "Qdrant vector DB"],
    ]
    docker_table = Table(docker_data, colWidths=[1.2 * inch, 1.8 * inch, 0.7 * inch, 1.8 * inch])
    docker_table.setStyle(create_table_style())
    story.append(docker_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Data Flow", styles["SubsectionHeader"]))
    story.append(
        Paragraph("1. User interacts via web UI or natural language chat", styles["BulletItem"])
    )
    story.append(
        Paragraph(
            "2. Frontend sends requests to Next.js API routes (proxied to backend)",
            styles["BulletItem"],
        )
    )
    story.append(
        Paragraph("3. FastAPI validates requests with Pydantic schemas", styles["BulletItem"])
    )
    story.append(
        Paragraph(
            "4. For NL commands: Parser + Claude AI extracts intent and entities",
            styles["BulletItem"],
        )
    )
    story.append(
        Paragraph(
            "5. RAG service provides conversation context and semantic search", styles["BulletItem"]
        )
    )
    story.append(
        Paragraph("6. Service layer executes business logic with database", styles["BulletItem"])
    )
    story.append(Paragraph("7. Response serialized and returned to frontend", styles["BulletItem"]))
    story.append(PageBreak())

    # ==================== PAGE 5: PAYMENT TYPES ====================
    story.append(Paragraph("Payment Types & Features", styles["SectionHeader"]))

    story.append(Paragraph("Supported Payment Types", styles["SubsectionHeader"]))
    story.append(
        Paragraph(
            "Money Flow supports 9 distinct payment types, each with specialized tracking fields:",
            styles["BodyParagraph"],
        )
    )

    payment_types_data = [
        ["Type", "Examples", "Special Features"],
        ["SUBSCRIPTION", "Netflix, Spotify, Claude AI", "Standard recurring tracking"],
        ["HOUSING", "Rent, mortgage", "Auto-classified from keywords"],
        ["UTILITY", "Electric, water, council tax", "Auto-classified from keywords"],
        ["PROFESSIONAL", "Therapist, coach, trainer", "Service provider tracking"],
        ["INSURANCE", "Health, AppleCare, vehicle", "Policy management"],
        ["DEBT", "Credit cards, loans, personal", "total_owed, remaining_balance, creditor"],
        ["SAVINGS", "Goals, regular transfers", "target_amount, current_saved, recipient"],
        ["TRANSFER", "Family support, gifts", "recipient tracking"],
        ["ONE_TIME", "Legal fees, single purchases", "Non-recurring with end_date"],
    ]
    payment_table = Table(payment_types_data, colWidths=[1.2 * inch, 2 * inch, 2.3 * inch])
    payment_table.setStyle(create_table_style())
    story.append(payment_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Payment Card System", styles["SubsectionHeader"]))
    story.append(
        Paragraph(
            "Track which card pays for each subscription with the payment card system:",
            styles["BodyParagraph"],
        )
    )
    card_features = [
        "Card types: Debit, Credit, Prepaid, Bank Account",
        "Visual card display with brand colors and logos",
        "Balance tracking per card (this month / next month)",
        "Funding chain support (e.g., PayPal funded by Monzo)",
        "Unassigned payment tracking and warnings",
    ]
    for item in card_features:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Multi-Currency Support", styles["SubsectionHeader"]))
    currency_data = [
        ["Currency", "Symbol", "Flag", "Status"],
        ["GBP", "£", "🇬🇧", "Default"],
        ["EUR", "€", "🇪🇺", "Supported"],
        ["USD", "$", "🇺🇸", "Supported"],
        ["UAH", "₴", "🇺🇦", "Supported"],
    ]
    currency_table = Table(currency_data, colWidths=[1.3 * inch, 1 * inch, 1 * inch, 1.5 * inch])
    currency_table.setStyle(create_table_style())
    story.append(currency_table)
    story.append(PageBreak())

    # ==================== PAGE 6: AI AGENT ====================
    story.append(Paragraph("AI Agent & Natural Language Interface", styles["SectionHeader"]))

    story.append(Paragraph("Agentic Architecture", styles["SubsectionHeader"]))
    story.append(
        Paragraph(
            "The AI agent uses Claude Haiku 4.5 for fast, cost-effective intent classification and "
            "entity extraction. The system implements dual-mode parsing with AI as primary and regex "
            "patterns as fallback for reliability.",
            styles["BodyParagraph"],
        )
    )

    story.append(Paragraph("Agent Components", styles["SubsectionHeader"]))
    agent_data = [
        ["Component", "File", "Purpose"],
        ["CommandParser", "src/agent/parser.py", "NL → intent + entities"],
        ["AgentExecutor", "src/agent/executor.py", "Intent → service calls"],
        ["PromptLoader", "src/agent/prompt_loader.py", "XML prompt management"],
        ["ConversationalAgent", "src/agent/conversational_agent.py", "Tool-use based agent"],
    ]
    agent_table = Table(agent_data, colWidths=[1.6 * inch, 2.2 * inch, 1.7 * inch])
    agent_table.setStyle(create_table_style())
    story.append(agent_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Example Commands", styles["SubsectionHeader"]))
    commands = [
        '"Add Netflix for £15.99 monthly" → Creates subscription',
        '"Add rent payment £1137.50 monthly" → Creates housing payment',
        '"Add debt to John £500, paying £50 monthly" → Creates debt with creditor',
        '"Add savings goal £10000 for holiday" → Creates savings with target',
        '"I paid £200 off my credit card" → Updates debt balance',
        '"How much am I spending per month?" → Returns summary',
        '"What\'s due this week?" → Lists upcoming payments',
        '"Show my total debt" → Aggregates debt balances',
    ]
    for cmd in commands:
        story.append(Paragraph(f"• {cmd}", styles["BulletItem"]))

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("XML-Based Prompting", styles["SubsectionHeader"]))
    story.append(
        Paragraph(
            "Prompts are organized in structured XML files for maintainability:",
            styles["BodyParagraph"],
        )
    )
    prompt_files = [
        "system.xml - System role and capabilities",
        "command_patterns.xml - Intent patterns with examples",
        "currency.xml - Currency detection configuration",
        "response_templates.xml - Response format templates",
    ]
    for item in prompt_files:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))
    story.append(PageBreak())

    # ==================== PAGE 7: RAG IMPLEMENTATION ====================
    story.append(Paragraph("RAG Implementation", styles["SectionHeader"]))

    story.append(Paragraph("What is RAG?", styles["SubsectionHeader"]))
    story.append(
        Paragraph(
            "RAG (Retrieval-Augmented Generation) enhances the AI agent with memory and context "
            "awareness. The agent can remember conversations, search semantically, and provide "
            "intelligent insights based on historical data.",
            styles["BodyParagraph"],
        )
    )

    story.append(Paragraph("RAG Services", styles["SubsectionHeader"]))
    rag_data = [
        ["Service", "Purpose", "Status"],
        ["EmbeddingService", "Generate text embeddings (384-dim)", "✅ Complete"],
        ["VectorStore", "Qdrant CRUD + similarity search", "✅ Complete"],
        ["RAGService", "Context retrieval, reference resolution", "✅ Complete"],
        ["ConversationService", "Session management, history", "✅ Complete"],
        ["InsightsService", "Spending patterns, recommendations", "✅ Complete"],
        ["HistoricalQueryService", "Temporal parsing, date queries", "✅ Complete"],
        ["CacheService", "Redis embedding cache", "✅ Complete"],
        ["RAGAnalyticsService", "Query monitoring, metrics", "✅ Complete"],
    ]
    rag_table = Table(rag_data, colWidths=[1.8 * inch, 2.5 * inch, 1.2 * inch])
    rag_table.setStyle(create_table_style())
    story.append(rag_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Key RAG Features", styles["SubsectionHeader"]))
    rag_features = [
        "Reference Resolution: 'Cancel it' → 'Cancel Netflix' (from context)",
        "Semantic Note Search: Find subscriptions by meaning, not just keywords",
        "Conversation Memory: Multi-turn conversations with session tracking",
        "Hybrid Search: Combines semantic similarity with keyword boosting",
        "Spending Insights: Trend analysis, category breakdown, predictions",
        "Historical Queries: 'What did I add last month?' with temporal parsing",
        "Embedding Cache: 60%+ cache hit rate for performance",
        "Analytics Dashboard: Query latency tracking, health monitoring",
    ]
    for item in rag_features:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Architecture Decisions", styles["SubsectionHeader"]))
    decisions = [
        "Vector DB: Qdrant (self-hosted, Docker-native, excellent filtering)",
        "Embedding Model: all-MiniLM-L6-v2 (local, 50ms inference, 80MB)",
        "Caching: Redis with TTL-based expiration",
        "Context: Hybrid approach (recent turns + semantic search)",
        "Data Isolation: User-level filtering on all queries",
    ]
    for item in decisions:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))
    story.append(PageBreak())

    # ==================== PAGE 8: FRONTEND & UI ====================
    story.append(Paragraph("Frontend & User Interface", styles["SectionHeader"]))

    story.append(Paragraph("Modern Design System", styles["SubsectionHeader"]))
    story.append(
        Paragraph(
            "The frontend uses cutting-edge 2025 CSS features with Tailwind CSS v4, featuring a "
            "glassmorphism design language with OKLCH color space for perceptually uniform colors.",
            styles["BodyParagraph"],
        )
    )

    design_features = [
        "Glassmorphism cards with backdrop blur and subtle borders",
        "OKLCH color definitions for consistent lightness perception",
        "Framer Motion animations with spring physics",
        "Scroll-driven animations and CSS anchor positioning",
        "Container style queries and :has() parent selectors",
        "Service icon library with 70+ popular subscription icons",
        "Brand colors for recognized services (Netflix, Spotify, etc.)",
    ]
    for item in design_features:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Key Components", styles["SubsectionHeader"]))
    components_data = [
        ["Component", "Purpose"],
        ["Header", "Navigation, branding with gradient glow"],
        ["StatsPanel", "Spending summary, debt/savings progress"],
        ["SubscriptionList", "Payment list with service icons, filtering"],
        ["AddSubscriptionModal", "Smart form with service suggestions"],
        ["PaymentCalendar", "Calendar view of upcoming payments"],
        ["CardsDashboard", "Payment card management, balance tracking"],
        ["AgentChat", "Natural language interface with markdown"],
        ["ImportExportModal", "JSON/CSV import and export"],
    ]
    components_table = Table(components_data, colWidths=[2 * inch, 3.5 * inch])
    components_table.setStyle(create_table_style())
    story.append(components_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Service Icon Library", styles["SubsectionHeader"]))
    story.append(
        Paragraph(
            "The application includes icons for 70+ popular services across categories:",
            styles["BodyParagraph"],
        )
    )
    icon_categories = [
        "Streaming: Netflix, Disney+, Hulu, HBO Max, Apple TV+, YouTube",
        "Music: Spotify, Apple Music, Tidal, Deezer, Amazon Music",
        "Gaming: Xbox Game Pass, PlayStation Plus, Steam, GeForce Now",
        "Productivity: Microsoft 365, Google One, Notion, Slack, Figma",
        "Development: GitHub, GitLab, JetBrains, Vercel, AWS, Heroku",
        "AI Tools: ChatGPT Plus, Claude Pro, Midjourney, Grammarly",
    ]
    for item in icon_categories:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))
    story.append(PageBreak())

    # ==================== PAGE 9: API ENDPOINTS ====================
    story.append(Paragraph("API Endpoints", styles["SectionHeader"]))

    story.append(Paragraph("Subscriptions API", styles["SubsectionHeader"]))
    subs_api_data = [
        ["Method", "Endpoint", "Description"],
        ["GET", "/api/subscriptions", "List all (with payment_type filter)"],
        ["GET", "/api/subscriptions/{id}", "Get single subscription"],
        ["POST", "/api/subscriptions", "Create subscription"],
        ["PUT", "/api/subscriptions/{id}", "Update subscription"],
        ["DELETE", "/api/subscriptions/{id}", "Delete subscription"],
        ["GET", "/api/subscriptions/summary", "Spending summary by period"],
        ["GET", "/api/subscriptions/upcoming", "Upcoming payments"],
    ]
    subs_table = Table(subs_api_data, colWidths=[0.8 * inch, 2.3 * inch, 2.4 * inch])
    subs_table.setStyle(create_table_style())
    story.append(subs_table)

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Import/Export API", styles["SubsectionHeader"]))
    export_api_data = [
        ["Method", "Endpoint", "Description"],
        ["GET", "/api/subscriptions/export/json", "Export as JSON v2.0"],
        ["GET", "/api/subscriptions/export/csv", "Export as CSV v2.0"],
        ["POST", "/api/subscriptions/import/json", "Import from JSON"],
        ["POST", "/api/subscriptions/import/csv", "Import from CSV"],
    ]
    export_table = Table(export_api_data, colWidths=[0.8 * inch, 2.5 * inch, 2.2 * inch])
    export_table.setStyle(create_table_style())
    story.append(export_table)

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Cards & Analytics API", styles["SubsectionHeader"]))
    other_api_data = [
        ["Method", "Endpoint", "Description"],
        ["GET", "/api/cards", "List payment cards"],
        ["POST", "/api/cards", "Create payment card"],
        ["GET", "/api/cards/balance-summary", "Card balance summary"],
        ["GET", "/api/analytics/daily", "Daily RAG metrics"],
        ["GET", "/api/analytics/health", "System health check"],
        ["GET", "/api/insights/", "Complete spending insights"],
        ["POST", "/api/insights/historical", "Historical query with parsing"],
        ["POST", "/api/search/notes", "Semantic note search"],
        ["POST", "/api/agent/execute", "Execute NL command"],
    ]
    other_table = Table(other_api_data, colWidths=[0.8 * inch, 2.5 * inch, 2.2 * inch])
    other_table.setStyle(create_table_style())
    story.append(other_table)
    story.append(PageBreak())

    # ==================== PAGE 10: METRICS & STATUS ====================
    story.append(Paragraph("Project Metrics & Status", styles["SectionHeader"]))

    story.append(Paragraph("Development Metrics", styles["SubsectionHeader"]))
    metrics_data = [
        ["Metric", "Value", "Notes"],
        ["Total Tests", "400+", "Unit + Integration"],
        ["Python Files", "51+", "Backend codebase"],
        ["TypeScript Files", "18+", "Frontend codebase"],
        ["API Endpoints", "45+", "REST API coverage"],
        ["Database Migrations", "8", "Alembic managed"],
        ["Payment Types", "9", "Full Money Flow coverage"],
        ["Service Icons", "70+", "Popular subscriptions"],
        ["Lines of Code", "~7,500+", "Python backend"],
    ]
    metrics_table = Table(metrics_data, colWidths=[1.8 * inch, 1.2 * inch, 2.5 * inch])
    metrics_table.setStyle(create_table_style())
    story.append(metrics_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Completion Status", styles["SubsectionHeader"]))
    status_data = [
        ["Feature", "Status", "Phase"],
        ["Core CRUD Operations", "✅ Complete", "Initial"],
        ["AI Agent (Claude Haiku)", "✅ Complete", "Initial"],
        ["Multi-Currency Support", "✅ Complete", "Initial"],
        ["Money Flow Refactor", "✅ Complete", "Phase 1-3"],
        ["RAG Implementation", "✅ Complete", "Phase 1-4"],
        ["Payment Cards System", "✅ Complete", "Enhancement"],
        ["Import/Export v2.0", "✅ Complete", "Enhancement"],
        ["Modern UI (Tailwind v4)", "✅ Complete", "Polish"],
        ["GCP Deployment", "⏳ Planned", "Future"],
        ["User Authentication", "⏳ Planned", "Future"],
    ]
    status_table = Table(status_data, colWidths=[2.2 * inch, 1.3 * inch, 2 * inch])
    status_table.setStyle(create_table_style())
    story.append(status_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Access URLs (Local Development)", styles["SubsectionHeader"]))
    urls_data = [
        ["Service", "URL"],
        ["Frontend", "http://localhost:3001"],
        ["Backend API", "http://localhost:8001"],
        ["API Documentation", "http://localhost:8001/docs"],
        ["Database", "localhost:5433"],
        ["Qdrant Dashboard", "http://localhost:6333/dashboard"],
    ]
    urls_table = Table(urls_data, colWidths=[2 * inch, 3.5 * inch])
    urls_table.setStyle(create_table_style())
    story.append(urls_table)

    story.append(Spacer(1, 0.5 * inch))
    story.append(
        Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')} | Money Flow v2.0",
            styles["Footer"],
        )
    )

    # Build the PDF
    doc.build(story)
    print(f"PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    build_pdf()
