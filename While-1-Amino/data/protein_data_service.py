from .uniprot_api import UniProtAPI
from .ncbi_api import NCBIProteinAPI
from .structure_api import ProteinStructureAPI
from .interaction_api import ProteinInteractionAPI
from .disease_drug_api import DiseaseDrugAPI
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProteinDataService:
    """Service class that integrates all protein data sources"""
    
    def __init__(self):
        self.uniprot_api = UniProtAPI()
        self.ncbi_api = NCBIProteinAPI()
        self.structure_api = ProteinStructureAPI()
        self.interaction_api = ProteinInteractionAPI()
        self.disease_drug_api = DiseaseDrugAPI()
        self.cache = {}  # Simple in-memory cache
        
        # No longer need to set a primary source - we'll use both
        self.use_combined_data = True
    
    def get_protein_data(self, query):
        """Get comprehensive protein data from all sources"""
        # Create a cache key for this query
        cache_key = f"protein_data_{query}"
        if cache_key in self.cache:
            logger.info(f"Cache hit for {query}")
            return self.cache[cache_key]
        
        try:
            # Get data from both sources
            logger.info(f"Fetching data for: {query} from both UniProt and NCBI")
            
            # Try UniProt first (priority source)
            uniprot_info = self.uniprot_api.get_protein_summary(query)
            
            # Try NCBI as well
            ncbi_info = self.ncbi_api.get_protein_summary(query)
            
            # Determine which source to use as primary data
            if "error" not in uniprot_info:
                # Use UniProt as primary if available
                protein_info = uniprot_info
                protein_info["data_source"] = "UniProt"
                secondary_info = ncbi_info
                logger.info(f"Using UniProt as primary data source for {query}")
            elif "error" not in ncbi_info:
                # Use NCBI if UniProt fails
                protein_info = ncbi_info
                protein_info["data_source"] = "NCBI"
                secondary_info = None
                logger.info(f"Using NCBI as primary data source for {query}")
            else:
                # Both sources failed
                return {
                    "error": f"No protein data found for '{query}' in either UniProt or NCBI databases.",
                    "query": query
                }
            
            # Extract ID and gene symbol for use with other APIs
            uniprot_id = protein_info.get("accession", protein_info.get("uniprot_id", ""))
            gene_symbol = protein_info.get("gene_symbol", query)
            
            # If we got an NCBI gene ID, try to convert it to UniProt ID
            if uniprot_id.startswith("GENE_") and gene_symbol:
                try:
                    # Try to get UniProt ID from NCBI
                    uniprot_mapping = self.ncbi_api.get_uniprot_mapping(gene_symbol)
                    if uniprot_mapping and "uniprot_id" in uniprot_mapping:
                        uniprot_id = uniprot_mapping["uniprot_id"]
                        logger.info(f"Converted NCBI gene ID to UniProt ID: {uniprot_id}")
                        # Update the protein info with the correct UniProt ID
                        protein_info["accession"] = uniprot_id
                        protein_info["uniprot_id"] = uniprot_id
                    else:
                        logger.warning(f"Failed to convert NCBI gene ID to UniProt ID: {uniprot_mapping.get('error', 'Unknown error')}")
                except Exception as e:
                    logger.warning(f"Failed to convert NCBI gene ID to UniProt ID: {str(e)}")
            
            logger.info(f"Using ID: {uniprot_id}, Gene Symbol: {gene_symbol}")
            
            # Enhance data with secondary source if available
            if secondary_info and "error" not in secondary_info:
                # Merge in any missing data from secondary source
                for key, value in secondary_info.items():
                    if key not in protein_info or not protein_info[key]:
                        protein_info[key] = value
                        logger.info(f"Enhanced {key} with data from secondary source")
                
                # Special handling for function and summary
                if not protein_info.get("function") and secondary_info.get("function"):
                    protein_info["function"] = secondary_info["function"]
                
                if not protein_info.get("summary") and secondary_info.get("summary"):
                    protein_info["summary"] = secondary_info["summary"]
                
                # If we have summary but no function, use summary as function
                if protein_info.get("summary") and not protein_info.get("function"):
                    protein_info["function"] = protein_info["summary"]
                
                # If we have function but no summary, use function as summary
                if protein_info.get("function") and not protein_info.get("summary"):
                    protein_info["summary"] = protein_info["function"]
            
            # Get structure information if we have a valid UniProt ID
            structure_info = {"structures": []}
            if uniprot_id and not uniprot_id.startswith("GENE_"):
                try:
                    structure_info = self.structure_api.get_structure_summary(uniprot_id, gene_symbol)
                    if isinstance(structure_info, dict) and "error" in structure_info:
                        logger.warning(f"Error getting structure info: {structure_info['error']}")
                        structure_info = {"structures": []}
                except Exception as e:
                    logger.error(f"Exception getting structure info: {str(e)}")
            
            # Get interaction information if we have a gene symbol
            interaction_info = {"interactions": []}
            try:
                interaction_info = self.interaction_api.get_interactions(gene_symbol, uniprot_id)
                if isinstance(interaction_info, dict) and "error" in interaction_info:
                    logger.warning(f"Error getting interaction info: {interaction_info['error']}")
                    interaction_info = {"interactions": []}
            except Exception as e:
                logger.error(f"Exception getting interaction info: {str(e)}")
            
            # Get disease and drug information
            disease_drug_info = {"diseases": [], "drugs": []}
            try:
                disease_drug_info = self.disease_drug_api.get_disease_drug_summary(gene_symbol, uniprot_id)
                if isinstance(disease_drug_info, dict) and "error" in disease_drug_info:
                    logger.warning(f"Error getting disease/drug info: {disease_drug_info['error']}")
                    disease_drug_info = {"diseases": [], "drugs": []}
            except Exception as e:
                logger.error(f"Exception getting disease/drug info: {str(e)}")
            
            # Combine all data
            combined_data = {
                "query": query,
                "basic_info": protein_info,
                "structure": structure_info,
                "interactions": interaction_info,
                "disease_drug": disease_drug_info,
                "data_source": protein_info.get("data_source", "Combined"),
                "ai_generated": False
            }
            
            # Cache the result
            self.cache[cache_key] = combined_data
            return combined_data
            
        except Exception as e:
            logger.error(f"Error in get_protein_data: {str(e)}")
            return {
                "error": f"Failed to retrieve protein data for '{query}': {str(e)}",
                "query": query
            }
    
    def set_primary_data_source(self, source):
        """This method is kept for backward compatibility but no longer used"""
        logger.info(f"Note: The application now automatically uses data from both UniProt and NCBI")
        return True
    
    def get_protein_chat_response(self, query, chat_history, user_query):
        """Get a chat response based on protein data and user query"""
        try:
            # First, get the protein data
            protein_data = self.get_protein_data(query)
            
            # Check if we have an error
            if "error" in protein_data:
                return {
                    "response": f"I couldn't find information about '{query}'. {protein_data['error']}",
                    "error": protein_data["error"]
                }
            
            # Extract relevant information from protein_data
            protein_info = protein_data["basic_info"]
            protein_name = protein_info.get("protein_name", "")
            gene_symbol = protein_info.get("gene_symbol", "")
            function = protein_info.get("function", "")
            summary = protein_info.get("summary", "")
            
            # Get structure information
            structures = protein_data["structure"].get("structures", [])
            structure_text = ""
            if structures:
                structure_text = f"This protein has {len(structures)} known structures from {', '.join(set([s['source'] for s in structures]))}."
            
            # Get disease information
            diseases = protein_data["disease_drug"].get("diseases", [])
            disease_text = ""
            if diseases:
                disease_names = [d["disease_name"] for d in diseases[:3]]
                disease_text = f"This protein is associated with diseases such as {', '.join(disease_names)}."
            
            # Get drug information
            drugs = protein_data["disease_drug"].get("drugs", [])
            drug_text = ""
            if drugs:
                drug_names = [d["name"] for d in drugs[:3]]
                drug_text = f"Drugs that target this protein include {', '.join(drug_names)}."
            
            # Generate a simple response based on the user's query
            response_text = ""
            
            # Check what the user is asking about
            user_query_lower = user_query.lower()
            
            if "function" in user_query_lower or "do" in user_query_lower or "role" in user_query_lower:
                response_text = f"The function of {protein_name} ({gene_symbol}) is: {function}"
            
            elif "disease" in user_query_lower or "condition" in user_query_lower or "disorder" in user_query_lower:
                if diseases:
                    response_text = f"{protein_name} ({gene_symbol}) is associated with several diseases, including: "
                    for disease in diseases[:3]:
                        response_text += f"\n- {disease['disease_name']}: {disease.get('description', 'No description available')}"
                else:
                    response_text = f"I don't have information about diseases associated with {protein_name} ({gene_symbol})."
            
            elif "drug" in user_query_lower or "medication" in user_query_lower or "treatment" in user_query_lower:
                if drugs:
                    response_text = f"There are several drugs that target {protein_name} ({gene_symbol}), including: "
                    for drug in drugs[:3]:
                        response_text += f"\n- {drug['name']}: {drug.get('mechanism', 'Mechanism unknown')}"
                else:
                    response_text = f"I don't have information about drugs that target {protein_name} ({gene_symbol})."
            
            elif "structure" in user_query_lower or "3d" in user_query_lower:
                if structures:
                    response_text = f"{protein_name} ({gene_symbol}) has {len(structures)} known structures: "
                    for structure in structures[:3]:
                        response_text += f"\n- {structure['id']} from {structure['source']} ({structure.get('method', 'Method unknown')})"
                else:
                    response_text = f"I don't have information about the 3D structure of {protein_name} ({gene_symbol})."
            
            elif "interaction" in user_query_lower or "partner" in user_query_lower or "bind" in user_query_lower:
                interactions = protein_data["interactions"].get("interactions", [])
                if interactions:
                    response_text = f"{protein_name} ({gene_symbol}) interacts with several proteins, including: "
                    for interaction in interactions[:3]:
                        response_text += f"\n- {interaction.get('interactor_name', 'Unknown protein')}"
                else:
                    response_text = f"I don't have information about proteins that interact with {protein_name} ({gene_symbol})."
            
            else:
                # General summary for other questions
                response_text = f"About {protein_name} ({gene_symbol}): {summary}\n\n"
                
                if function:
                    response_text += f"Function: {function}\n\n"
                
                if structure_text:
                    response_text += f"{structure_text}\n\n"
                
                if disease_text:
                    response_text += f"{disease_text}\n\n"
                
                if drug_text:
                    response_text += f"{drug_text}"
            
            # Add data source information
            data_source = protein_data.get("data_source", "Unknown")
            response_text += f"\n\nThis information was retrieved from {data_source}."
            
            return {
                "response": response_text
            }
            
        except Exception as e:
            logger.error(f"Error in get_protein_chat_response: {str(e)}")
            return {
                "response": f"I encountered an error while trying to answer your question about {query}. Please try again or ask about a different protein.",
                "error": str(e)
            }
