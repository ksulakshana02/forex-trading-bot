import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os
from .base import BaseStrategy

class MLEnsembleStrategy(BaseStrategy):
    def __init__(self, model_path="models/rf_model.pkl"):
        super().__init__("ML Ensemble")
        self.model_path = model_path
        self.model = None
        self.feature_cols = ['rsi', 'macd', 'adx', 'volatility_20', 'z_score', 'log_returns']
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print(f"[ML] Loaded model from {self.model_path}")
            except Exception as e:
                print(f"[ML] Failed to load model: {e}")
        else:
            print("[ML] No model found. Training required.")

    def train_model(self, df: pd.DataFrame):
        """
        Train the model on provided data and save it.
        """
        print("[ML] Starting training...")
        
        # Prepare Target: 1 if price rises in next 4 periods, else 0
        df['target'] = (df['close'].shift(-4) > df['close']).astype(int)
        
        # Drop NaNs created by shift and indicators
        data = df.dropna()
        
        if len(data) < 500:
            print("[ML] Insufficient data for training")
            return
            
        X = data[self.feature_cols]
        y = data['target']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        self.model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        self.model.fit(X_train, y_train)
        
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        print(f"[ML] Training completed. Train Acc: {train_score:.2f}, Test Acc: {test_score:.2f}")
        
        # Save model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        print(f"[ML] Model saved to {self.model_path}")

    def generate_signal(self, df: pd.DataFrame):
        if self.model is None:
            return None, 0.0
            
        latest_features = df[self.feature_cols].iloc[-1:].fillna(0)
        
        try:
            prediction = self.model.predict(latest_features)[0]
            confidence = self.model.predict_proba(latest_features)[0].max() # Raw probability
            
            # Map prob to confidence score
            # If prob is 0.55, confidence is low. If 0.8, high.
            # Scale (0.5, 1.0) -> (0.0, 1.0) ideally, or just use raw prob if > threshold
            
            if confidence < 0.55:
                return None, 0.0
                
            signal = "BUY" if prediction == 1 else "SELL"
            
            return signal, confidence
        except Exception as e:
            print(f"[ML] Prediction error: {e}")
            return None, 0.0
