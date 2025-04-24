import requests
import json
import re
import time
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class NCBIProteinAPI:
    """Class to interact with the NCBI Protein and Gene databases for protein information"""
    
    NCBI_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    NCBI_EFETCH_URL = f"{NCBI_EUTILS_BASE}efetch.fcgi"
    NCBI_ESEARCH_URL = f"{NCBI_EUTILS_BASE}esearch.fcgi"
    NCBI_ESUMMARY_URL = f"{NCBI_EUTILS_BASE}esummary.fcgi"
    
    # Well-known protein mappings for common proteins (NCBI Protein IDs)
    COMMON_PROTEINS = {
        "TP53": "P04637",  # UniProt ID for compatibility
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
    
    # NCBI Gene IDs for common proteins
    COMMON_GENE_IDS = {
        "TP53": "7157",
        "BRCA1": "672",
        "BRCA2": "675",
        "EGFR": "1956",
        "INS": "3630",
        "APP": "351",
        "APOE": "348",
        "TNF": "7124",
        "IL6": "3569",
        "ALB": "213",
        "KRAS": "3845",
        "PTEN": "5728",
        "VEGFA": "7422",
        "SOD1": "6647",
        "CFTR": "1080"
    }
    
    # Common protein descriptions
    COMMON_DESCRIPTIONS = {
        "TP53": "Tumor protein p53 is a tumor suppressor protein that regulates cell cycle and functions as a tumor suppressor. It plays a crucial role in preventing cancer formation.",
        "BRCA1": "Breast cancer type 1 susceptibility protein is involved in DNA repair, cell cycle checkpoint control, and maintenance of genomic stability.",
        "BRCA2": "Breast cancer type 2 susceptibility protein is involved in the repair of chromosomal damage with an important role in the error-free repair of DNA double strand breaks.",
        "EGFR": "Epidermal growth factor receptor is a transmembrane protein that is activated by binding of its specific ligands. It plays a crucial role in cell signaling pathways.",
        "INS": "Insulin is a peptide hormone produced by beta cells of the pancreatic islets. It regulates the metabolism of carbohydrates, fats and protein.",
        "APP": "Amyloid precursor protein is an integral membrane protein expressed in many tissues and concentrated in the synapses of neurons. It is cleaved by secretases to form a number of peptides.",
        "APOE": "Apolipoprotein E is a class of apolipoprotein found in the chylomicron and Intermediate-density lipoprotein that is essential for the normal catabolism of triglyceride-rich lipoprotein constituents.",
        "TNF": "Tumor necrosis factor is a cytokine that is involved in systemic inflammation and is one of the cytokines that regulate the acute phase reaction.",
        "IL6": "Interleukin 6 is an interleukin that acts as both a pro-inflammatory cytokine and an anti-inflammatory myokine.",
        "ALB": "Albumin is a family of globular proteins, the most common of which are the serum albumins. They are commonly found in blood plasma.",
        "KRAS": "KRAS is a protein that in humans is encoded by the KRAS gene. It is involved in regulating cell division as part of the RAS/MAPK pathway.",
        "PTEN": "Phosphatase and tensin homolog is a protein that, in humans, is encoded by the PTEN gene. It acts as a tumor suppressor gene.",
        "VEGFA": "Vascular endothelial growth factor A is a protein that in humans is encoded by the VEGFA gene. It stimulates angiogenesis, vasculogenesis and endothelial cell growth.",
        "SOD1": "Superoxide dismutase 1 is an enzyme that in humans is encoded by the SOD1 gene. It converts harmful superoxide radicals to hydrogen peroxide and oxygen.",
        "CFTR": "Cystic fibrosis transmembrane conductance regulator is a membrane protein and chloride channel in vertebrates that is encoded by the CFTR gene."
    }
    
    def __init__(self):
        self.session = requests.Session()
        # Add headers to mimic a browser request
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Accept': 'application/json'
        })
    
    def search_protein(self, query, organism="Human", limit=5):
        """Search for a protein by name or gene symbol using NCBI databases"""
        try:
            # Clean the query
            cleaned_query = query.strip().upper()
            
            # Check if this is a well-known protein first
            if cleaned_query in self.COMMON_PROTEINS:
                logger.info(f"Found well-known protein: {cleaned_query}")
                
                # For compatibility with the rest of the system, return in UniProt format
                protein_data = self.get_protein_by_gene_id(self.COMMON_GENE_IDS[cleaned_query])
                
                if "error" not in protein_data:
                    # Format as search results for compatibility
                    return {
                        "results": [protein_data]
                    }
            
            # Search NCBI Gene database first to get gene ID
            search_params = {
                "db": "gene",
                "term": f"{cleaned_query}[Gene Name] AND {organism}[Organism]",
                "retmode": "json",
                "retmax": limit
            }
            
            response = self.session.get(self.NCBI_ESEARCH_URL, params=search_params)
            
            if response.status_code != 200:
                logger.warning(f"NCBI Gene search failed with status code: {response.status_code}")
                return {"error": f"NCBI Gene search failed with status code: {response.status_code}"}
            
            search_data = response.json()
            
            # Check if we found any genes
            if "esearchresult" in search_data and int(search_data["esearchresult"]["count"]) > 0:
                gene_ids = search_data["esearchresult"]["idlist"]
                
                # Get details for each gene
                results = []
                for gene_id in gene_ids[:limit]:
                    protein_data = self.get_protein_by_gene_id(gene_id)
                    if "error" not in protein_data:
                        results.append(protein_data)
                
                if results:
                    return {"results": results}
            
            # If gene search failed, try direct protein search
            search_params = {
                "db": "protein",
                "term": f"{cleaned_query} AND {organism}[Organism]",
                "retmode": "json",
                "retmax": limit
            }
            
            response = self.session.get(self.NCBI_ESEARCH_URL, params=search_params)
            
            if response.status_code != 200:
                logger.warning(f"NCBI Protein search failed with status code: {response.status_code}")
                return {"error": f"NCBI Protein search failed with status code: {response.status_code}"}
            
            search_data = response.json()
            
            # Check if we found any proteins
            if "esearchresult" in search_data and int(search_data["esearchresult"]["count"]) > 0:
                protein_ids = search_data["esearchresult"]["idlist"]
                
                # Get details for each protein
                results = []
                for protein_id in protein_ids[:limit]:
                    protein_data = self.get_protein_by_id(protein_id)
                    if "error" not in protein_data:
                        results.append(protein_data)
                
                if results:
                    return {"results": results}
            
            # No results found
            logger.warning(f"No results found for query: {query}")
            return {"error": f"No protein found for '{query}' in NCBI databases"}
            
        except Exception as e:
            logger.error(f"Error searching NCBI for protein: {str(e)}")
            return {"error": f"Error searching NCBI: {str(e)}"}
    
    def get_protein_by_gene_id(self, gene_id):
        """Get protein information from a gene ID"""
        try:
            # First get gene summary
            summary_params = {
                "db": "gene",
                "id": gene_id,
                "retmode": "json"
            }
            
            response = self.session.get(self.NCBI_ESUMMARY_URL, params=summary_params)
            
            if response.status_code != 200:
                logger.warning(f"NCBI Gene summary failed with status code: {response.status_code}")
                return {"error": f"NCBI Gene summary failed with status code: {response.status_code}"}
            
            gene_data = response.json()
            
            if "result" not in gene_data or gene_id not in gene_data["result"]:
                logger.warning(f"No gene data found for ID: {gene_id}")
                return {"error": f"No gene data found for ID: {gene_id}"}
            
            gene_info = gene_data["result"][gene_id]
            
            # Now search for the protein associated with this gene
            search_params = {
                "db": "protein",
                "term": f"{gene_info['name']}[Gene Name] AND refseq[Filter]",
                "retmode": "json",
                "retmax": 1
            }
            
            response = self.session.get(self.NCBI_ESEARCH_URL, params=search_params)
            
            protein_id = None
            sequence = ""
            protein_name = gene_info.get("description", "").split("[")[0].strip()
            
            if response.status_code == 200:
                search_data = response.json()
                
                if "esearchresult" in search_data and int(search_data["esearchresult"]["count"]) > 0:
                    protein_ids = search_data["esearchresult"]["idlist"]
                    if protein_ids:
                        protein_id = protein_ids[0]
                        
                        # Get protein sequence
                        fetch_params = {
                            "db": "protein",
                            "id": protein_id,
                            "rettype": "fasta",
                            "retmode": "text"
                        }
                        
                        seq_response = self.session.get(self.NCBI_EFETCH_URL, params=fetch_params)
                        
                        if seq_response.status_code == 200:
                            fasta_data = seq_response.text
                            
                            # Parse FASTA format
                            lines = fasta_data.strip().split('\n')
                            if len(lines) > 1:
                                protein_name = lines[0][1:].split("[")[0].strip()  # Remove '>' character and extract name
                                sequence = ''.join(lines[1:])
            
            # Create a description of the gene function
            function_description = gene_info.get("summary", "")
            if not function_description:
                function_description = f"{gene_info.get('description', '')} is a protein-coding gene."
            
            # Format data in a way that's compatible with the rest of the system
            return {
                "protein_id": protein_id if protein_id else f"GENE_{gene_id}",
                "protein_name": protein_name,
                "gene_symbol": gene_info.get("name", ""),
                "gene_names": [gene_info.get("name", "")],
                "organism": gene_info.get("organism", {}).get("scientificname", ""),
                "accession": f"GENE_{gene_id}",  # Placeholder for compatibility
                "uniprot_id": f"GENE_{gene_id}",  # Placeholder for compatibility
                "length": len(sequence),
                "sequence": sequence,
                "function": function_description,
                "summary": gene_info.get("description", ""),
                "subcellular_location": [],
                "data_source": "NCBI"
            }
            
        except Exception as e:
            logger.error(f"Error getting protein by gene ID: {str(e)}")
            return {"error": f"Error getting protein by gene ID: {str(e)}"}
    
    def get_protein_by_id(self, protein_id):
        """Get detailed protein information by NCBI Protein ID"""
        try:
            # Get protein summary
            summary_params = {
                "db": "protein",
                "id": protein_id,
                "retmode": "json"
            }
            
            response = self.session.get(self.NCBI_ESUMMARY_URL, params=summary_params)
            
            if response.status_code != 200:
                logger.warning(f"NCBI Protein summary failed with status code: {response.status_code}")
                return {"error": f"NCBI Protein summary failed with status code: {response.status_code}"}
            
            summary_data = response.json()
            
            if "result" not in summary_data or protein_id not in summary_data["result"]:
                logger.warning(f"No protein data found for ID: {protein_id}")
                return {"error": f"No protein data found for ID: {protein_id}"}
            
            protein_summary = summary_data["result"][protein_id]
            
            # Get protein sequence and full data
            fetch_params = {
                "db": "protein",
                "id": protein_id,
                "rettype": "fasta",
                "retmode": "text"
            }
            
            response = self.session.get(self.NCBI_EFETCH_URL, params=fetch_params)
            
            if response.status_code != 200:
                logger.warning(f"NCBI Protein fetch failed with status code: {response.status_code}")
                return {"error": f"NCBI Protein fetch failed with status code: {response.status_code}"}
            
            fasta_data = response.text
            
            # Parse FASTA format
            lines = fasta_data.strip().split('\n')
            header = lines[0][1:]  # Remove '>' character
            sequence = ''.join(lines[1:])
            
            # Extract gene name from header if possible
            gene_match = re.search(r'\[gene=(\w+)\]', header)
            gene_symbol = gene_match.group(1) if gene_match else ""
            
            # Extract organism from header if possible
            organism_match = re.search(r'\[(.*?)\]', header)
            organism = organism_match.group(1) if organism_match else ""
            
            # Extract protein name from title
            protein_name = protein_summary.get("title", "")
            
            # Clean up protein name
            if "[" in protein_name:
                protein_name = protein_name.split("[")[0].strip()
            
            # Format data in a way that's compatible with the rest of the system
            protein_data = {
                "protein_id": protein_id,
                "accession": protein_summary.get("accessionversion", protein_id),
                "uniprot_id": protein_summary.get("accessionversion", protein_id),
                "protein_name": protein_name,
                "gene_symbol": gene_symbol,
                "gene_names": [gene_symbol] if gene_symbol else [],
                "organism": organism,
                "length": len(sequence),
                "sequence": sequence,
                "function": protein_summary.get("comment", ""),
                "summary": protein_name,
                "subcellular_location": [],  # Not easily available from NCBI
                "ec_number": "",  # Not easily available from NCBI
                "data_source": "NCBI"
            }
            
            return protein_data
            
        except Exception as e:
            logger.error(f"Error getting protein by ID: {str(e)}")
            return {"error": f"Error getting protein by ID: {str(e)}"}
    
    def get_protein_by_accession(self, accession):
        """Get protein by accession number (for compatibility with UniProt API)"""
        try:
            # For well-known proteins, use gene ID mapping
            for gene, acc in self.COMMON_PROTEINS.items():
                if acc == accession and gene in self.COMMON_GENE_IDS:
                    return self.get_protein_by_gene_id(self.COMMON_GENE_IDS[gene])
            
            # Search for the accession in NCBI
            search_params = {
                "db": "protein",
                "term": f"{accession}[Accession]",
                "retmode": "json",
                "retmax": 1
            }
            
            response = self.session.get(self.NCBI_ESEARCH_URL, params=search_params)
            
            if response.status_code != 200:
                logger.warning(f"NCBI Protein search failed with status code: {response.status_code}")
                return {"error": f"NCBI Protein search failed with status code: {response.status_code}"}
            
            search_data = response.json()
            
            # Check if we found any proteins
            if "esearchresult" in search_data and int(search_data["esearchresult"]["count"]) > 0:
                protein_id = search_data["esearchresult"]["idlist"][0]
                return self.get_protein_by_id(protein_id)
            
            logger.warning(f"No protein found for accession: {accession}")
            return {"error": f"No protein found for accession: {accession}"}
            
        except Exception as e:
            logger.error(f"Error getting protein by accession: {str(e)}")
            return {"error": f"Error getting protein by accession: {str(e)}"}
    
    def get_protein_summary(self, query):
        """Get a summary of protein information by name or accession"""
        try:
            # Check if the query looks like an accession number
            if re.match(r'^[A-Z][0-9][A-Z0-9]{3}[0-9]$', query) or re.match(r'^[A-Z]{2}_\d+\.\d+$', query) or re.match(r'^[A-Z]{3}_\d+\.\d+$', query):
                protein_data = self.get_protein_by_accession(query)
                if "error" not in protein_data:
                    return self.format_protein_data(protein_data)
            
            # Check if this is a well-known protein
            if query.upper() in self.COMMON_GENE_IDS:
                gene_id = self.COMMON_GENE_IDS[query.upper()]
                protein_data = self.get_protein_by_gene_id(gene_id)
                if "error" not in protein_data:
                    return self.format_protein_data(protein_data)
            
            # Otherwise search for the protein
            search_results = self.search_protein(query)
            
            if "error" in search_results:
                logger.warning(f"Error searching for protein: {search_results['error']}")
                return {"error": search_results["error"]}
            
            if "results" in search_results and search_results["results"]:
                # Return the first result
                return self.format_protein_data(search_results["results"][0])
            
            logger.warning(f"No protein found for query: {query}")
            return {"error": f"No protein found for '{query}'"}
            
        except Exception as e:
            logger.error(f"Error getting protein summary: {str(e)}")
            return {"error": f"Error getting protein summary: {str(e)}"}
    
    def format_protein_data(self, protein_data):
        """Format protein data in a consistent way"""
        # For compatibility with the rest of the system
        formatted_data = {
            "uniprot_id": protein_data.get("accession", ""),
            "protein_name": protein_data.get("protein_name", ""),
            "gene_symbol": protein_data.get("gene_symbol", ""),
            "gene_names": protein_data.get("gene_names", []),
            "organism": protein_data.get("organism", ""),
            "function": protein_data.get("function", ""),
            "summary": protein_data.get("summary", ""),
            "sequence": protein_data.get("sequence", ""),
            "length": protein_data.get("length", 0),
            "subcellular_location": protein_data.get("subcellular_location", []),
            "ec_number": protein_data.get("ec_number", ""),
            "data_source": "NCBI"
        }
        
        # Generate a summary if not present
        if not formatted_data["summary"] or formatted_data["summary"] == formatted_data["protein_name"]:
            gene_info = formatted_data["gene_symbol"]
            protein_info = formatted_data["protein_name"]
            organism = formatted_data["organism"]
            
            summary = f"{protein_info}"
            if gene_info:
                summary += f" ({gene_info})"
            
            if organism:
                summary += f" is a protein found in {organism}."
            else:
                summary += " is a protein."
                
            if formatted_data["function"]:
                summary += f" {formatted_data['function']}"
                
            formatted_data["summary"] = summary.strip()
        
        # Generate a function description if not present
        if not formatted_data["function"]:
            if formatted_data["gene_symbol"]:
                for gene, desc in self.COMMON_DESCRIPTIONS.items():
                    if gene.lower() == formatted_data["gene_symbol"].lower():
                        formatted_data["function"] = desc
                        break
        
        return formatted_data
    
    def get_uniprot_mapping(self, gene_symbol):
        """Get UniProt ID mapping for a gene symbol from NCBI"""
        try:
            # First check if this is a well-known protein
            if gene_symbol in self.COMMON_PROTEINS:
                return {"uniprot_id": self.COMMON_PROTEINS[gene_symbol]}
            
            # Use NCBI's eutils to get gene info
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            params = {
                "db": "gene",
                "term": f"{gene_symbol}[Gene Name] AND Homo sapiens[Organism]",
                "retmode": "json"
            }
            
            response = self.session.get(url, params=params)
            if response.status_code != 200:
                return {"error": f"Failed to get gene info: {response.status_code}"}
            
            gene_data = response.json()
            if not gene_data.get("esearchresult", {}).get("idlist"):
                return {"error": f"No gene found for {gene_symbol}"}
            
            gene_id = gene_data["esearchresult"]["idlist"][0]
            
            # Get gene details including UniProt ID
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            params = {
                "db": "gene",
                "id": gene_id,
                "retmode": "xml"
            }
            
            response = self.session.get(url, params=params)
            if response.status_code != 200:
                return {"error": f"Failed to get gene details: {response.status_code}"}
            
            # Parse XML response to find UniProt ID
            root = ET.fromstring(response.text)
            
            # Look for UniProt ID in the Gene-ref section
            for gene_ref in root.findall(".//Gene-ref"):
                for dbtag in gene_ref.findall(".//Dbtag"):
                    if dbtag.find("DB") is not None and dbtag.find("DB").text == "UniProt":
                        if dbtag.find("Object-id") is not None and dbtag.find("Object-id").find("Str") is not None:
                            return {"uniprot_id": dbtag.find("Object-id").find("Str").text}
            
            return {"error": f"No UniProt ID found for {gene_symbol}"}
            
        except Exception as e:
            return {"error": str(e)}
