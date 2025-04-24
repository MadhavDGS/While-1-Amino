"""PDB API utilities for finding similar protein structures"""
import requests
import json

def find_similar_pdb_structures(uniprot_id):
    """
    Find similar PDB structures for a given UniProt ID using both exact and sequence similarity search
    
    Args:
        uniprot_id: UniProt ID of the protein
        
    Returns:
        List of similar structures with their details
    """
    try:
        # Use RCSB PDB search API to find similar structures
        search_url = "https://search.rcsb.org/rcsbsearch/v2/query"
        
        # First try exact match
        exact_search_json = {
            "query": {
                "type": "group",
                "logical_operator": "and",
                "nodes": [
                    {
                        "type": "terminal",
                        "service": "text",
                        "parameters": {
                            "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                            "operator": "exact_match",
                            "value": uniprot_id
                        }
                    },
                    {
                        "type": "terminal",
                        "service": "text",
                        "parameters": {
                            "attribute": "rcsb_entity_source_organism.taxonomy_lineage.name",
                            "operator": "exact_match",
                            "value": "Homo sapiens"
                        }
                    }
                ]
            },
            "return_type": "entry"
        }

        # Then try sequence similarity search
        sequence_search_json = {
            "query": {
                "type": "group",
                "logical_operator": "and",
                "nodes": [
                    {
                        "type": "terminal",
                        "service": "sequence",
                        "parameters": {
                            "target": "pdb_protein_sequence",
                            "value": uniprot_id,
                            "identity_cutoff": 0.4,  # 40% sequence identity cutoff
                            "evalue_cutoff": 0.1
                        }
                    }
                ]
            },
            "return_type": "entry"
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Try exact match first
        similar_structures = []
        response = requests.post(search_url, headers=headers, data=json.dumps(exact_search_json))
        
        if response.status_code == 200:
            results = response.json()
            if "result_set" in results and results["result_set"]:
                similar_structures.extend(get_structure_details(results["result_set"], is_exact_match=True))
        
        # If no exact matches, try sequence similarity search
        if not similar_structures:
            response = requests.post(search_url, headers=headers, data=json.dumps(sequence_search_json))
            if response.status_code == 200:
                results = response.json()
                if "result_set" in results and results["result_set"]:
                    similar_structures.extend(get_structure_details(results["result_set"], is_exact_match=False))
        
        return similar_structures
            
    except Exception as e:
        print(f"Error finding similar PDB structures: {str(e)}")
        return []

def get_structure_details(result_set, is_exact_match=False):
    """Helper function to get structure details from PDB"""
    structures = []
    for result in result_set:
        try:
            pdb_id = result["identifier"]
            
            # Get structure details
            details_url = f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
            details_response = requests.get(details_url)
            
            if details_response.status_code == 200:
                structure_data = details_response.json()
                
                # Extract relevant information
                method = structure_data.get("exptl", [{}])[0].get("method", "Unknown method")
                resolution = structure_data.get("rcsb_entry_info", {}).get("resolution_combined", "N/A")
                title = structure_data.get("struct", {}).get("title", "")
                
                if resolution != "N/A":
                    resolution = f"{resolution:.1f} Å"
                
                structures.append({
                    "pdb_id": pdb_id,
                    "method": method,
                    "resolution": resolution,
                    "title": title,
                    "viewer_url": f"https://www.rcsb.org/structure/{pdb_id}",
                    "is_exact_match": is_exact_match,
                    "similarity_score": result.get("score", 1.0) if not is_exact_match else 1.0
                })
        except Exception as e:
            print(f"Error getting details for structure {pdb_id}: {str(e)}")
            continue
    
    # Sort by similarity score and resolution
    structures.sort(key=lambda x: (-x["similarity_score"], 
                                 float(x["resolution"].replace(" Å", "")) if x["resolution"] != "N/A" else float('inf')))
    
    return structures
