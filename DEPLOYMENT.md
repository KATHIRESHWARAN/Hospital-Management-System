# Deployment Guide

## Size Optimization for Vercel

The Vercel serverless function has a 250 MB uncompressed size limit. To meet this constraint, the ML dependencies (numpy, scikit-learn, spacy) have been moved to **optional dependencies** and are not deployed to Vercel.

### How It Works

1. **Production (Vercel)**:
   - Uses a lightweight keyword-based triage assessment fallback
   - No numpy, scikit-learn, or spacy installed
   - Function size: ~50-60 MB
   - Fully functional with degraded AI capabilities

2. **Development (Local)**:
   - Install ML dependencies: `pip install -e ".[ml]"`
   - Full ML-powered triage assessment using scikit-learn
   - Spacy NLP model for advanced text processing

## Local Setup with Full ML Features

```bash
# Install base dependencies
pip install -e .

# Install ML dependencies (numpy, scikit-learn, spacy)
pip install -e ".[ml]"

# Run locally
python -m flask run
```

## Vercel Deployment

```bash
# Deploy to Vercel (ML deps are excluded via .vercelignore)
vercel
```

## Triage Assessment Features

### On Vercel (Keyword-Based Fallback)
- Fast, lightweight severity classification
- Critical, High, Medium, Low categories
- Keyword matching for common symptoms
- Appropriate for production serverless environment

### Locally (Full ML Model)
- Machine learning-powered severity classification
- NLP preprocessing with spacy
- TF-IDF + Naive Bayes classifier
- More sophisticated symptom analysis
- Better accuracy for edge cases

## Key Files

- `pyproject.toml` - Dependency configuration
- `.vercelignore` - Exclusion list for Vercel deployment
- `ai_services.py` - Triage assessment with fallback mechanism
- `routes.py` - HTTP endpoints (lazy imports ML modules)

## Troubleshooting

### Function Size Exceeded on Vercel
Verify `.vercelignore` includes:
```
node_modules
__pycache__
.git
tests
docs
static
templates
scripts
```

### ML Features Not Working Locally
Install ML dependencies:
```bash
pip install -e ".[ml]"
```

### Spacy Model Not Found
First time spacy is used, it will fail gracefully and use simple tokenization.

To use full spacy features:
```bash
python -m spacy download en_core_web_sm
```
