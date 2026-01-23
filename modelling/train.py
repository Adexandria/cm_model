import ast
from sklearn.calibration import LinearSVC, CalibratedClassifierCV
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_model(X_train, y_train,path='logistic_regression_model.pth', **kwargs):
    """Trains a RandomForestClassifier model and saves it to the specified path."""
    print("Training model...")

    print("Length of training data:", len(X_train))

    y_train = y_train.apply(ast.literal_eval).tolist()

    y_train = np.array(y_train, dtype=int)

    print("Shape of y_train after conversion to list:", y_train.shape)
    # Run this right before model.fit(X_train, y_train)
    print("First row of y_train:", y_train[0])
    print("Type of y_train:", type(y_train))
    print("Shape of y_train:", y_train.shape)

    classifier =  LinearSVC(
            # CHANGED: Manually boost Class 6 (assuming '6' is the label)
            # If your labels are strings, use 'class_name': 10
            class_weight={0:1, 1:1, 2:1, 3:1, 4:1, 5:1, 6:10}, 
            random_state=42,
            C=1.5,
            dual='auto'
        )
    
    calibrated_svm = CalibratedClassifierCV(classifier,method='sigmoid')
    
    model = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words=None, max_features=1000, min_df=1)),
        ('clf', OneVsRestClassifier(calibrated_svm)) 
    ])

    model.fit(X_train, y_train)

    print("Model training completed.")

    joblib.dump(model, path)
    print(f"Model saved to '{path}'")

    return model
