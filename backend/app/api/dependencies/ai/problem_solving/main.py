import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from .models import QuestionResponse
from .service import QuestionService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Smart Question Generator",
    description="Generates thought-provoking questions to boost mental ability",
    version="1.0.0",
)

# Initialize service — no API key needed; model configured via OLLAMA_* env vars
service = QuestionService()


@app.post("/generate", response_model=QuestionResponse)
async def generate_question():
    """
    Generate a thought-provoking question to boost mental ability.

    Example:
    {
        "user_id": "101",
        "level": "beginner"
    }

    Levels: beginner, medium, advanced
    """
    try:
        # Use dummy data for testing
        user_id = "104"
        level = "beginner"

        # Uncomment to use actual request data:
        # user_id = request.user_id
        # level = request.level

        question = service.generate_question(user_id=user_id, level=level)

        logger.info(f"Generated question for user: {user_id}, level: {level}")
        return question

    except Exception as e:
        logger.error(f"Error generating question: {e}")
        raise HTTPException(
            status_code=500, detail=f"Could not generate question: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Smart Question Generator ready!"}


def test_generator():
    """Test the question generator."""
    print("🧠 Testing Smart Question Generator\n")

    try:
        levels = ["beginner", "medium", "advanced"]

        for level in levels:
            print(f"🎯 Testing {level.upper()} level:")
            print("-" * 50)

            question = service.generate_question(user_id="test_user", level=level)

            print(f"❓ Question: {question.question}")
            print("📝 Options:")
            print(f"   A) {question.option_a}")
            print(f"   B) {question.option_b}")
            print(f"   C) {question.option_c}")
            print(f"   D) {question.option_d}")
            print(f"✅ Answer: {question.correct_answer}")
            print(f"💡 Explanation: {question.explanation}")
            print("\n" + "=" * 80 + "\n")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_generator()