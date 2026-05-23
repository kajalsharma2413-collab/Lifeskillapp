# Life Skills Learning App

A comprehensive web application designed to help school-aged children (ages 8-14) develop essential life skills through interactive learning, AI-powered assistance, and gamified experiences.

## 🎯 Overview

The Life Skills Learning App empowers children to develop crucial life competencies including safety awareness, financial literacy, communication skills, and problem-solving abilities. Built with modern AI technologies, the app provides personalized learning experiences through interactive activities, voice coaching, and intelligent chatbot assistance.

### Target Audience

- **Primary Users**: Children aged 8-14 years
- **Secondary Users**: Parents and guardians for monitoring and support
- **Administrators**: Content managers and system administrators

## 🏗️ Architecture & Technology Stack

### Backend Framework

- **FastAPI**: High-performance Python web framework
- **Python 3.11+**: Core runtime environment
- **Uvicorn**: ASGI server for production deployment

### Database & Authentication

- **Firebase**:
  - Authentication (JWT tokens, role-based access)
  - Firestore NoSQL database
  - Real-time data synchronization
- **Parent-Child Linking**: Secure code-based family account management

### AI & Machine Learning

- **Google Generative AI (Gemini 1.5 Flash)**: Primary LLM for chatbot interactions
- **LangChain**: AI application framework for conversation management
- **LangGraph**: State machine for complex AI workflows
- **HuggingFace Transformers**: Sentence embeddings (`all-MiniLM-L6-v2`)
- **Pinecone**: Vector database for RAG (Retrieval Augmented Generation)
- **Tavily Search**: Child-safe web search integration

### Voice & Communication

- **VAPI**: Voice API integration for speech-based interactions
- **Voice Coaches**: Specialized AI personas for storytelling and debate practice

### Development Tools

- **Ruff**: Code formatting and linting
- **Pre-commit**: Git hooks for code quality
- **Loguru**: Advanced logging system
- **Pydantic**: Data validation and serialization

## 🎮 Core Features

### 1. Life Skills Modules

#### Safety Skills (`/safetyskills`)

- Emergency response training
- Personal safety awareness
- Digital safety education
- Interactive safety scenarios

#### Financial Literacy (`/financeskills`)

- Money management fundamentals
- Saving and budgeting concepts
- Needs vs. wants decision-making
- Interactive spending simulations

#### Communication Skills (`/conversation`)

- Voice communication practice
- Storytelling exercises
- Debate coaching
- Active listening training

#### Problem Solving (`/problem-solving`)

- Critical thinking development
- Step-by-step problem analysis
- Creative solution generation
- Logic puzzle challenges

#### Basic Manners (Coming Soon)

- Social etiquette training
- Empathy development
- Hygiene education
- Respectful behavior practice

### 2. AI-Powered Learning

#### RAG Chatbot System

- **Educational Assistant**: Answers children's questions using curated knowledge base
- **Context-Aware Responses**: Age-appropriate explanations (8-14 years)
- **Safety-First Approach**: Content filtering and appropriate topic guidance
- **Multi-Modal Input**: Text and voice interaction support

#### Mentor Chatbot

- **Personalized Guidance**: Adaptive responses based on user progress
- **Emotional Support**: Encouraging and positive reinforcement
- **Learning Path Optimization**: Customized skill development recommendations

#### Voice Communication Features

- **Storytelling Coach**: Interactive narrative experiences with voice prompts
- **Debate Coach**: Structured argument practice for ages 8-14
- **Real-time Feedback**: Voice analysis and improvement suggestions

### 3. Gamification System

#### Points & Rewards

- **Activity-Based Scoring**: Points for quiz completion, skill practice
- **Achievement Tracking**: Progress monitoring across all skill areas
- **Milestone Recognition**: Special rewards for consistent engagement

#### Badge System

- **Skill-Specific Badges**: Recognition for mastery in different areas
- **Progress Badges**: Incremental achievement acknowledgments
- **Special Achievement Badges**: Exceptional performance recognition

#### Leaderboards & Social Features

- **Peer Comparison**: Age-appropriate competitive elements
- **Family Leaderboards**: Parent-child shared achievement tracking
- **Skill-Based Rankings**: Category-specific performance metrics

### 4. User Management

#### Role-Based Access Control

- **Children (USER role)**: Full learning access with parental oversight
- **Parents (PARENT role)**: Child monitoring, progress tracking, account management
- **Administrators (ADMIN role)**: System management, content creation, analytics

#### Parent-Child Relationships

- **Secure Linking**: Unique 6-character codes for family account connection
- **Privacy Protection**: Age-appropriate data handling and parental controls
- **Emergency Contacts**: Safety information management

#### Profile Management

- **Age Verification**: Automatic age calculation and grade-level assignment
- **Avatar Customization**: Child-friendly profile personalization
- **Preference Settings**: Learning style and content preferences

### 5. Assessment & Progress Tracking

#### Dynamic Quiz Generation

- **AI-Generated Questions**: Contextual quizzes based on learning content
- **Adaptive Difficulty**: Questions scaled to user age and skill level
- **Immediate Feedback**: Real-time performance assessment

#### Progress Analytics

- **Skill Mastery Tracking**: Competency measurement across all areas
- **Learning Velocity**: Pace of skill acquisition monitoring
- **Engagement Metrics**: Time spent, activities completed, consistency tracking

#### Parental Dashboard

- **Child Progress Overview**: Comprehensive development monitoring
- **Achievement Notifications**: Real-time updates on child accomplishments
- **Recommendation Engine**: Suggested activities based on performance gaps

## 📁 Project Structure

```
app/
├── api/
│   ├── dependencies/
│   │   ├── ai/                    # AI service dependencies
│   │   │   ├── diary_summarizer.py
│   │   │   ├── mentor_chatbot/    # Mentor AI system
│   │   │   └── rag_chatbot/       # RAG chatbot system
│   │   └── auth.py                # Authentication dependencies
│   └── v1/                        # API version 1 endpoints
│       ├── admin.py               # Admin management APIs
│       ├── admin_dashboard.py     # Admin analytics dashboard
│       ├── ai.py                  # General AI endpoints
│       ├── auth.py                # Authentication endpoints
│       ├── chatbot.py             # Chatbot interaction APIs
│       ├── diary.py               # Learning diary features
│       ├── finance.py             # Financial literacy APIs
│       ├── mentor_chatbot.py      # Mentor chatbot endpoints
│       ├── parent.py              # Parent management APIs
│       ├── problem_solving.py     # Problem-solving activities
│       ├── public.py              # Public/unauthenticated endpoints
│       ├── quiz.py                # Quiz generation and management
│       ├── rag_chat.py            # RAG chatbot endpoints
│       ├── safety.py              # Safety skills APIs
│       ├── skills.py              # General skills management
│       ├── users.py               # User management APIs
│       └── vapi.py                # Voice API integration
├── config/
│   ├── firebase.py                # Firebase configuration
│   ├── logging.py                 # Logging configuration
│   └── settings.py                # Application settings
├── models/                        # Data models
│   ├── base.py                    # Base model definitions
│   ├── skill.py                   # Skill-related models
│   └── user.py                    # User models
├── schemas/                       # Pydantic schemas
│   ├── auth.py                    # Authentication schemas
│   ├── base.py                    # Base response schemas
│   ├── diary.py                   # Diary feature schemas
│   ├── safety.py                  # Safety skills schemas
│   ├── skill.py                   # Skill management schemas
│   └── user.py                    # User data schemas
├── services/                      # Business logic services
│   ├── ai.py                      # AI service orchestration
│   ├── auth.py                    # Authentication services
│   ├── firebase.py                # Firebase integration
│   └── user.py                    # User management services
├── utils/                         # Utility functions
│   ├── exceptions.py              # Custom exception handling
│   ├── pagination.py              # Pagination utilities
│   ├── quiz_utils.py              # Quiz generation utilities
│   ├── security.py                # Security utilities
│   └── skill_tracking.py          # Skill progress tracking
└── main.py                        # Application entry point
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.11 or higher**
- **Firebase Project** with Authentication and Firestore enabled
- **Google Cloud API Key** for Generative AI
- **Pinecone Account** for vector database
- **VAPI Account** for voice features (optional)

### Environment Variables

Create a `.env` file in the project root:

```env
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token

# AI Services
GOOGLE_API_KEY=your-google-generative-ai-key
PINECONE_API_KEY=your-pinecone-api-key
TAVILY_API_KEY=your-tavily-search-key
LANGSMITH_API_KEY=your-langsmith-key (optional)

# Voice API
VAPI_TOKEN=your-vapi-token

# Application Settings
SECRET_KEY=your-super-secret-jwt-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
```

### Installation

1. **Clone the repository:**

```bash
git clone <repository-url>
cd life-skills-app
```

2. **Install dependencies using uv (recommended):**

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

3. **Alternative installation with pip:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

4. **Setup pre-commit hooks (for development):**

```bash
pre-commit install
```

### Database Setup

1. **Firebase Configuration:**

   - Create a Firebase project at <https://console.firebase.google.com>
   - Enable Authentication (Email/Password, Google Sign-In)
   - Enable Firestore Database
   - Download service account key and configure environment variables

2. **Pinecone Setup:**
   - Create account at <https://pinecone.io>
   - Create index with dimension 384 (for sentence-transformers/all-MiniLM-L6-v2)
   - Configure API key in environment variables

### Running the Application

1. **Development Server:**

```bash
# Using uv
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Using standard Python
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Production Server:**

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

3. **Access the application:**
   - API Documentation: <http://localhost:8000/docs>
   - Alternative Docs: <http://localhost:8000/redoc>
   - Health Check: <http://localhost:8000/api/v1/public/health>

## 📊 API Documentation

### Authentication Endpoints

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/auth/refresh` - Token refresh
- `DELETE /api/v1/auth/delete-account` - Account deletion

### User Management

- `GET /api/v1/users/me` - Current user information
- `PUT /api/v1/users/me` - Update user profile
- `GET /api/v1/users/leaderboard` - User rankings
- `GET /api/v1/users/scoring-table` - Detailed scoring information

### Skills & Learning

- `GET /api/v1/skills` - Available skill modules
- `POST /api/v1/quiz/generate` - Generate skill-based quizzes
- `POST /api/v1/quiz/submit` - Submit quiz responses
- `GET /api/v1/safety/scenarios` - Safety skill scenarios
- `GET /api/v1/finance/levels` - Financial literacy levels

### AI Interactions

- `POST /api/v1/rag-chat/ask` - RAG chatbot queries
- `POST /api/v1/mentor-chatbot/chat` - Mentor AI conversations
- `POST /api/v1/ai/generate-response` - General AI assistance

### Parent Features

- `POST /api/v1/parent/generate-code` - Generate child linking code
- `POST /api/v1/parent/link-child` - Link child account
- `GET /api/v1/parent/children` - View linked children
- `GET /api/v1/parent/child/{child_id}/progress` - Child progress tracking

### Administrative

- `GET /api/v1/admin/dashboard/stats` - System statistics
- `GET /api/v1/admin/users` - User management
- `POST /api/v1/admin/badges` - Badge creation
- `GET /api/v1/admin/analytics` - Usage analytics

## 🔒 Security Features

### Authentication & Authorization

- **Firebase Authentication**: Secure JWT token validation
- **Role-Based Access Control**: Child, Parent, and Admin permissions
- **Session Management**: Automatic token refresh and expiration

### Data Protection

- **Age-Appropriate Content Filtering**: AI responses tailored for children
- **Parental Controls**: Child account oversight and management
- **Privacy Compliance**: COPPA-compliant data handling practices

### Content Safety

- **AI Content Moderation**: Inappropriate content detection and filtering
- **Safe Search Integration**: Child-safe web search results only
- **Emergency Contact System**: Quick access to trusted adults

## 🎨 Frontend Integration

### Expected Frontend Technologies

- **React/Vue/Angular**: Modern SPA framework
- **Firebase SDK**: Client-side authentication
- **WebRTC**: Voice interaction capabilities
- **Progressive Web App**: Mobile-responsive design

### API Integration Guidelines

- **Base URL**: Use environment-specific API base URLs
- **Authentication**: Include Firebase ID tokens in Authorization headers
- **Error Handling**: Implement comprehensive error response handling
- **Loading States**: Provide user feedback during AI response generation

### Key Frontend Routes

- `/dashboard` - Main user dashboard
- `/safetyskills` - Safety skill module
- `/financeskills` - Financial literacy module
- `/conversation` - Communication skills practice
- `/problem-solving` - Problem-solving activities
- `/parent-dashboard` - Parent monitoring interface

## 🧪 Testing

### Running Tests

```bash
# Unit tests
uv run pytest tests/unit/

# Integration tests
uv run pytest tests/integration/

# All tests with coverage
uv run pytest --cov=app tests/
```

### Test Categories

- **Authentication Tests**: Login, registration, token validation
- **API Endpoint Tests**: All CRUD operations and business logic
- **AI Service Tests**: Chatbot responses, quiz generation
- **Database Tests**: Firebase integration and data persistence

## 📈 Monitoring & Analytics

### Application Metrics

- **User Engagement**: Daily/monthly active users, session duration
- **Learning Progress**: Skill completion rates, quiz performance
- **AI Interaction**: Chatbot usage, response accuracy
- **System Performance**: API response times, error rates

### Logging Configuration

- **Structured Logging**: JSON-formatted logs with Loguru
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Request Tracing**: Unique request IDs for debugging
- **Performance Monitoring**: Response time and resource usage tracking

## 🚀 Deployment

### Production Considerations

- **Environment Variables**: Secure secret management
- **Database Scaling**: Firestore capacity planning
- **AI Service Limits**: Google API quota management
- **CDN Configuration**: Static asset optimization

### Recommended Infrastructure

- **Container Deployment**: Docker with multi-stage builds
- **Load Balancing**: Multiple FastAPI instances
- **Monitoring**: Application performance monitoring (APM)
- **Backup Strategy**: Regular database backups

### Scaling Guidelines

- **Horizontal Scaling**: Multiple worker processes
- **Caching Strategy**: Redis for session and response caching
- **Database Optimization**: Firestore index optimization
- **AI Service Optimization**: Response caching for common queries

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes following code style guidelines
4. Run tests and ensure all pass
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

### Code Standards

- **Python Style**: Follow PEP 8 with Ruff formatting
- **Type Hints**: Use type annotations throughout
- **Documentation**: Document all functions and classes
- **Testing**: Maintain high test coverage (>80%)

### Commit Message Format

```
type(scope): brief description

Detailed explanation if necessary

- Bullet points for multiple changes
- Reference issue numbers: #123
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Support & Community

### Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Comprehensive API documentation at `/docs`
- **Community Forum**: Discussion and Q&A
- **Email Support**: Technical support contact

### Acknowledgments

- **AI Technologies**: Google Generative AI, LangChain, HuggingFace
- **Infrastructure**: Firebase, Pinecone, FastAPI
- **Child Safety**: Tavily Search for safe content retrieval
- **Voice Technology**: VAPI for speech interaction

## 🔄 Version History

### v0.1.0 (Current)

- Initial release with core life skills modules
- AI-powered chatbot and mentor system
- Parent-child account management
- Gamification with points and badges
- Voice interaction capabilities
- Admin dashboard and analytics

### Planned Features

- Advanced learning path personalization
- Multi-language support
- Offline mode capabilities
- Enhanced voice recognition
- Social learning features
- Advanced parental controls

---

**Built with ❤️ for children's education and development**
