import pandas as pd
import os

try:
    import google.generativeai as genai
except ImportError:
    print("Required library not found. Please run: pip install google-generativeai")
    genai = None

class DiagnosisModel:
    def __init__(self):
        self.all_symptoms = []
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        try:
            dataset_path = os.path.join(project_root, 'data', 'dataset.csv')
            symptom_map_df = pd.read_csv(dataset_path)
            symptoms_set = set()
            for col in symptom_map_df.columns[1:]:
                symptoms_set.update(symptom_map_df[col].dropna().str.strip().str.lower())
            self.all_symptoms = sorted(list(symptoms_set))
        except FileNotFoundError as e:
            print(f"Warning: Dataset for suggestions not found. Auto-complete may not work. {e}")

    def get_symptom_suggestions(self, query):
        if not query or not self.all_symptoms:
            return []
        query = query.lower()
        return [s for s in self.all_symptoms if s.startswith(query)]

    def get_ai_diagnosis(self, symptoms_list):
        """
        Calls Gemini for a best-practices medical differential/triage/next-steps answer.
        """
        if not genai:
            return "Google Generative AI library not installed. Please run 'pip install google-generativeai'."
        if not symptoms_list:
            return "Please provide at least one symptom for analysis."

        try:
            genai.configure(api_key="AIzaSyCz9cQ3cnyqOx_a3GLZ50w3oWHCJDhlGso") #API KEY
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = (
                "You are an expert, cautious, step-by-step AI medical assistant. "
                "Given a patient with the following symptoms: "
                + ", ".join(symptoms_list)
                + (
                    ".\n\nProvide (1) the 2 most likely medical conditions, (2) 1-2 less likely but serious conditions NOT to miss, "
                    "(3) recommended immediate next steps/advice for the patient, and (4) urgent warning signs to watch for. "
                    "Always remind the user to consult a real healthcare professional, and clearly state this isn't medical advice.\n"
                ))

            response = model.generate_content(prompt)
            # Gemini outputs response.text as a string.
            resp = response.text.strip()
            # Always append/disclaimer for safety
            if "medical advice" not in resp.lower():
                resp += "\n\nDisclaimer: This is an AI assistant, not a licensed doctor. Always consult a healthcare professional for real medical advice."
            return resp

        except Exception as e:
            print(f"Error calling generative model: {e}")
            return f"AI analysis service is unavailable. Error: {e}\nPlease check your API key and internet connection."

