import requests
import json
import re

class UniProtAPI:
    """Class to interact with the UniProt API for protein information"""
    
    BASE_URL = "https://rest.uniprot.org/uniprotkb/"
    SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"
    
    # Well-known protein mappings for common proteins
    COMMON_PROTEINS = {
        "TP53": "P04637",
        "BRCA1": "P38398",
        "BRCA2": "P51587",
        "EGFR": "P00533",
        "INS": "P01308",
        "APP": "P05067",
        "APOE": "P02649",
        "TNF": "P01375",
        "IL6": "P05231",
        "ALB": "P02768",
        "KRAS": "P01116",
        "PTEN": "P60484",
        "VEGFA": "P15692",
        "SOD1": "P00441",
        "CFTR": "P13569"
    }
    
    def __init__(self):
        self.session = requests.Session()
        # Add headers to mimic a browser request
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Accept': 'application/json'
        })
    
    def search_protein(self, query, organism="Human", limit=5):
        """Search for a protein by name or gene symbol"""
        try:
            # Use a simpler approach - just search by gene name
            cleaned_query = query.strip().upper()
            
            # Check if this is a well-known protein first
            if cleaned_query in self.COMMON_PROTEINS:
                print(f"Found well-known protein: {cleaned_query} (UniProt: {self.COMMON_PROTEINS[cleaned_query]})")
                try:
                    # Get protein by accession
                    protein_data = self.get_protein_by_accession(self.COMMON_PROTEINS[cleaned_query])
                    if "error" not in protein_data:
                        # Format as search results
                        return {
                            "results": [protein_data],
                            "totalHits": 1
                        }
                except Exception as e:
                    print(f"Error in direct lookup for well-known protein: {str(e)}")
            
            # First try a direct accession lookup if the query looks like an accession
            if re.match(r'^[OPQ][0-9][A-Z0-9]{3}[0-9]$|^[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}$', cleaned_query):
                print(f"Query looks like a UniProt accession: {cleaned_query}")
                try:
                    # Try direct lookup
                    protein_data = self.get_protein_by_accession(cleaned_query)
                    if "error" not in protein_data:
                        # Format as search results
                        return {
                            "results": [protein_data],
                            "totalHits": 1
                        }
                except Exception as e:
                    print(f"Error in direct accession lookup: {str(e)}")
            
            # Try multiple search approaches
            
            # Approach 1: Standard search with organism filter
            print(f"Searching UniProt with query: {cleaned_query} AND organism_id:9606")
            params = {
                'query': f"{cleaned_query} AND organism_id:9606",  # 9606 is the taxonomy ID for humans
                'format': 'json',
                'size': limit
            }
            
            response = self.session.get(self.SEARCH_URL, params=params)
            if response.status_code == 200:
                search_results = response.json()
                if search_results.get("totalHits", 0) > 0:
                    return search_results
            
            # Approach 2: Try with gene name qualifier
            print(f"Trying with gene name qualifier: gene:{cleaned_query} AND organism_id:9606")
            params = {
                'query': f"gene:{cleaned_query} AND organism_id:9606",
                'format': 'json',
                'size': limit
            }
            
            response = self.session.get(self.SEARCH_URL, params=params)
            if response.status_code == 200:
                search_results = response.json()
                if search_results.get("totalHits", 0) > 0:
                    return search_results
            
            # Approach 3: Try with protein name qualifier
            print(f"Trying with protein name qualifier: protein_name:{cleaned_query} AND organism_id:9606")
            params = {
                'query': f"protein_name:{cleaned_query} AND organism_id:9606",
                'format': 'json',
                'size': limit
            }
            
            response = self.session.get(self.SEARCH_URL, params=params)
            if response.status_code == 200:
                search_results = response.json()
                if search_results.get("totalHits", 0) > 0:
                    return search_results
            
            # If all approaches fail, return an error
            print(f"No proteins found for query: {cleaned_query}")
            return {"error": f"No protein found for query: {cleaned_query}"}
            
        except Exception as e:
            print(f"Error searching for protein: {str(e)}")
            return {"error": str(e)}
    
    def get_protein_by_accession(self, accession):
        """Get protein data by UniProt accession"""
        try:
            url = f"{self.BASE_URL}{accession}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting protein by accession: {response.status_code}")
                return {"error": f"Error getting protein by accession: {response.status_code}"}
                
        except Exception as e:
            print(f"Error in get_protein_by_accession: {str(e)}")
            return {"error": str(e)}
    
    def extract_protein_info(self, protein_data):
        """Extract relevant information from UniProt protein data"""
        if "error" in protein_data:
            return protein_data
        
        try:
            # Basic information
            info = {
                "accession": protein_data.get("primaryAccession", ""),
                "name": protein_data.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", ""),
                "gene_names": [gene.get("value", "") for gene in protein_data.get("genes", [{}])[0].get("geneName", [])],
                "organism": protein_data.get("organism", {}).get("scientificName", ""),
                "sequence": protein_data.get("sequence", {}).get("value", ""),
                "length": protein_data.get("sequence", {}).get("length", 0),
                "function": "",
                "subcellular_location": [],
                "go_terms": []
            }
            
            # Extract function
            for comment in protein_data.get("comments", []):
                if comment.get("commentType") == "FUNCTION":
                    info["function"] = comment.get("texts", [{}])[0].get("value", "")
                elif comment.get("commentType") == "SUBCELLULAR LOCATION":
                    for location in comment.get("subcellularLocations", []):
                        if "location" in location:
                            info["subcellular_location"].append(location["location"].get("value", ""))
            
            # Extract GO terms
            for dbRef in protein_data.get("uniProtKBCrossReferences", []):
                if dbRef.get("database") == "GO":
                    term = {
                        "id": dbRef.get("id", ""),
                        "term": "",
                        "category": ""
                    }
                    for property in dbRef.get("properties", []):
                        if property.get("key") == "GoTerm":
                            term["term"] = property.get("value", "")
                        elif property.get("key") == "GoEvidenceType":
                            term["evidence"] = property.get("value", "")
                    info["go_terms"].append(term)
            
            # Extract disease associations
            info["diseases"] = []
            for comment in protein_data.get("comments", []):
                if comment.get("commentType") == "DISEASE":
                    disease = {
                        "name": comment.get("disease", {}).get("diseaseName", {}).get("value", ""),
                        "description": comment.get("texts", [{}])[0].get("value", "") if comment.get("texts") else ""
                    }
                    info["diseases"].append(disease)
            
            return info
        except Exception as e:
            return {"error": f"Failed to extract protein information: {str(e)}"}

    def get_protein_summary(self, query):
        """Get a summary of protein information based on a query"""
        print(f"Getting protein summary for: {query}")
        
        try:
            # Try to get data from the API
            search_results = self.search_protein(query)
            
            # Check for errors in the search results
            if isinstance(search_results, dict) and "error" in search_results:
                print(f"Error in search results: {search_results['error']}")
                return {"error": f"No protein found for query: {query}"}
            
            # Check if any results were found
            if not search_results or search_results.get("totalHits", 0) == 0:
                print(f"No proteins found for query: {query}")
                return {"error": f"No protein found for query: {query}"}
            
            try:
                # Get the first result
                results = search_results.get("results", [])
                if not results:
                    print("No results found in search response")
                    return {"error": f"No protein found for query: {query}"}
                    
                first_hit = results[0]
                accession = first_hit.get("primaryAccession")
                
                if not accession:
                    print("No accession found in first hit")
                    return {"error": f"No protein found for query: {query}"}
                
                print(f"Found protein with accession: {accession}")
                
                # Get detailed information
                protein_data = self.get_protein_by_accession(accession)
                
                # Check for errors in the detailed data
                if isinstance(protein_data, dict) and "error" in protein_data:
                    print(f"Error in protein data: {protein_data['error']}")
                    return {"error": f"No protein found for query: {query}"}
                
                # Extract and return the protein information
                result = self.extract_protein_info(protein_data)
                
                # Final check to ensure we have valid data
                if isinstance(result, dict) and "error" in result:
                    print(f"Error extracting protein info: {result['error']}")
                    return {"error": f"No protein found for query: {query}"}
                    
                return result
                
            except Exception as e:
                print(f"Error processing protein data: {str(e)}")
                return {"error": f"Error retrieving protein data: {str(e)}"}
                
        except Exception as e:
            print(f"Unexpected error in get_protein_summary: {str(e)}")
            return {"error": f"Error retrieving protein data: {str(e)}"}
