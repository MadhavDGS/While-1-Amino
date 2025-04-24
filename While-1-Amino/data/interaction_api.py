import requests
import json
import pandas as pd

class ProteinInteractionAPI:
    """Class to interact with STRING API for protein-protein interactions"""
    
    STRING_API_URL = "https://string-db.org/api"
    API_VERSION = "11.0"
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_string_id(self, query, species=9606):  # 9606 is human
        """Convert a protein name to STRING ID"""
        url = f"{self.STRING_API_URL}/{self.API_VERSION}/json/get_string_ids"
        
        params = {
            "identifiers": query,
            "species": species,
            "limit": 1,
            "echo_query": 1
        }
        
        response = self.session.post(url, data=params)
        
        if response.status_code == 200:
            result = response.json()
            if result and len(result) > 0:
                return result[0].get("stringId")
            else:
                return None
        else:
            return None
    
    def get_interactions(self, string_id, required_score=400, limit=10):
        """Get protein-protein interactions for a given STRING ID"""
        if not string_id:
            return {"error": "Invalid STRING ID"}
        
        url = f"{self.STRING_API_URL}/{self.API_VERSION}/json/interactions"
        
        params = {
            "identifiers": string_id,
            "required_score": required_score,
            "limit": limit
        }
        
        response = self.session.post(url, data=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to retrieve interactions: {response.status_code}"}
    
    def get_network_image(self, string_id, required_score=400, limit=10):
        """Get URL for network image from STRING"""
        if not string_id:
            return None
        
        network_url = f"https://string-db.org/cgi/networkList?identifiers={string_id}&required_score={required_score}&limit={limit}&network_flavor=evidence&species=9606"
        
        return network_url
    
    def format_interactions(self, interactions):
        """Format interaction data into a more usable structure"""
        if isinstance(interactions, dict) and "error" in interactions:
            return interactions
        
        formatted = []
        for interaction in interactions:
            formatted.append({
                "source": interaction.get("stringId_A"),
                "source_name": interaction.get("preferredName_A", ""),
                "target": interaction.get("stringId_B"),
                "target_name": interaction.get("preferredName_B", ""),
                "score": interaction.get("score", 0),
                "evidence": [
                    {"type": "neighborhood", "score": interaction.get("neighborhood", 0)},
                    {"type": "fusion", "score": interaction.get("fusion", 0)},
                    {"type": "cooccurence", "score": interaction.get("cooccurence", 0)},
                    {"type": "coexpression", "score": interaction.get("coexpression", 0)},
                    {"type": "experimental", "score": interaction.get("experimental", 0)},
                    {"type": "database", "score": interaction.get("database", 0)},
                    {"type": "textmining", "score": interaction.get("textmining", 0)}
                ]
            })
        
        return formatted
    
    def get_interaction_summary(self, query, required_score=400, limit=10):
        """Get a summary of protein interactions based on a query"""
        # Convert query to STRING ID
        string_id = self.get_string_id(query)
        
        if not string_id:
            return {"error": f"Could not find STRING ID for query: {query}"}
        
        # Get interactions
        interactions = self.get_interactions(string_id, required_score, limit)
        
        # Format interactions
        formatted_interactions = self.format_interactions(interactions)
        
        # Get network image URL
        network_url = self.get_network_image(string_id, required_score, limit)
        
        return {
            "query": query,
            "string_id": string_id,
            "interactions": formatted_interactions,
            "network_url": network_url,
            "total": len(formatted_interactions) if isinstance(formatted_interactions, list) else 0
        }
