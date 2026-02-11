import os
import sys
import json
import google.generativeai as genai
from google.cloud import bigquery

class KnowledgeRetrieverAgent:
    def __init__(self, project_id, api_key=None):
        self.project_id = project_id
        if not api_key:
            api_key = os.environ.get("GOOGLE_GENAI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.bq_client = bigquery.Client(project=project_id)
        self.dataset_id = "support_tickets_staging"

    def retrieve_solutions(self, ticket_description: str, category: str, top_k: int = 3) -> list:
        """
        Retrieves relevant solutions from BigQuery and ranks them using Gemini.
        """
        # 1. Query BigQuery for candidates
        query = f"""
            SELECT solution_id, problem_description, solution_text, success_rate
            FROM `{self.project_id}.{self.dataset_id}.knowledge_base`
            WHERE category = @category
            ORDER BY success_rate DESC
            LIMIT {top_k * 3}
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("category", "STRING", category),
            ]
        )
        
        try:
            query_job = self.bq_client.query(query, job_config=job_config)
            candidates = [dict(row) for row in query_job]
            
            if not candidates:
                return []
                
            # 2. Use Gemini to rank candidates
            prompt = f"""
            Rank the following solutions by relevance to this support ticket:
            Ticket: {ticket_description}

            Solutions:
            {json.dumps(candidates, indent=2)}

            Return ONLY a JSON list of solution_ids in order of relevance, 
            limited to the top {top_k} results.
            """
            
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            ordered_ids = json.loads(text)
            
            # Map back to full dictionary
            id_to_solution = {c["solution_id"]: c for c in candidates}
            results = [id_to_solution[sid] for sid in ordered_ids if sid in id_to_solution]

            
            return results[:top_k]
            
        except Exception as e:
            print(f"Error in retrieval: {e}")
            return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python knowledge_retriever_agent.py <project_id>")
        sys.exit(1)
        
    api_key = None
    if os.path.exists("../.env"):
        with open("../.env") as f:
            for line in f:
                if line.startswith("GOOGLE_GENAI_API_KEY="):
                    api_key = line.split("=")[1].strip()

    project_id = sys.argv[1]
    agent = KnowledgeRetrieverAgent(project_id, api_key=api_key)
    results = agent.retrieve_solutions("My payment was declined", "billing")
    print(json.dumps(results, indent=2))
