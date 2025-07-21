import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
import re

# Get the absolute path to the project's root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class DiagnosisModel:
    def __init__(self):
        """
        Initializes the model by loading all necessary datasets and preparing data structures.
        """
        self.symptom_map_df = None
        self.symptom_severity_df = None
        self.symptom_precaution_df = None
        self.all_symptoms = []
        self.severity_dict = {}

        try:
            # --- Using the correct 'data' folder name ---
            dataset_path = os.path.join(project_root, 'data', 'dataset.csv')
            severity_path = os.path.join(project_root, 'data', 'Symptom-severity.csv')
            precaution_path = os.path.join(project_root, 'data', 'symptom_precaution.csv')

            self.symptom_map_df = pd.read_csv(dataset_path)
            self.symptom_severity_df = pd.read_csv(severity_path)
            self.symptom_precaution_df = pd.read_csv(precaution_path)

            # Prepare symptom list for autocomplete suggestions
            symptoms_set = set()
            for col in self.symptom_map_df.columns[1:]:
                symptoms_set.update(self.symptom_map_df[col].dropna().str.strip().str.lower())
            self.all_symptoms = sorted(list(symptoms_set))

            # Prepare severity dictionary for weighted diagnosis
            self.symptom_severity_df['Symptom'] = self.symptom_severity_df['Symptom'].str.lower().str.strip()
            self.severity_dict = self.symptom_severity_df.set_index('Symptom')['weight'].to_dict()

        except FileNotFoundError as e:
            print(f"Error loading dataset: {e}. Please ensure all CSV files are in the 'data' folder.")

    def get_symptom_suggestions(self, query):
        """Returns a list of symptoms that start with the user's query."""
        if not query:
            return []
        query = query.lower()
        return [s for s in self.all_symptoms if s.startswith(query)]

    def predict_disease(self, user_symptoms):
        """
        Predicts disease based on user symptoms, weighted by severity.
        """
        if self.symptom_map_df is None or not user_symptoms:
            return "Not enough information.", 0

        user_symptoms = set(s.lower() for s in user_symptoms)
        disease_scores = {}
        
        for index, row in self.symptom_map_df.iterrows():
            disease = row['Disease']
            symptoms_for_disease = set(s.lower().strip() for s in row[1:].dropna())
            
            matched_symptoms = user_symptoms.intersection(symptoms_for_disease)
            
            if matched_symptoms:
                score = sum(self.severity_dict.get(s, 0) for s in matched_symptoms)
                if score > 0:
                    disease_scores[disease] = score
        
        if not disease_scores:
            return "Could not identify a likely disease.", 0

        # Return the disease with the highest score
        best_match_disease = max(disease_scores, key=disease_scores.get)
        return best_match_disease, len(user_symptoms)

    def get_precautions(self, disease):
        """Fetches precautions for a given disease from the dataset."""
        try:
            precautions = self.symptom_precaution_df[self.symptom_precaution_df['Disease'] == disease]
            if not precautions.empty:
                return [col for col in precautions.iloc[0, 1:].dropna()]
            return ["No specific precautions found."]
        except Exception:
            return ["Could not retrieve precautions."]

    @staticmethod
    def scrape_disease_description(disease_name):
        """Scrapes a brief description of the disease from Wikipedia."""
        try:
            url = f"https://en.wikipedia.org/wiki/{disease_name.replace(' ', '_')}"
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            paragraphs = soup.select("div.mw-parser-output > p")
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 150:
                
                    text = re.sub(r'\[\d+\]', '', text)
                    return text 
            
            return "No detailed summary was found on Wikipedia."
            
        except requests.exceptions.RequestException:
            return "Failed to fetch information online. Please check your connection."