# Sentiment Analysis Feature

A comprehensive sentiment analysis system built with Support Vector Machines (SVM) for the RAG & Multi-Agent Application dashboard.

## Overview

The sentiment analysis feature provides a modular, reusable, and configurable solution for analyzing sentiment in text data. It supports multiple input formats, custom model training, and configurable preprocessing options.

## Key Features

### 🎯 **Analysis Capabilities**
- **Text Analysis**: Analyze plain text input (single or batch)
- **CSV Analysis**: Process CSV files with automatic sentiment annotation
- **Configurable Preprocessing**: Control stopword removal, lemmatization, stemming, and case normalization

### 🤖 **Machine Learning**
- **SVM-Based Classification**: Industry-standard Support Vector Machine algorithm
- **Custom Model Training**: Train models on your own labeled datasets
- **Multiple Training Modes**: 
  - Upload training CSV files
  - Manual text/label input
- **Configurable Parameters**: Test/train split ratios, SVM hyperparameters

### 📊 **Results & Analytics**
- **Confidence Scores**: Get probability distributions for all sentiment classes
- **Statistics**: Sentiment distribution, average confidence, sample counts
- **Export Functionality**: Download CSV files with sentiment annotations
- **Analysis History**: Track past analyses and retrieve results

### 🔒 **Security & Permissions**
- **Role-Based Access**: `sentiment:analyze` and `sentiment:train` permissions
- **User Isolation**: Each user's analyses and models are tracked separately
- **Secure File Handling**: Validated uploads with size limits

## Architecture

### Backend Components

#### 1. **Sentiment Service** (`backend/app/services/sentiment_service.py`)

Core ML service implementing the SVM sentiment classifier:

```python
class SentimentAnalyzer:
    - preprocess_text(): Text cleaning and normalization
    - train_model(): Train SVM on labeled data
    - predict(): Classify sentiment for texts
    - predict_csv(): Process entire DataFrames
    - save_model(): Persist trained models
    - load_model(): Load existing models
```

**Features:**
- TF-IDF vectorization with n-grams
- Configurable text preprocessing pipeline
- Model persistence with joblib
- Comprehensive performance metrics

#### 2. **API Router** (`backend/app/api/v1/sentiment.py`)

RESTful API endpoints:

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/analyze-text` | POST | Analyze plain text | `sentiment:analyze` |
| `/analyze-csv` | POST | Analyze CSV file | `sentiment:analyze` |
| `/train` | POST | Train from manual input | `sentiment:train` |
| `/train-from-csv` | POST | Train from CSV file | `sentiment:train` |
| `/results/{id}` | GET | Retrieve analysis results | `sentiment:analyze` |
| `/export/{id}` | GET | Download CSV results | `sentiment:analyze` |
| `/model/info` | GET | Get model information | Any authenticated |
| `/history` | GET | Get analysis history | `sentiment:analyze` |

#### 3. **Database Model** (`backend/app/database/models.py`)

```python
class SentimentAnalysisResult:
    - analysis_type: 'text', 'csv', or 'training'
    - input_config: JSON with input parameters
    - preprocessing_config: JSON with preprocessing settings
    - training_config: JSON with training parameters
    - training_metrics: JSON with performance metrics
    - results: JSON with predictions
    - sentiment_distribution: JSON with counts
    - input_file_path: Original uploaded file
    - output_file_path: Annotated CSV file
```

### Frontend Components

#### Dashboard Page (`frontend/app/dashboard/sentiment/page.tsx`)

Comprehensive UI with 4 tabs:

**1. Text Analysis Tab**
- Multi-line text input
- Preprocessing option checkboxes
- Real-time results table
- Confidence scores with color coding

**2. CSV Analysis Tab**
- File upload with drag-and-drop
- Column selector for text field
- Preview of first 10 results
- Download annotated CSV button
- Statistics dashboard

**3. Train Model Tab**
- Two training modes: CSV upload or manual input
- Column selectors for text and labels
- Test/train split configuration
- Model naming
- Training metrics display (accuracy, precision, recall, F1)

**4. Results History Tab**
- View past analyses
- Retrieve by analysis ID
- Download previous results

## Installation & Setup

### 1. Install Python Dependencies

The following packages have been added to `backend/requirements.txt`:

```
scikit-learn==1.3.2
nltk==3.8.1
imbalanced-learn==0.11.0
joblib==1.3.2
```

Install them:

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Database Migration

Add the SentimentAnalysisResult table:

```bash
cd backend
python scripts/migrate_add_sentiment_table.py
```

### 3. Download NLTK Data

The service automatically downloads required NLTK data on first run:
- Punkt tokenizer
- Stopwords
- WordNet lemmatizer

### 4. Restart Backend Server

```bash
cd backend
python main.py
```

### 5. Access the Feature

1. Login to the dashboard
2. Ensure your user has `sentiment:analyze` permission (analysts and admins have it by default)
3. Click on the "Sentiment Analysis" card
4. Start analyzing!

## Usage Examples

### 1. Text Analysis

**Input:**
```
I love this product!
This is terrible.
It's okay, nothing special.
```

**Output:**
| Text | Sentiment | Confidence |
|------|-----------|------------|
| I love this product! | positive | 95.3% |
| This is terrible. | negative | 92.1% |
| It's okay, nothing special. | neutral | 78.4% |

### 2. CSV Analysis

**Input CSV (`reviews.csv`):**
```csv
review_id,review_text,product_name
1,Excellent quality!,Widget A
2,Not worth the money,Widget B
3,Average product,Widget C
```

**Output CSV (with sentiment):**
```csv
review_id,review_text,product_name,sentiment,sentiment_confidence,prob_positive,prob_negative,prob_neutral
1,Excellent quality!,Widget A,positive,0.94,0.94,0.03,0.03
2,Not worth the money,Widget B,negative,0.89,0.05,0.89,0.06
3,Average product,Widget C,neutral,0.76,0.12,0.12,0.76
```

### 3. Model Training

**Training Data CSV (`training_data.csv`):**
```csv
text,sentiment
I'm very happy,positive
This is awful,negative
It's fine,neutral
...
```

**Configuration:**
- Text Column: `text`
- Label Column: `sentiment`
- Test Size: 0.2 (20% for testing)

**Training Results:**
- Accuracy: 87.5%
- Precision: 86.2%
- Recall: 87.1%
- F1 Score: 86.6%

## API Usage Examples

### Analyze Text (cURL)

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze-text" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["I love this!", "This is bad"],
    "preprocessing_config": {
      "remove_stopwords": true,
      "use_lemmatization": true,
      "lowercase": true
    }
  }'
```

### Analyze CSV (Python)

```python
import requests

url = "http://localhost:8000/api/v1/sentiment/analyze-csv"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
files = {"file": open("reviews.csv", "rb")}
data = {"text_column": "review_text"}

response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()

print(f"Analyzed {result['total_samples']} samples")
print(f"Average confidence: {result['statistics']['average_confidence']}")
```

### Train Model (Python)

```python
import requests

url = "http://localhost:8000/api/v1/sentiment/train"
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}
data = {
    "texts": ["I love it", "I hate it", "It's okay"],
    "labels": ["positive", "negative", "neutral"],
    "test_size": 0.2,
    "model_name": "my_custom_model"
}

response = requests.post(url, headers=headers, json=data)
metrics = response.json()["metrics"]

print(f"Accuracy: {metrics['accuracy']:.2%}")
print(f"F1 Score: {metrics['f1_score']:.2%}")
```

## Configuration Options

### Preprocessing Options

```python
preprocessing_config = {
    "remove_stopwords": True,   # Remove common English stopwords
    "use_stemming": False,      # Apply Porter stemming (aggressive)
    "use_lemmatization": True,  # Apply WordNet lemmatization (recommended)
    "lowercase": True           # Convert to lowercase
}
```

**Recommendations:**
- Use `use_lemmatization` for better semantic preservation
- Use `use_stemming` only for very specific use cases
- Keep `remove_stopwords` enabled for better classification

### SVM Configuration

```python
svm_config = {
    "kernel": "linear",      # linear, rbf, poly
    "C": 1.0,                # Regularization parameter
    "probability": True,     # Enable probability estimates
    "random_state": 42       # For reproducibility
}
```

**Recommendations:**
- `linear` kernel works best for text classification
- Increase `C` to reduce regularization (more complex models)
- Always set `probability=True` for confidence scores

### Training Configuration

```python
training_config = {
    "test_size": 0.2,        # 20% for testing
    "random_state": 42       # For reproducibility
}
```

## Model Persistence

Models are saved to `backend/app/services/models/` with the following naming:
- Default: `sentiment_svm_model.pkl`
- Custom: `sentiment_model_{username}_{timestamp}.pkl`

Each model file contains:
- Trained SVM pipeline (TF-IDF + SVM)
- Label encoder
- Class labels
- Training metrics
- Metadata

## Performance Considerations

### For Large CSV Files

**Recommendations:**
- Files under 5,000 rows: Process synchronously ✓
- Files over 5,000 rows: Consider chunking or async processing

**Current Limits:**
- Max file size: 10 MB (configurable in `settings.MAX_UPLOAD_SIZE`)
- Max results stored in DB: First 100 predictions (full results in CSV export)

### Memory Usage

- TF-IDF vectorizer: ~50-200 MB depending on vocabulary size
- SVM model: ~10-50 MB depending on training data size
- Per-request memory: ~10-100 MB depending on batch size

## Troubleshooting

### Issue: "No trained model found"

**Solution:** Train a model first using the "Train Model" tab.

### Issue: "Column not found in CSV"

**Solution:** Ensure column names match exactly (case-sensitive).

### Issue: NLTK download errors

**Solution:** Manually download NLTK data:
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
```

### Issue: Low accuracy scores

**Solutions:**
1. Increase training data (aim for 100+ samples per class)
2. Balance classes (equal samples for each sentiment)
3. Adjust preprocessing options
4. Try different SVM parameters

## Permissions

### Required Permissions

| Action | Permission | Default Roles |
|--------|------------|---------------|
| Analyze sentiment | `sentiment:analyze` | analyst, admin |
| Train models | `sentiment:train` | analyst, admin |
| View model info | Any authenticated | all |

### Granting Permissions

Admins can grant permissions via the Admin panel or database:

```python
# Add to analyst role
analyst_role.permissions.append(
    Permission(name="sentiment:analyze", resource="sentiment", action="analyze")
)
```

## Extension Points

### Custom Preprocessing

Extend `SentimentAnalyzer.preprocess_text()` to add:
- Emoji handling
- Slang normalization
- Domain-specific text cleaning

### Additional Algorithms

The service is modular - you can add:
- Naive Bayes classifier
- Random Forest
- Neural networks (BERT, RoBERTa)
- Ensemble methods

### Multi-Language Support

Add language detection and language-specific preprocessing:
```python
from langdetect import detect

def preprocess_multilingual(text):
    lang = detect(text)
    # Apply language-specific preprocessing
```

## Best Practices

1. **Training Data Quality**
   - Aim for balanced classes
   - Use diverse, representative samples
   - Clean and validate labels

2. **Model Evaluation**
   - Check confusion matrix
   - Validate on held-out test set
   - Monitor confidence scores

3. **Production Deployment**
   - Version your models
   - Log predictions for monitoring
   - Set up performance alerts

4. **Security**
   - Validate all file uploads
   - Sanitize text inputs
   - Implement rate limiting

## Future Enhancements

- [ ] Aspect-based sentiment analysis
- [ ] Multi-label classification
- [ ] Real-time streaming analysis
- [ ] Model comparison and A/B testing
- [ ] Automatic model retraining
- [ ] Integration with existing chat/RAG features
- [ ] Sentiment trend visualization
- [ ] Export to multiple formats (JSON, Excel, Parquet)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API error messages
3. Check backend logs: `backend/logs/`
4. Contact system administrator

## License

This feature is part of the RAG & Multi-Agent Application and follows the same license terms.
