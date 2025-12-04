"""
Setup Sentiment Analysis Model

This script initializes the sentiment analysis service and creates
a pre-trained SVM model. Run this after installing dependencies.

Usage:
    python backend/scripts/setup_sentiment_model.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger
from app.services.sentiment_service import get_sentiment_service

def main():
    """Initialize sentiment analysis service and create pre-trained model"""
    
    logger.info("=" * 60)
    logger.info("Sentiment Analysis Setup")
    logger.info("=" * 60)
    
    try:
        # Initialize service (this will create the model if it doesn't exist)
        logger.info("\nInitializing sentiment analysis service...")
        service = get_sentiment_service()
        
        logger.info("\n✅ Sentiment analysis service initialized successfully!")
        logger.info(f"   Model location: {service.MODEL_PATH}")
        
        # Test the model with sample text
        logger.info("\nTesting the model with sample texts...")
        
        test_samples = [
            "I absolutely love this product! It's amazing and works perfectly!",
            "This is terrible, I'm very disappointed and frustrated with this.",
            "The item arrived on time and works as described.",
        ]
        
        for i, text in enumerate(test_samples, 1):
            result = service.analyze_text(text)
            logger.info(f"\n   Test {i}:")
            logger.info(f"   Text: {text[:60]}...")
            logger.info(f"   Sentiment: {result['sentiment']}")
            logger.info(f"   Confidence: {result['confidence']:.2%}")
        
        logger.info("\n" + "=" * 60)
        logger.info("Setup completed successfully!")
        logger.info("=" * 60)
        logger.info("\nThe sentiment analysis feature is ready to use.")
        logger.info("You can now:")
        logger.info("  1. Start the backend server: python backend/main.py")
        logger.info("  2. Access the sentiment analysis dashboard")
        logger.info("  3. Upload CSV files for batch sentiment analysis")
        
    except Exception as e:
        logger.error(f"\n❌ Setup failed: {e}")
        logger.exception(e)
        sys.exit(1)

if __name__ == "__main__":
    main()
