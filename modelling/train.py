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

    print("Length of training labels:", len(y_train))

    dual = kwargs.get('dual', 'auto')
    if dual == 'true':
        dual = True
    elif dual == 'false':
        dual = False
    else:
        dual = 'auto'

    classifier =  LinearSVC(
            class_weight=kwargs.get('class_weight', {0:1, 1:1, 2:1, 3:1, 4:1, 5:1, 6:10}), 
            random_state=kwargs.get('random_state', 42),
            C=kwargs.get('c', 1.5),
            dual=dual
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
