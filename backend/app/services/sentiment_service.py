"""
Sentiment Analysis Service

Provides modular, reusable sentiment analysis using SVM classifier.
Supports text input and CSV batch processing with column specification.
"""

import os
import re
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import uuid

from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from loguru import logger


class SentimentAnalysisService:
    """
    Modular sentiment analysis service using SVM classifier.
    
    Features:
    - Pre-trained model with fallback to initialization
    - Text preprocessing with NLTK
    - TF-IDF vectorization
    - Batch processing for CSV files
    - Confidence scoring
    - Generic and reusable for various use cases
    """
    
    MODEL_DIR = Path(__file__).parent / "models"
    MODEL_PATH = MODEL_DIR / "sentiment_svm_model.pkl"
    
    # Sentiment labels
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    
    def __init__(self):
        """Initialize the sentiment analysis service."""
        self.model: Optional[Pipeline] = None
        self.vectorizer: Optional[TfidfVectorizer] = None
        
        # Ensure model directory exists
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        
        # Download NLTK data if not available
        self._setup_nltk()
        
        # Load or initialize model
        self._load_or_initialize_model()
    
    def _setup_nltk(self):
        """Download required NLTK data."""
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            logger.info("Downloading NLTK data...")
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('punkt_tab', quiet=True)
    
    def _load_or_initialize_model(self):
        """Load existing model or initialize a new one."""
        if self.MODEL_PATH.exists():
            try:
                logger.info(f"Loading pre-trained sentiment model from {self.MODEL_PATH}")
                self.model = joblib.load(self.MODEL_PATH)
                logger.info("Sentiment model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                logger.info("Initializing new model...")
                self._initialize_model()
        else:
            logger.info("No pre-trained model found. Initializing new model...")
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize a new SVM sentiment model with basic training."""
        logger.info("Creating new SVM sentiment classifier...")
        
        # Create pipeline with TF-IDF vectorizer and LinearSVC
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.8,
                strip_accents='unicode',
                lowercase=True,
                stop_words='english'
            )),
            ('classifier', LinearSVC(
                C=1.0,
                class_weight='balanced',
                max_iter=2000,
                random_state=42
            ))
        ])
        
        # Train with basic sentiment examples
        self._train_with_seed_data()
        
        # Save the initialized model
        self.save_model()
    
    def _train_with_seed_data(self):
        """Train the model with seed sentiment data."""
        logger.info("Training model with seed data...")
        
        # Seed training data with diverse sentiment examples
        seed_data = [
            # Positive sentiments
            ("I love this product, it's amazing and works perfectly!", self.POSITIVE),
            ("Excellent service, highly recommend to everyone!", self.POSITIVE),
            ("This is wonderful, exceeded my expectations!", self.POSITIVE),
            ("Great experience, very satisfied with the quality!", self.POSITIVE),
            ("Fantastic work, absolutely brilliant and impressive!", self.POSITIVE),
            ("I'm very happy with this, worth every penny!", self.POSITIVE),
            ("Outstanding performance, couldn't ask for better!", self.POSITIVE),
            ("Superb quality, this is exactly what I needed!", self.POSITIVE),
            ("Delighted with the results, truly remarkable!", self.POSITIVE),
            ("Perfect in every way, I'm thrilled with this!", self.POSITIVE),
            ("Awesome product, highly satisfied and impressed!", self.POSITIVE),
            ("Beautiful design and excellent functionality!", self.POSITIVE),
            ("This made my day, absolutely love it!", self.POSITIVE),
            ("Impressive quality, exceeded all expectations!", self.POSITIVE),
            ("Brilliant solution, works like a charm!", self.POSITIVE),
            
            # Negative sentiments
            ("I hate this, it's terrible and doesn't work at all.", self.NEGATIVE),
            ("Awful experience, very disappointed and frustrated.", self.NEGATIVE),
            ("This is horrible, complete waste of money and time.", self.NEGATIVE),
            ("Terrible quality, very poor and unsatisfactory.", self.NEGATIVE),
            ("Worst purchase ever, extremely disappointed.", self.NEGATIVE),
            ("I'm very unhappy with this, total disaster.", self.NEGATIVE),
            ("Poor service, wouldn't recommend to anyone.", self.NEGATIVE),
            ("Disgusting quality, broke immediately after use.", self.NEGATIVE),
            ("Horrible experience, very frustrating and annoying.", self.NEGATIVE),
            ("Disappointing results, not what was promised.", self.NEGATIVE),
            ("Bad quality, doesn't meet basic standards.", self.NEGATIVE),
            ("Useless product, completely failed expectations.", self.NEGATIVE),
            ("Terrible design, very poorly made and cheap.", self.NEGATIVE),
            ("Unacceptable quality, I want my money back.", self.NEGATIVE),
            ("Awful performance, doesn't work as advertised.", self.NEGATIVE),
            
            # Neutral sentiments
            ("This is okay, nothing special but acceptable.", self.NEUTRAL),
            ("The product arrived on time, standard packaging.", self.NEUTRAL),
            ("It works as described, meets basic requirements.", self.NEUTRAL),
            ("Average quality, neither good nor bad.", self.NEUTRAL),
            ("Standard service, nothing remarkable to report.", self.NEUTRAL),
            ("This is functional, does what it's supposed to do.", self.NEUTRAL),
            ("Received the item, it's as expected from the description.", self.NEUTRAL),
            ("Moderate quality, acceptable for the price point.", self.NEUTRAL),
            ("The product is operational, serves its purpose.", self.NEUTRAL),
            ("Normal experience, no complaints but nothing special.", self.NEUTRAL),
            ("Fair quality, meets minimum expectations.", self.NEUTRAL),
            ("Standard functionality, works adequately for basic needs.", self.NEUTRAL),
            ("This is satisfactory, no major issues to report.", self.NEUTRAL),
            ("Decent product, serves its intended purpose well enough.", self.NEUTRAL),
            ("Unremarkable but functional, does the job.", self.NEUTRAL),
        ]
        
        texts = [text for text, _ in seed_data]
        labels = [label for _, label in seed_data]
        
        # Preprocess texts
        processed_texts = [self._preprocess_text(text) for text in texts]
        
        # Train the model
        self.model.fit(processed_texts, labels)
        
        # Log training accuracy
        predictions = self.model.predict(processed_texts)
        accuracy = accuracy_score(labels, predictions)
        logger.info(f"Seed model training completed. Accuracy: {accuracy:.2%}")
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for sentiment analysis.
        
        Args:
            text: Input text to preprocess
            
        Returns:
            Preprocessed text string
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove mentions and hashtags (social media specific)
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Remove special characters and digits, keep only letters and spaces
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a single text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing sentiment label and confidence score
        """
        if not text or not isinstance(text, str):
            return {
                "text": text,
                "sentiment": self.NEUTRAL,
                "confidence": 0.0,
                "error": "Invalid or empty text"
            }
        
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            if not processed_text:
                return {
                    "text": text,
                    "sentiment": self.NEUTRAL,
                    "confidence": 0.5,
                    "error": "Text empty after preprocessing"
                }
            
            # Predict sentiment
            sentiment = self.model.predict([processed_text])[0]
            
            # Get decision function scores for confidence
            decision_scores = self.model.decision_function([processed_text])[0]
            
            # Calculate confidence (normalized decision function score)
            # For multi-class, take the max score and normalize
            if isinstance(decision_scores, np.ndarray):
                max_score = np.max(decision_scores)
                min_score = np.min(decision_scores)
                if max_score != min_score:
                    confidence = (max_score - min_score) / (np.ptp(decision_scores) + 1e-10)
                else:
                    confidence = 0.5
            else:
                # Binary classification
                confidence = abs(decision_scores) / (abs(decision_scores) + 1)
            
            confidence = float(np.clip(confidence, 0, 1))
            
            return {
                "text": text[:200] + "..." if len(text) > 200 else text,
                "sentiment": sentiment,
                "confidence": round(confidence, 4)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return {
                "text": text,
                "sentiment": self.NEUTRAL,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for a batch of texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of sentiment analysis results
        """
        results = []
        
        for text in texts:
            result = self.analyze_text(text)
            results.append(result)
        
        return results
    
    def analyze_dataframe(
        self,
        df: pd.DataFrame,
        text_column: str,
        output_sentiment_column: str = "sentiment",
        output_confidence_column: str = "sentiment_confidence"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Analyze sentiment for a DataFrame column.
        
        Args:
            df: Input DataFrame
            text_column: Name of column containing text to analyze
            output_sentiment_column: Name for sentiment output column
            output_confidence_column: Name for confidence output column
            
        Returns:
            Tuple of (updated DataFrame, statistics dictionary)
        """
        if text_column not in df.columns:
            raise ValueError(f"Column '{text_column}' not found in DataFrame")
        
        # Create a copy to avoid modifying original
        result_df = df.copy()
        
        # Analyze each text
        logger.info(f"Analyzing {len(df)} rows...")
        texts = df[text_column].fillna("").astype(str).tolist()
        
        sentiments = []
        confidences = []
        
        for i, text in enumerate(texts):
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(texts)} rows...")
            
            result = self.analyze_text(text)
            sentiments.append(result["sentiment"])
            confidences.append(result["confidence"])
        
        # Add results to DataFrame
        result_df[output_sentiment_column] = sentiments
        result_df[output_confidence_column] = confidences
        
        # Calculate statistics
        sentiment_counts = result_df[output_sentiment_column].value_counts().to_dict()
        avg_confidence = result_df[output_confidence_column].mean()
        
        stats = {
            "total_rows": len(result_df),
            "sentiment_distribution": sentiment_counts,
            "average_confidence": round(float(avg_confidence), 4),
            "positive_count": sentiment_counts.get(self.POSITIVE, 0),
            "negative_count": sentiment_counts.get(self.NEGATIVE, 0),
            "neutral_count": sentiment_counts.get(self.NEUTRAL, 0),
            "positive_percentage": round(sentiment_counts.get(self.POSITIVE, 0) / len(result_df) * 100, 2),
            "negative_percentage": round(sentiment_counts.get(self.NEGATIVE, 0) / len(result_df) * 100, 2),
            "neutral_percentage": round(sentiment_counts.get(self.NEUTRAL, 0) / len(result_df) * 100, 2),
        }
        
        logger.info(f"Analysis complete. Stats: {stats}")
        
        return result_df, stats
    
    def process_csv_file(
        self,
        input_path: str,
        output_path: str,
        text_column: str,
        output_sentiment_column: str = "sentiment",
        output_confidence_column: str = "sentiment_confidence"
    ) -> Dict[str, Any]:
        """
        Process a CSV file and add sentiment analysis columns.
        
        Args:
            input_path: Path to input CSV file
            output_path: Path to output CSV file
            text_column: Name of column containing text to analyze
            output_sentiment_column: Name for sentiment output column
            output_confidence_column: Name for confidence output column
            
        Returns:
            Dictionary with statistics and file paths
        """
        try:
            logger.info(f"Reading CSV file: {input_path}")
            df = pd.read_csv(input_path)
            
            logger.info(f"CSV loaded. Shape: {df.shape}")
            logger.info(f"Columns: {list(df.columns)}")
            
            # Analyze DataFrame
            result_df, stats = self.analyze_dataframe(
                df=df,
                text_column=text_column,
                output_sentiment_column=output_sentiment_column,
                output_confidence_column=output_confidence_column
            )
            
            # Save result
            logger.info(f"Saving results to: {output_path}")
            result_df.to_csv(output_path, index=False)
            
            return {
                "success": True,
                "input_path": input_path,
                "output_path": output_path,
                "statistics": stats,
                "columns": {
                    "text_column": text_column,
                    "sentiment_column": output_sentiment_column,
                    "confidence_column": output_confidence_column
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {e}")
            return {
                "success": False,
                "error": str(e),
                "input_path": input_path
            }
    
    def get_column_suggestions(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Suggest which columns might contain text for sentiment analysis.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with column suggestions
        """
        text_columns = []
        numeric_columns = []
        
        for col in df.columns:
            # Check if column contains string/object data
            if df[col].dtype == 'object':
                # Sample some values to check if they're text
                sample = df[col].dropna().head(5)
                if len(sample) > 0:
                    avg_length = sample.astype(str).str.len().mean()
                    # Consider columns with average length > 10 as potential text columns
                    if avg_length > 10:
                        text_columns.append(col)
            elif pd.api.types.is_numeric_dtype(df[col]):
                numeric_columns.append(col)
        
        return {
            "text_columns": text_columns,
            "numeric_columns": numeric_columns,
            "all_columns": list(df.columns)
        }
    
    def save_model(self):
        """Save the trained model to disk."""
        try:
            joblib.dump(self.model, self.MODEL_PATH)
            logger.info(f"Model saved to {self.MODEL_PATH}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def train_custom_model(
        self,
        texts: List[str],
        labels: List[str],
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train a custom model with user-provided data.
        
        Args:
            texts: List of training texts
            labels: List of corresponding sentiment labels
            test_size: Proportion of data to use for testing
            
        Returns:
            Dictionary with training results and metrics
        """
        try:
            logger.info(f"Training custom model with {len(texts)} samples...")
            
            # Preprocess texts
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                processed_texts, labels, test_size=test_size, random_state=42, stratify=labels
            )
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate
            train_predictions = self.model.predict(X_train)
            test_predictions = self.model.predict(X_test)
            
            train_accuracy = accuracy_score(y_train, train_predictions)
            test_accuracy = accuracy_score(y_test, test_predictions)
            
            # Get classification report
            report = classification_report(y_test, test_predictions, output_dict=True)
            
            # Save model
            self.save_model()
            
            results = {
                "success": True,
                "train_accuracy": round(train_accuracy, 4),
                "test_accuracy": round(test_accuracy, 4),
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "classification_report": report
            }
            
            logger.info(f"Training complete. Test accuracy: {test_accuracy:.2%}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error training custom model: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global service instance
_sentiment_service = None


def get_sentiment_service() -> SentimentAnalysisService:
    """Get or create the global sentiment analysis service instance."""
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentAnalysisService()
    return _sentiment_service
