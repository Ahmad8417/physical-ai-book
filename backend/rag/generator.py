"""
RAG Generator - Generate answers using Ollama LLM
"""
from typing import Dict, Optional
import ollama


class AnswerGenerator:
    """Generate answers using LLM with retrieved context."""

    def __init__(
        self,
        model: str = "llama3.2",
        ollama_host: Optional[str] = None
    ):
        self.model = model
        if ollama_host:
            ollama.Client(host=ollama_host)

    def generate(self, question: str, context: str) -> Dict:
        """
        Generate answer using LLM with context.

        Args:
            question: User question
            context: Retrieved context from documents

        Returns:
            Dict with answer and metadata
        """
        # Create prompt
        prompt = self._create_prompt(question, context)

        try:
            # Call Ollama
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': (
                            'You are an expert AI assistant for the Physical AI & Humanoid Robotics textbook. '
                            'Answer questions based on the provided context from the textbook. '
                            'Be accurate, concise, and helpful. '
                            'If the context does not contain enough information to answer the question, '
                            'say so honestly and suggest what topics might be relevant.'
                        )
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )

            answer = response['message']['content']

            return {
                'answer': answer,
                'model': self.model,
                'success': True
            }

        except Exception as e:
            return {
                'answer': f"Error generating answer: {str(e)}",
                'model': self.model,
                'success': False,
                'error': str(e)
            }

    def _create_prompt(self, question: str, context: str) -> str:
        """Create prompt for LLM."""
        return f"""Based on the following context from the Physical AI & Humanoid Robotics textbook, please answer the question.

Context:
{context}

Question: {question}

Answer:"""

    def check_ollama_available(self) -> bool:
        """Check if Ollama is available and model is installed."""
        try:
            models = ollama.list()
            model_names = [m['name'] for m in models.get('models', [])]

            # Check if our model is available
            model_available = any(self.model in name for name in model_names)

            if not model_available:
                print(f"Model {self.model} not found. Available models: {model_names}")
                print(f"Please run: ollama pull {self.model}")

            return model_available

        except Exception as e:
            print(f"Ollama not available: {e}")
            print("Please make sure Ollama is running: https://ollama.ai/")
            return False


if __name__ == "__main__":
    # Test generator
    generator = AnswerGenerator()

    # Check if Ollama is available
    if generator.check_ollama_available():
        # Test generation
        test_context = """
        ROS 2 (Robot Operating System 2) is an open-source middleware framework
        designed for building robot applications. It provides tools and libraries
        for robot software development.
        """

        result = generator.generate(
            question="What is ROS 2?",
            context=test_context
        )

        print(f"Answer: {result['answer']}")
    else:
        print("Ollama not available for testing")
