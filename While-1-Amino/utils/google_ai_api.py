"""
Google AI Studio API integration for AminoVerse
Provides advanced natural language understanding for protein-related queries
"""

import requests
import json
import os

class GoogleAIAPI:
    """
    Handles interactions with Google AI Studio API for natural language understanding
    and advanced question answering about proteins
    """
    
    def __init__(self, api_key=None):
        """Initialize with API key"""
        self.api_key = api_key or os.environ.get("GOOGLE_AI_API_KEY")
        self.api_url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
        
    def set_api_key(self, api_key):
        """Set or update the API key"""
        self.api_key = api_key
        
    def is_configured(self):
        """Check if the API is properly configured"""
        return self.api_key is not None and self.api_key.strip() != ""
        
    def answer_protein_question(self, protein_data, question):
        """
        Use Google AI to answer a question about a protein based on the provided data
        
        Args:
            protein_data (dict): Comprehensive protein data from various sources
            question (str): The user's question about the protein
            
        Returns:
            dict: Response with answer and any relevant visualization data
        """
        if not self.is_configured():
            return {
                "type": "error",
                "answer": "Google AI API is not configured. Please set a valid API key."
            }
            
        try:
            # Extract relevant protein information for context
            basic_info = protein_data.get("basic_info", {})
            protein_name = basic_info.get("name", "Unknown protein")
            gene_names = ", ".join(basic_info.get("gene_names", ["Unknown"]))
            organism = basic_info.get("organism", "Unknown")
            function = basic_info.get("function", "Function unknown")
            
            # Create a prompt with protein context and the user's question
            prompt = f"""
            I need information about the protein {protein_name} (Gene: {gene_names}) from {organism}.
            
            Here's what I know about this protein:
            - Function: {function}
            
            The user is asking: {question}
            
            Please provide a concise, scientifically accurate answer based on the protein information.
            If the answer relates to diseases, interactions, structure, or drugs, please indicate this in your response
            by starting with [DISEASE], [INTERACTION], [STRUCTURE], or [DRUG] so the appropriate visualization can be shown.
            """
            
            # Prepare the request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024
                }
            }
            
            # Make the API request
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload)
            )
            
            # Process the response
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract the generated text
                try:
                    answer_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Determine the answer type for visualization
                    answer_type = "general"
                    if "[DISEASE]" in answer_text:
                        answer_type = "disease"
                        answer_text = answer_text.replace("[DISEASE]", "").strip()
                    elif "[INTERACTION]" in answer_text:
                        answer_type = "interaction"
                        answer_text = answer_text.replace("[INTERACTION]", "").strip()
                    elif "[STRUCTURE]" in answer_text:
                        answer_type = "structure"
                        answer_text = answer_text.replace("[STRUCTURE]", "").strip()
                    elif "[DRUG]" in answer_text:
                        answer_type = "drug"
                        answer_text = answer_text.replace("[DRUG]", "").strip()
                    
                    # Return the answer with appropriate type
                    result = {
                        "type": answer_type,
                        "answer": answer_text
                    }
                    
                    # Add visualization data if available
                    if answer_type == "disease":
                        result["diseases"] = protein_data.get("disease_drug", {}).get("diseases", [])
                    elif answer_type == "interaction":
                        result["interactions"] = protein_data.get("interactions", {}).get("interactions", [])
                    elif answer_type == "structure":
                        result["structures"] = protein_data.get("structure", {}).get("structures", [])
                    elif answer_type == "drug":
                        result["drugs"] = protein_data.get("disease_drug", {}).get("drugs", [])
                    
                    return result
                    
                except (KeyError, IndexError) as e:
                    return {
                        "type": "error",
                        "answer": f"Error parsing AI response: {str(e)}"
                    }
            else:
                return {
                    "type": "error",
                    "answer": f"API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "type": "error",
                "answer": f"Error calling Google AI API: {str(e)}"
            }
            
    def enhance_protein_summary(self, protein_data):
        """
        Generate an enhanced summary of the protein using Google AI
        
        Args:
            protein_data (dict): Comprehensive protein data
            
        Returns:
            str: Enhanced protein summary
        """
        if not self.is_configured():
            return "Google AI API is not configured. Using standard protein description."
            
        try:
            # Extract protein information
            basic_info = protein_data.get("basic_info", {})
            protein_name = basic_info.get("name", "Unknown protein")
            gene_names = ", ".join(basic_info.get("gene_names", ["Unknown"]))
            organism = basic_info.get("organism", "Unknown")
            function = basic_info.get("function", "Function unknown")
            
            # Get disease associations
            diseases = protein_data.get("disease_drug", {}).get("diseases", [])
            disease_names = [d.get("disease_name", "") for d in diseases[:3]]
            disease_text = ", ".join(disease_names) if disease_names else "No known diseases"
            
            # Create a prompt for the summary
            prompt = f"""
            Create a concise scientific summary (3-4 sentences) for the protein {protein_name} (Gene: {gene_names}) from {organism}.
            
            Key information:
            - Function: {function}
            - Associated diseases: {disease_text}
            
            The summary should be scientifically accurate and highlight the most important aspects of this protein's function and significance.
            """
            
            # Prepare the request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 512
                }
            }
            
            # Make the API request
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload)
            )
            
            # Process the response
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract the generated text
                try:
                    summary = response_data["candidates"][0]["content"]["parts"][0]["text"]
                    return summary.strip()
                except (KeyError, IndexError):
                    return function  # Fall back to basic function description
            else:
                return function  # Fall back to basic function description
                
        except Exception:
            return function  # Fall back to basic function description
            
    def generate_protein_info(self, query):
        """
        Generate basic protein information using Google AI when database retrieval fails
        
        Args:
            query (str): The protein or gene name to generate information for
            
        Returns:
            dict: A dictionary containing basic protein information
        """
        if not self.is_configured():
            return {"error": "Google AI API is not configured."}
            
        try:
            # Create a prompt for protein information
            prompt = f"""
            Generate comprehensive scientific information about the protein encoded by the gene {query} in humans.
            
            Please format your response as a structured JSON object with the following fields:
            - name: The full protein name
            - gene_names: A list of gene symbols (primary and aliases)
            - accession: A fictional UniProt ID (format: P#####)
            - organism: The organism (should be Homo sapiens)
            - length: Approximate amino acid length
            - subcellular_locati
            on: A list of cellular locations
            - function: A detailed paragraph about the protein's function and significance
            
            Be scientifically accurate and comprehensive.
            """
            
            # Prepare the request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024
                }
            }
            
            # Make the API request
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload)
            )
            
            # Process the response
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract the generated text
                try:
                    text_response = response_data["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Extract JSON from the response
                    import re
                    json_match = re.search(r'```json\n(.*?)\n```', text_response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        json_str = text_response
                    
                    # Clean up the string to ensure it's valid JSON
                    json_str = re.sub(r'```.*?```', '', json_str, flags=re.DOTALL)
                    json_str = re.sub(r'```', '', json_str)
                    
                    # Parse the JSON
                    try:
                        protein_info = json.loads(json_str)
                        
                        # Ensure all required fields are present
                        required_fields = ["name", "gene_names", "accession", "organism", "length", "subcellular_location", "function"]
                        for field in required_fields:
                            if field not in protein_info:
                                if field == "gene_names":
                                    protein_info[field] = [query.upper()]
                                elif field == "subcellular_location":
                                    protein_info[field] = ["Unknown"]
                                else:
                                    protein_info[field] = "Unknown"
                        
                        # Add a note that this is AI-generated
                        protein_info["source"] = "AI-generated"
                        
                        return protein_info
                        
                    except json.JSONDecodeError:
                        # If JSON parsing fails, create a structured response manually
                        return {
                            "name": f"{query.upper()} protein",
                            "gene_names": [query.upper()],
                            "accession": f"P{100000 + hash(query) % 900000}",  # Generate a fictional ID
                            "organism": "Homo sapiens",
                            "length": 500,  # Default length
                            "subcellular_location": ["Unknown"],
                            "function": f"Information about {query} could not be retrieved from databases. This is AI-generated placeholder data.",
                            "source": "AI-generated"
                        }
                        
                except (KeyError, IndexError):
                    return {"error": "Failed to parse AI response"}
            else:
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Error generating protein information: {str(e)}"}
