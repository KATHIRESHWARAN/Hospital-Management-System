import logging
import re

# Initialize logging
logger = logging.getLogger(__name__)

# Lazy load ML dependencies
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    ML_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ML dependencies not available: {e}. AI services will be limited.")
    ML_AVAILABLE = False

# Global spaCy model - loaded lazily on first use (not at import time)
# This prevents serverless function crashes on Vercel startup
_nlp = None

def get_nlp_model():
    """Lazy-load spaCy model on first use."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.warning("spaCy model not found. Using simple tokenization instead.")
            _nlp = None
        except Exception as e:
            logger.warning(f"Failed to load spaCy model: {e}. Using simple tokenization instead.")
            _nlp = None
    return _nlp

# For backward compatibility, expose nlp as a callable
nlp = None

# Training data for the triage model
# Format: (symptoms, severity)
TRIAGE_TRAINING_DATA = [
    # Low severity symptoms
    ("I have a mild headache", "Low"),
    ("Slight cough for one day", "Low"),
    ("Runny nose and sneezing", "Low"),
    ("Minor cuts and scrapes", "Low"),
    ("Mild sore throat", "Low"),
    ("Slight fever below 38°C", "Low"),
    ("Mild joint pain", "Low"),
    ("Minor skin rash", "Low"),
    
    # Medium severity symptoms
    ("Persistent headache for several days", "Medium"),
    ("Fever between 38°C and 39°C", "Medium"),
    ("Cough with colored phlegm", "Medium"),
    ("Dehydration with some dizziness", "Medium"),
    ("Persistent vomiting", "Medium"),
    ("Flu symptoms with high fever", "Medium"),
    ("Ear pain with discharge", "Medium"),
    ("Urinary tract infection symptoms", "Medium"),
    
    # High severity symptoms
    ("Severe abdominal pain", "High"),
    ("Difficulty breathing", "High"),
    ("High fever above 39°C", "High"),
    ("Chest pain", "High"),
    ("Severe headache with neck stiffness", "High"),
    ("Sudden vision changes", "High"),
    ("Deep cut requiring stitches", "High"),
    ("Broken bone or suspected fracture", "High"),
    
    # Critical severity symptoms
    ("Unconsciousness or fainting", "Critical"),
    ("Severe chest pain radiating to arm or jaw", "Critical"),
    ("Inability to breathe", "Critical"),
    ("Severe bleeding that won't stop", "Critical"),
    ("Poisoning or overdose", "Critical"),
    ("Seizure", "Critical"),
    ("Severe burn", "Critical"),
    ("Stroke symptoms like facial drooping", "Critical"),
]

# Additional training data with medical terminology
MEDICAL_TRAINING_DATA = [
    # Low severity
    ("Mild rhinitis with nasal discharge", "Low"),
    ("Slight pharyngitis with minimal discomfort", "Low"),
    ("Minor contusions", "Low"),
    ("Localized dermatitis", "Low"),
    
    # Medium severity
    ("Moderate pyrexia with myalgia", "Medium"),
    ("Persistent emesis", "Medium"),
    ("Otitis media with effusion", "Medium"),
    ("Uncomplicated cystitis", "Medium"),
    
    # High severity
    ("Acute dyspnea", "High"),
    ("Severe cephalgia with photophobia", "High"),
    ("Suspected appendicitis", "High"),
    ("Open fracture requiring reduction", "High"),
    
    # Critical severity
    ("Syncope with irregular cardiac rhythm", "Critical"),
    ("Acute myocardial infarction", "Critical"),
    ("Status epilepticus", "Critical"),
    ("Cerebrovascular accident with hemiparesis", "Critical"),
]

# Combine all training data
ALL_TRAINING_DATA = TRIAGE_TRAINING_DATA + MEDICAL_TRAINING_DATA

# Function to preprocess text
def preprocess_text(text):
    nlp = get_nlp_model()  # Get lazily-loaded model
    if nlp:
        # Use spaCy for preprocessing if available
        doc = nlp(text.lower())
        # Remove stopwords and punctuation
        tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
        return " ".join(tokens)
    else:
        # Simple preprocessing if spaCy is not available
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        # Simple tokenization
        return text

class TriageAI:
    def __init__(self):
        self.model = None
        self.confidence_threshold = 0.6
        if ML_AVAILABLE:
            self.initialize_model()
        else:
            logger.warning("ML dependencies not available. Triage AI will use fallback mode.")
    
    def initialize_model(self):
        """Initialize and train the triage model"""
        if not ML_AVAILABLE:
            logger.warning("Cannot initialize model: ML dependencies not available")
            self.model = None
            return
            
        try:
            # Extract symptoms and severities
            symptoms = [data[0] for data in ALL_TRAINING_DATA]
            severities = [data[1] for data in ALL_TRAINING_DATA]
            
            # Preprocess symptoms
            preprocessed_symptoms = [preprocess_text(symptom) for symptom in symptoms]
            
            # Create a pipeline with TF-IDF vectorizer and Multinomial Naive Bayes classifier
            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000)),
                ('clf', MultinomialNB())
            ])
            
            # Train the model
            self.model.fit(preprocessed_symptoms, severities)
            
            logger.info("Triage AI model successfully initialized")
        except Exception as e:
            logger.error(f"Error initializing triage model: {str(e)}")
            self.model = None
    
    def assess_symptoms(self, symptoms_text):
        """
        Assess the severity of symptoms and provide recommendations
        
        Args:
            symptoms_text (str): Description of symptoms
            
        Returns:
            dict: Assessment results including severity, recommendation, and confidence
        """
        if not self.model:
            return {
                'severity': 'Unknown',
                'recommendation': 'Error in AI model. Please consult with a healthcare professional directly.',
                'confidence': 0.0
            }
        
        try:
            # Preprocess the symptoms
            preprocessed_symptoms = preprocess_text(symptoms_text)
            
            # Predict severity
            severity = self.model.predict([preprocessed_symptoms])[0]
            
            # Get prediction probabilities
            probabilities = self.model.predict_proba([preprocessed_symptoms])[0]
            
            if ML_AVAILABLE:
                confidence = float(np.max(probabilities))
            else:
                confidence = float(probabilities[0]) if probabilities.size > 0 else 0.0
            
            # Generate recommendation based on severity
            recommendation = self.generate_recommendation(severity, confidence, symptoms_text)
            
            return {
                'severity': severity,
                'recommendation': recommendation,
                'confidence': confidence
            }
        except Exception as e:
            logger.error(f"Error in symptom assessment: {str(e)}")
            return {
                'severity': 'Unknown',
                'recommendation': 'An error occurred during assessment. Please consult with a healthcare professional.',
                'confidence': 0.0
            }
    
    def generate_recommendation(self, severity, confidence, symptoms):
        """Generate a recommendation based on the assessed severity and confidence"""
        
        # Base recommendations by severity
        recommendations = {
            'Low': "Your symptoms suggest a non-urgent condition. Rest, hydrate, and monitor symptoms. If they persist for more than 2-3 days or worsen, schedule a regular appointment.",
            'Medium': "Your symptoms may require medical attention. Schedule an appointment in the next 1-2 days. Monitor for worsening symptoms.",
            'High': "Your symptoms require prompt medical attention. Please schedule an urgent appointment or visit urgent care within 24 hours.",
            'Critical': "Your symptoms suggest a potentially life-threatening condition. Seek immediate emergency medical attention or call emergency services."
        }
        
        base_recommendation = recommendations.get(severity, "Please consult with a healthcare professional for proper evaluation.")
        
        # Add confidence-based disclaimer
        if confidence < self.confidence_threshold:
            disclaimer = "\n\nNote: This is an initial assessment with limited confidence. A healthcare professional should verify this assessment."
            return base_recommendation + disclaimer
        
        return base_recommendation

# Initialize the TriageAI instance
triage_ai = TriageAI()

# Function to be called from routes
def assess_patient_symptoms(symptoms_text):
    """
    Assess patient symptoms using the AI triage tool
    
    Args:
        symptoms_text (str): Patient-reported symptoms
        
    Returns:
        dict: Assessment results
    """
    return triage_ai.assess_symptoms(symptoms_text)
