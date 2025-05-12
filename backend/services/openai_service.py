import openai
import json

class OpenAIService:
    def __init__(self, api_key):
        self.api_key = api_key
        openai.api_key = api_key
    
    def generate_questions(self, company, role, num_questions=2, question_type=None):
        """Generate interview questions using GPT-4o."""
        # Get a human-readable description of the question type
        question_type_desc = self._get_question_type_description(question_type)
        
        system_message = f"""
        You are an expert interviewer for {company} Product Management roles.
        Generate {num_questions} challenging {question_type_desc} interview questions for a {role} position.
        
        For each question, provide:
        1. The main question
        2. 2-3 follow-up questions
        3. Context about why this question matters for the role
        
        Format your response as a JSON object with this exact structure:
        {{
            "questions": [
                {{
                    "mainQuestion": "Your question here",
                    "followUpQuestions": ["Follow-up 1", "Follow-up 2"],
                    "context": "Why this question matters"
                }},
                ... more questions ...
            ]
        }}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Generate {question_type_desc} PM interview questions for a {role} position at {company}."}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            raw_content = response.choices[0].message.content
            print(f"Raw OpenAI response: {raw_content[:200]}...")  # Log first 200 chars
            
            response_data = json.loads(raw_content)
            
            # Format the response to match what the frontend expects
            formatted_response = {
                "questions": []
            }
            
            for i, q in enumerate(response_data.get("questions", [])):
                formatted_response["questions"].append({
                    "question_id": f"llm-{i+1}",
                    "question_text": q.get("mainQuestion", ""),
                    "follow_ups": q.get("followUpQuestions", []),
                    "category": question_type_desc if question_type else "Product Management",
                    "company_specific": True,
                    "company": company
                })
            
            # Check if we have empty questions and log it
            if not formatted_response["questions"] or not any(q.get("question_text") for q in formatted_response["questions"]):
                print("WARNING: OpenAI generated empty questions")
            
            return formatted_response
            
        except Exception as e:
            print(f"Error generating questions: {e}")
            return {"error": str(e), "questions": []}
    
    def _get_question_type_description(self, question_type):
        """Convert question_type code to human-readable description."""
        if not question_type:
            return "Product Management"
            
        type_mapping = {
            "product-strategy": "Product Strategy",
            "product-design": "Product Design",
            "technical": "Technical",
            "market-analysis": "Market Analysis",
            "behavioral": "Behavioral",
            "case-study": "Case Study",
            "estimation": "Estimation",
            "user-experience": "User Experience",
            "data-analysis": "Data Analysis"
        }
        
        return type_mapping.get(question_type, "Product Management")
    
    def generate_follow_up(self, question, answer, company, role):
        """Generate a follow-up question based on the candidate's response."""
        system_message = f"""
        You are an expert interviewer for {company} Product Management roles.
        The candidate just answered a question. Based on their response, generate ONE insightful follow-up question 
        that digs deeper or explores an area they didn't fully address. Be specific, challenging, and direct.
        
        Return only the follow-up question text with no additional context, explanation, or prefixes like "Follow-up question:".
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Original Question: {question}\n\nCandidate's Answer: {answer}\n\nGenerate one follow-up question:"}
                ],
                max_tokens=100
            )
            
            follow_up = response.choices[0].message.content.strip()
            print(f"Generated follow-up: {follow_up}")
            
            # Just return whatever was generated, even if empty
            return follow_up
        except Exception as e:
            print(f"Error generating follow-up: {e}")
            return None
    
    def evaluate_response(self, question, response, company, role):
        """Evaluate the interview response using GPT-4o."""
        system_message = f"""
        You are an expert Product Management interviewer for {company}.
        Evaluate this candidate's response to the following question for a {role} position.
        
        Provide structured feedback in JSON format with these fields:
        1. strengths: List 3-4 specific strengths of the response
        2. weaknesses: List 3-4 areas for improvement
        3. improvement_tips: Provide 3-4 specific tips to improve the answer. Also give an ideal response to the question including a proper structure and perhaps the framework/frameworks you used.
        4. rating: Rate the answer on a scale of 1-20
        5. explanation: Brief explanation of the rating
        
        Be specific, constructive, and a bit strict in your evaluation. You want this person to be extremely ready. Focus on PM skills like:
        - Strategic thinking
        - Customer understanding
        - Technical knowledge
        - Communication clarity
        - Problem-solving approach
        - Business acumen
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Question: {question}\n\nCandidate's Response: {response}"}
                ],
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error evaluating response: {e}")
            return {"error": str(e)}