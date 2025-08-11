import pandas as pd
import os

try:
    import google.generativeai as genai
except ImportError:
    print("Required library not found. Please run: pip install google-generativeai")
    # This allows the app to still run for local suggestions even if the genai library is missing.
    genai = None

class DiagnosisModel:
    def __init__(self):
        """
        Initializes the model, loading the dataset for symptom suggestions.
        """
        self.all_symptoms = []
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        try:
            # The dataset is used for the fast auto-suggestion feature
            dataset_path = os.path.join(project_root, 'data', 'dataset.csv')
            symptom_map_df = pd.read_csv(dataset_path)
            
            symptoms_set = set()
            for col in symptom_map_df.columns[1:]:
                symptoms_set.update(symptom_map_df[col].dropna().str.strip().str.lower())
            self.all_symptoms = sorted(list(symptoms_set))
        except FileNotFoundError as e:
            print(f"Warning: Dataset for suggestions not found. Auto-complete may not work. {e}")

    def get_symptom_suggestions(self, query):
        """Returns a list of symptoms from the local dataset for auto-complete."""
        if not query or not self.all_symptoms:
            return []
        query = query.lower()
        return [s for s in self.all_symptoms if s.startswith(query)]

    def get_ai_diagnosis(self, symptoms_list):
        """
        Calls a generative AI model to get a diagnosis based on symptoms.
        """
        if not genai:
            return "Google Generative AI library not installed. Please run 'pip install google-generativeai'."
            
        if not symptoms_list:
            return "Please provide at least one symptom for analysis."

        try:
            
            genai.configure(api_key="AIzaSyDEpAqbvzLIZiFinneHD4DrYXCbYjLCdPo")
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = (
                "Given the following symptoms: "
                + ", ".join(symptoms_list)
                + ". What are the possible diagnoses and recommended next steps?"
            )
            response = model.generate_content(prompt)
            return response.text
            
            # Using a high-quality placeholder response for demonstration
            placeholder_response = (
                "Possible Conditions:\n"
                "1. Influenza (Flu):The combination of fever, headache, and fatigue is a classic presentation for the flu virus.\n"
                "2. COVID-19: These symptoms are also highly characteristic of a COVID-19 infection.\n"
                "3. Sinusitis: If headache is the primary symptom and there is facial pressure, a sinus infection could be the cause.\n\n"
                "Recommended Next Steps:\n"
                "- Isolate to prevent potential spread and get significant rest.\n"
                "- Stay well-hydrated by drinking plenty of water, broth, or tea.\n"
                "- Use over-the-counter pain relievers like ibuprofen or acetaminophen to manage fever and aches."
            )
            return placeholder_response

        except Exception as e:
            print(f"Error calling generative model: {e}")
            return "I'm sorry, the AI analysis service is currently unavailable. Please check your API key and internet connection."