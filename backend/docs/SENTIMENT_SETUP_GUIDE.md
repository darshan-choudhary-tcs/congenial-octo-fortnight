# Sentiment Analysis Feature - Setup Guide

## Quick Start

This guide will help you set up the Sentiment Analysis feature in your dashboard.

## Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL or SQLite database
- Backend and frontend already configured

## Installation Steps

### 1. Install Python Dependencies

```bash
cd backend
pip install scikit-learn==1.4.0 nltk==3.8.1 joblib==1.3.2 imbalanced-learn==0.12.0
```

Or install from requirements.txt (already updated):
```bash
pip install -r requirements.txt
```

### 2. Run Database Migration

Create the sentiment_analysis_results table:

```bash
cd backend
python scripts/migrate_add_sentiment_table.py
```

### 3. Add Permissions

Add sentiment:analyze permission to roles:

```bash
python scripts/migrate_add_sentiment_permissions.py
```

This adds the permission to admin and analyst roles.

### 4. Initialize the Sentiment Model

Create and train the pre-trained SVM model:

```bash
python scripts/setup_sentiment_model.py
```

This will:
- Download NLTK data (punkt, stopwords)
- Create a pre-trained SVM model with seed data
- Save the model to `backend/app/services/models/`
- Run test predictions to verify setup

Expected output:
```
Sentiment Analysis Setup
============================================================
Initializing sentiment analysis service...
Downloading NLTK data...
Training model with seed data...
Seed model training completed. Accuracy: 95%
✅ Sentiment analysis service initialized successfully!
   Model location: backend/app/services/models/sentiment_svm_model.pkl

Testing the model with sample texts...
   Test 1:
   Text: I absolutely love this product! It's amazing and works...
   Sentiment: positive
   Confidence: 87.32%
...
```

### 5. Start the Backend

```bash
cd backend
python main.py
```

The sentiment API will be available at:
- http://localhost:8000/api/v1/sentiment/

### 6. Start the Frontend

```bash
cd frontend
npm install  # if not already done
npm run dev
```

### 7. Access the Feature

1. Open http://localhost:3000
2. Login with a user that has `sentiment:analyze` permission
3. Navigate to Dashboard → Sentiment Analysis

## Feature Overview

### CSV Analysis Workflow

1. **Upload CSV File**
   - Click "Select CSV File" in the CSV Analysis tab
   - Choose a CSV file containing text data
   - System automatically detects text columns

2. **Configure Analysis**
   - Select the column containing text to analyze
   - Optionally customize output column names:
     - Sentiment column (default: "sentiment")
     - Confidence column (default: "sentiment_confidence")

3. **Run Analysis**
   - Click "Analyze Sentiment"
   - Processing begins (shows progress indicator)
   - Results appear in the Results tab

4. **View Results**
   - Statistics cards show sentiment distribution
   - Average confidence score displayed
   - Download button to get updated CSV file

5. **Download Output**
   - Click "Download CSV" to get the file
   - Original data + 2 new columns (sentiment, confidence)
   - All rows include sentiment classification

### Help Section

The dashboard includes a comprehensive Help tab with:
- Feature overview and sentiment categories
- Step-by-step workflow guide
- Technical details about the ML model
- Best practices for accurate results
- Use cases and examples

## API Endpoints

All endpoints require authentication with `sentiment:analyze` permission.

### Analyze Text
```bash
POST /api/v1/sentiment/analyze-text
Content-Type: application/json

{
  "text": "I love this product!"
}

Response:
{
  "text": "I love this product!",
  "sentiment": "positive",
  "confidence": 0.8532
}
```

### Analyze CSV
```bash
POST /api/v1/sentiment/analyze-csv
Content-Type: multipart/form-data

Form Fields:
- file: CSV file
- text_column: "review_text"
- sentiment_column: "sentiment" (optional)
- confidence_column: "confidence" (optional)

Response:
{
  "id": 1,
  "uuid": "abc-123",
  "status": "completed",
  "total_rows": 1000,
  "positive_count": 450,
  "negative_count": 300,
  "neutral_count": 250,
  "average_confidence": 0.78,
  ...
}
```

### Get Column Suggestions
```bash
POST /api/v1/sentiment/get-columns
Content-Type: multipart/form-data

Form Fields:
- file: CSV file

Response:
{
  "text_columns": ["review", "comment", "feedback"],
  "numeric_columns": ["rating", "price"],
  "all_columns": ["id", "review", "rating", "comment", ...]
}
```

### Get Results
```bash
GET /api/v1/sentiment/results?limit=20&offset=0

Response:
[
  {
    "id": 1,
    "uuid": "abc-123",
    "original_filename": "reviews.csv",
    "created_at": "2025-12-05T10:30:00",
    "status": "completed",
    ...
  }
]
```

### Get Single Result
```bash
GET /api/v1/sentiment/results/{uuid}
```

### Export Result CSV
```bash
GET /api/v1/sentiment/export/{uuid}

Response: CSV file download
```

### Delete Result
```bash
DELETE /api/v1/sentiment/results/{uuid}
```

## Programmatic Usage

### Python Service Layer

```python
from app.services.sentiment_service import get_sentiment_service

# Get service instance
service = get_sentiment_service()

# Analyze single text
result = service.analyze_text("This is amazing!")
print(result)
# {'text': 'This is amazing!', 'sentiment': 'positive', 'confidence': 0.85}

# Analyze batch
texts = ["Great product!", "Terrible quality", "It's okay"]
results = service.analyze_batch(texts)

# Analyze DataFrame
import pandas as pd
df = pd.read_csv("reviews.csv")
result_df, stats = service.analyze_dataframe(
    df=df,
    text_column="review_text",
    output_sentiment_column="sentiment",
    output_confidence_column="confidence"
)
print(stats)
# {
#   'total_rows': 1000,
#   'positive_count': 450,
#   'negative_count': 300,
#   'neutral_count': 250,
#   'average_confidence': 0.78,
#   ...
# }

# Process CSV file
result = service.process_csv_file(
    input_path="input.csv",
    output_path="output.csv",
    text_column="text"
)
```

## Model Details

### Pre-trained SVM Classifier

- **Algorithm**: LinearSVC (Support Vector Classification)
- **Vectorization**: TF-IDF with 5000 features, unigrams + bigrams
- **Classes**: positive, negative, neutral
- **Preprocessing**: Lowercase, URL removal, special character handling
- **Training**: Initialized with 45 diverse sentiment examples

### Text Preprocessing

The service automatically:
1. Converts text to lowercase
2. Removes URLs and email addresses
3. Removes social media mentions and hashtags
4. Strips special characters (keeps only letters and spaces)
5. Normalizes whitespace

### Confidence Scores

- Derived from SVM decision function
- Range: 0.0 to 1.0
- Higher values = more confident predictions
- Recommendations:
  - 0.8-1.0: High confidence, trust the prediction
  - 0.6-0.8: Medium confidence, generally reliable
  - 0.0-0.6: Low confidence, consider manual review

## Troubleshooting

### Model Not Found Error

**Problem**: `FileNotFoundError: sentiment_svm_model.pkl not found`

**Solution**:
```bash
cd backend
python scripts/setup_sentiment_model.py
```

### NLTK Data Missing

**Problem**: `LookupError: Resource punkt not found`

**Solution**:
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')
```

Or run the setup script which downloads automatically.

### Permission Denied

**Problem**: User cannot access sentiment analysis

**Solution**:
1. Run permission migration:
   ```bash
   python scripts/migrate_add_sentiment_permissions.py
   ```
2. Verify user has `sentiment:analyze` permission
3. Check user role (admin, analyst should have it)

### CSV Upload Fails

**Problem**: "Error reading CSV file"

**Solutions**:
- Verify CSV is valid UTF-8 encoded
- Check CSV has column headers
- Ensure file size is under limit (10MB default)
- Verify at least one text column exists

### Analysis Takes Too Long

**Problem**: Large CSV files time out

**Solutions**:
- Process smaller batches (split large files)
- Increase timeout settings
- Use server with more CPU resources
- Consider async processing for >5000 rows

## Best Practices

### Data Preparation
- Ensure CSV files have clear column headers
- Text should be in English (model trained on English)
- Longer text provides more accurate results (>10 words recommended)
- Clean obvious errors (encoding issues, null values)

### Model Usage
- Review low-confidence predictions (<0.6) manually for critical applications
- The model works best with complete sentences
- Very short text (1-2 words) may be unreliable
- Domain-specific slang may need fine-tuning

### Performance
- Files with <5000 rows: Process synchronously (fast)
- Files with >5000 rows: Consider batch processing
- Monitor confidence scores to identify data quality issues
- Use column suggestions to avoid wrong column selection

### Security
- Only upload CSV files you trust
- Results are user-isolated (privacy preserved)
- Downloaded files include all original data + sentiment columns
- Delete old results to save storage space

## Use Cases

### 1. Customer Feedback Analysis
```
CSV columns: customer_id, feedback_text, date
Analyze: feedback_text
Output: + sentiment, confidence
Use: Identify unhappy customers, track satisfaction trends
```

### 2. Product Review Monitoring
```
CSV columns: product_id, review, rating, reviewer
Analyze: review
Output: + sentiment, confidence
Use: Compare sentiment vs. star ratings, find fake reviews
```

### 3. Social Media Monitoring
```
CSV columns: post_id, content, author, timestamp
Analyze: content
Output: + sentiment, confidence
Use: Track brand mentions, measure campaign impact
```

### 4. Survey Analysis
```
CSV columns: respondent_id, open_response, question_id
Analyze: open_response
Output: + sentiment, confidence
Use: Quantify qualitative feedback, identify themes
```

### 5. Support Ticket Classification
```
CSV columns: ticket_id, description, category, priority
Analyze: description
Output: + sentiment, confidence
Use: Prioritize urgent negative tickets, route to appropriate teams
```

## Next Steps

After setup is complete:

1. **Test with Sample Data**
   - Create a small CSV with text data
   - Upload and analyze
   - Verify results are reasonable

2. **Integrate into Workflows**
   - Export results to BI tools
   - Schedule regular analyses
   - Build dashboards on top of results

3. **Monitor Performance**
   - Track confidence scores over time
   - Identify low-confidence patterns
   - Consider domain-specific training

4. **Provide User Training**
   - Share the Help documentation with users
   - Demonstrate the workflow
   - Set expectations for accuracy

## Support

For issues:
1. Check the Help tab in the dashboard
2. Review application logs: `backend/logs/`
3. Verify all migration scripts ran successfully
4. Test with the setup script

## Summary

The sentiment analysis feature is now ready to use! It provides:
- ✅ Pre-trained SVM model for immediate use
- ✅ CSV batch processing with column selection
- ✅ Confidence scoring for prediction quality
- ✅ Result history and export functionality
- ✅ Comprehensive help documentation
- ✅ Modular, reusable architecture

You can now analyze text sentiment directly from the dashboard or integrate the service layer into custom applications.
