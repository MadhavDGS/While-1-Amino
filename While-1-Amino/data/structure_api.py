import requests
import json
import re

class ProteinStructureAPI:
    """Class to interact with PDB and AlphaFold APIs for protein structure information"""
    
    PDB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
    PDB_DATA_URL = "https://data.rcsb.org/rest/v1/core/entry/"
    ALPHAFOLD_URL = "https://alphafold.ebi.ac.uk/api/"
    
    VALID_SOURCES = {"pdb", "alphafold"}
    
    def __init__(self):
        self.session = requests.Session()
    
    def validate_structure_info(self, structure_info):
        """Validate and normalize structure information"""
        if not isinstance(structure_info, dict):
            raise ValueError("Structure info must be a dictionary")
            
        # Ensure required fields
        if "id" not in structure_info:
            raise ValueError("Structure info must contain an 'id' field")
            
        # Normalize source field
        source = structure_info.get("source", "").lower()
        if not source:
            # Try to determine source from ID format
            if re.match(r'^[0-9][A-Za-z0-9]{3}$', structure_info["id"]):
                source = "pdb"
            elif re.match(r'^[A-Z][0-9][A-Z0-9]{3}[0-9]$', structure_info["id"]):
                source = "alphafold"
            else:
                raise ValueError(f"Invalid or missing source for structure ID: {structure_info['id']}")
                
        if source not in self.VALID_SOURCES:
            raise ValueError(f"Invalid source '{source}'. Must be one of: {', '.join(self.VALID_SOURCES)}")
            
        structure_info["source"] = source
        return structure_info
    
    def search_pdb(self, query, organism="Human"):
        """Search for protein structures in PDB by gene name or UniProt accession"""
        try:
            # Check if the query is a UniProt accession (format: [A-Z][0-9][A-Z0-9]{3}[0-9])
            is_uniprot = bool(re.match(r'^[A-Z][0-9][A-Z0-9]{3}[0-9]$', query))
            
            if is_uniprot:
                # First try exact match with UniProt ID
                search_json = {
                    "query": {
                        "type": "terminal",
                        "service": "text",
                        "parameters": {
                            "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                            "operator": "exact_match",
                            "value": query
                        }
                    },
                    "return_type": "entry"
                }
            else:
                # Search by gene name
                search_json = {
                    "query": {
                        "type": "terminal",
                        "service": "text",
                        "parameters": {
                            "attribute": "rcsb_gene_name.value",
                            "operator": "exact_match",
                            "value": query
                        }
                    },
                    "return_type": "entry"
                }
            
            # Add organism filter for humans if specified
            if organism.lower() == "human":
                search_json = {
                    "query": {
                        "type": "group",
                        "logical_operator": "and",
                        "nodes": [
                            search_json["query"],
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
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = self.session.post(self.PDB_SEARCH_URL, headers=headers, data=json.dumps(search_json))
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"PDB API returned status code: {response.status_code}")
                return {"error": f"Failed to retrieve PDB data: {response.status_code}"}
                
        except Exception as e:
            print(f"Error searching PDB: {str(e)}")
            return {"error": str(e)}
    
    def get_alphafold_structure(self, uniprot_id):
        """Get AlphaFold structure for a protein by UniProt ID"""
        try:
            url = f"{self.ALPHAFOLD_URL}prediction/{uniprot_id}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"AlphaFold API returned status code: {response.status_code}")
                return {"error": f"Failed to retrieve AlphaFold data: {response.status_code}"}
                
        except Exception as e:
            print(f"Error getting AlphaFold structure: {str(e)}")
            return {"error": str(e)}
    
    def get_pdb_structure_details(self, pdb_id):
        """Get detailed information about a PDB structure"""
        try:
            url = f"{self.PDB_DATA_URL}{pdb_id}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                structure_data = response.json()
                
                # Extract basic information
                method = structure_data.get("exptl", [{}])[0].get("method", "Unknown method")
                resolution = structure_data.get("rcsb_entry_info", {}).get("resolution_combined", "N/A")
                title = structure_data.get("struct", {}).get("title", "")
                
                # Extract assembly information
                assembly_info = structure_data.get("pdbx_struct_assembly", {})
                assembly_details = {
                    "oligomeric_state": assembly_info.get("oligomeric_details", "").strip(),
                    "details": assembly_info.get("details", "").strip(),
                    "method": assembly_info.get("method_details", "").strip()
                }
                
                # Extract symmetry information
                symmetry_info = structure_data.get("rcsb_struct_symmetry", [{}])[0]
                symmetry_details = {
                    "type": symmetry_info.get("type", ""),
                    "symbol": symmetry_info.get("symbol", ""),
                    "oligomeric_state": symmetry_info.get("oligomeric_state", "")
                }
                
                # Extract polymer composition
                polymer_info = structure_data.get("rcsb_assembly_info", {})
                polymer_details = {
                    "composition": polymer_info.get("polymer_composition", ""),
                    "entity_types": polymer_info.get("selected_polymer_entity_types", ""),
                    "atom_count": polymer_info.get("polymer_atom_count", 0),
                    "monomer_count": polymer_info.get("polymer_monomer_count", 0)
                }
                
                # Format resolution if available
                if resolution != "N/A":
                    try:
                        # Handle both string and numeric resolution values
                        if isinstance(resolution, (int, float)):
                            resolution = f"{float(resolution):.1f} Å"
                        else:
                            # Try to convert string to float
                            resolution = f"{float(resolution):.1f} Å"
                    except (ValueError, TypeError):
                        resolution = "N/A"
                
                # Combine all information
                detailed_info = {
                    "basic_info": {
                        "method": method,
                        "resolution": resolution,
                        "title": title
                    },
                    "assembly": assembly_details,
                    "symmetry": symmetry_details,
                    "polymer": polymer_details,
                    "viewer_url": f"https://www.rcsb.org/structure/{pdb_id}"
                }
                
                return detailed_info
            else:
                print(f"PDB API returned status code: {response.status_code}")
                return {"error": f"Failed to retrieve PDB data: {response.status_code}"}
                
        except Exception as e:
            print(f"Error getting PDB structure details: {str(e)}")
            return {"error": str(e)}
    
    def get_structure_summary(self, uniprot_id, gene_symbol=None):
        """Get a summary of available structures for a protein"""
        print(f"Getting structure summary for UniProt ID: {uniprot_id}, Gene Symbol: {gene_symbol}")
        
        structures = []
        errors = []
        
        # Try PDB structures first with UniProt ID
        pdb_results = self.search_pdb(uniprot_id)
        
        if "error" not in pdb_results and "result_set" in pdb_results:
            for result in pdb_results["result_set"]:
                pdb_id = result["identifier"]
                try:
                    structure_data = self.get_pdb_structure_details(pdb_id)
                    
                    if "error" not in structure_data:
                        # Create structure info with enhanced details
                        structure_info = {
                            "id": pdb_id,
                            "source": "pdb",
                            "method": structure_data["basic_info"]["method"],
                            "resolution": structure_data["basic_info"]["resolution"],
                            "title": structure_data["basic_info"]["title"],
                            "assembly": structure_data["assembly"],
                            "symmetry": structure_data["symmetry"],
                            "polymer": structure_data["polymer"],
                            "viewer_url": structure_data["viewer_url"]
                        }
                        
                        # Validate structure info before adding
                        try:
                            structures.append(self.validate_structure_info(structure_info))
                        except ValueError as e:
                            errors.append(f"Invalid structure info for {pdb_id}: {str(e)}")
                            continue
                            
                except Exception as e:
                    errors.append(f"Error getting details for PDB structure {pdb_id}: {str(e)}")
        else:
            if "error" in pdb_results:
                errors.append(f"PDB search error with UniProt ID: {pdb_results['error']}")
            
            # If no results with UniProt ID, try gene symbol
            if gene_symbol and not structures:
                pdb_results = self.search_pdb(gene_symbol)
                if "error" not in pdb_results and "result_set" in pdb_results:
                    for result in pdb_results["result_set"]:
                        pdb_id = result["identifier"]
                        try:
                            structure_data = self.get_pdb_structure_details(pdb_id)
                            
                            if "error" not in structure_data:
                                structure_info = {
                                    "id": pdb_id,
                                    "source": "pdb",
                                    "method": structure_data["basic_info"]["method"],
                                    "resolution": structure_data["basic_info"]["resolution"],
                                    "title": structure_data["basic_info"]["title"],
                                    "assembly": structure_data["assembly"],
                                    "symmetry": structure_data["symmetry"],
                                    "polymer": structure_data["polymer"],
                                    "viewer_url": structure_data["viewer_url"]
                                }
                                
                                try:
                                    structures.append(self.validate_structure_info(structure_info))
                                except ValueError as e:
                                    errors.append(f"Invalid structure info for {pdb_id}: {str(e)}")
                                    continue
                                    
                        except Exception as e:
                            errors.append(f"Error getting details for PDB structure {pdb_id}: {str(e)}")
                else:
                    if "error" in pdb_results:
                        errors.append(f"PDB search error with gene symbol: {pdb_results['error']}")
        
        # Try AlphaFold with UniProt ID
        try:
            alphafold_result = self.get_alphafold_structure(uniprot_id)
            if "error" not in alphafold_result:
                structure_info = {
                    "id": uniprot_id,
                    "source": "alphafold",
                    "method": "AI Prediction",
                    "resolution": "N/A",
                    "title": f"AlphaFold predicted structure for {uniprot_id}",
                    "assembly": {"oligomeric_state": "Predicted monomer"},
                    "symmetry": {"type": "Predicted", "oligomeric_state": "Monomer"},
                    "polymer": {"composition": "Predicted protein"},
                    "viewer_url": f"https://alphafold.ebi.ac.uk/entry/{uniprot_id}"
                }
                
                try:
                    structures.append(self.validate_structure_info(structure_info))
                except ValueError as e:
                    errors.append(f"Invalid AlphaFold structure info: {str(e)}")
            else:
                errors.append(f"AlphaFold API error: {alphafold_result['error']}")
        except Exception as e:
            errors.append(f"AlphaFold service error: {str(e)}")
        
        if not structures:
            error_summary = "\n".join(errors) if errors else "No structures found and no specific errors reported"
            return {
                "error": f"No valid structures found for UniProt ID: {uniprot_id}, Gene Symbol: {gene_symbol}",
                "details": error_summary,
                "structures": []
            }
        
        return {
            "structures": structures,
            "warnings": errors if errors else None
        }
