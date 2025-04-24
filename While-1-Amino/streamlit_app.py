import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
import os
import sys
import json
import plotly.express as px
import plotly.graph_objects as go
import time
import logging
import base64
from utils.supabase_client import SupabaseManager

# Add these functions for consistent styling with other pages
def get_base64_of_bin_file(bin_file):
    """Convert a binary file to a base64 string."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_video_background(video_path):
    """Set a video as the background for the Streamlit app."""
    video_html = f"""
    <style>
    .stApp {{
        background: transparent; 
    }}
    
    .video-container {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        overflow: hidden;
    }}
    
    video {{
        position: absolute;
        min-width: 100%; 
        min-height: 100%;
        width: auto;
        height: auto;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        object-fit: cover;
        opacity: 0.5;  /* Set opacity to 50% */
    }}
    
    /* Overlay CSS */
    .overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.8); /* Light overlay for better text visibility */
        z-index: -1;
    }}
    </style>
    
    <div class="video-container">
        <video autoplay loop muted playsinline>
            <source src="data:video/mp4;base64,{get_base64_of_bin_file(video_path)}" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    </div>
    <div class="overlay"></div>
    """
    st.markdown(video_html, unsafe_allow_html=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path for direct imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data.protein_data_service import ProteinDataService
from utils.visualization import create_interaction_network, create_disease_chart, display_protein_structure, create_drug_chart
from utils.report_generator import create_medical_report

# Page configuration
st.set_page_config(
    page_title="While(1)Amino - Protein Insights",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set video background
video_background_path = "../seamless-looping-animation-of-rotating-dna-strands-SBV-305438837-preview.mp4"
set_video_background(video_background_path)

# Custom CSS
st.markdown("""
<style>
/* Make header transparent */
header[data-testid="stHeader"] {
    background: transparent !important;
    color: #000000;
}

/* Fix sidebar styling */
[data-testid="stSidebar"] {
    background-color: rgba(255, 255, 255, 0.5) !important;
}

[data-testid="stSidebar"] > div:first-child {
    background-color: transparent !important;
}

[data-testid="stSidebarNav"] {
    background-color: transparent !important;
}

[data-testid="stSidebarNavItems"] {
    background-color: transparent !important;
}

.main-header {
    font-size: 2.5rem;
    color: #000000;
    text-align: center;
    margin-bottom: 1rem;
}
.sub-header {
    font-size: 1.5rem;
    color: #000000;
    margin-bottom: 1rem;
}
.protein-card {
    background-color: rgba(255, 255, 255, 0.9);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.chat-user {
    background-color: rgba(255, 255, 255, 0.9);
    padding: 12px;
    margin-bottom: 8px;
    border-radius: 8px;
}
.chat-assistant {
    background-color: rgba(255, 255, 255, 0.9);
    padding: 12px;
    margin-bottom: 16px;
    border-left: 2px solid #f0f0f0;
    border-radius: 8px;
}
.structure-viewer {
    height: 500px;
    width: 100%;
}
.stApp {
    background-color: transparent;
}
.sidebar .sidebar-content {
    background-color: rgba(255, 255, 255, 0.8);
    padding: 16px;
}
.search-container {
    background-color: rgba(255, 255, 255, 0.9);
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.stPlotlyChart {
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    padding: 10px;
    margin-bottom: 20px;
    background-color: rgba(255, 255, 255, 0.9);
}
</style>
""", unsafe_allow_html=True)

# Initialize Supabase manager
supabase_manager = SupabaseManager()

# Initialize session state variables
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_protein' not in st.session_state:
    st.session_state.current_protein = ""
if 'protein_data' not in st.session_state:
    st.session_state.protein_data = None
if 'question_asked' not in st.session_state:
    st.session_state.question_asked = False
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# Initialize the protein data service
protein_service = ProteinDataService()

# Sidebar
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #000000;'>🧬 While(1)Amino</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #000000;'>Protein Insights Platform</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Search History Section
    st.markdown("<h3 style='color: #000000;'>Search History</h3>", unsafe_allow_html=True)
    
    # Get search history from Supabase
    search_history = supabase_manager.get_search_history()
    
    if search_history:
        for search in search_history:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(
                    f"🔍 {search['protein_name'] or search['protein_id']}",
                    key=f"history_{search['id']}",
                    help=f"Gene Names: {', '.join(search['gene_names']) if search['gene_names'] else 'N/A'}\nOrganism: {search['organism']}\n\n{search['summary']}"
                ):
                    # Load protein data from history
                    protein_data = supabase_manager.get_protein_data(search['id'])
                    if protein_data:
                        st.session_state.current_protein = search['protein_id']
                        st.session_state.protein_data = protein_data
                        st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"delete_{search['id']}", help="Delete from history"):
                    supabase_manager.delete_search(search['id'])
                    st.rerun()
    else:
        st.info("No search history yet")
    
    st.markdown("---")
    
    # About section
    st.markdown("<h3 style='color: #000000;'>About</h3>", unsafe_allow_html=True)
    st.markdown("""
    While(1)Amino provides insights about proteins by querying biological databases 
    including UniProt, NCBI, PDB, AlphaFold, STRING, and more.
    
    Enter a protein name or gene symbol in the search box to explore:
    - Basic protein information
    - Protein structure
    - Protein-protein interactions
    - Disease and drug associations
    - Protein sequence
    """)
    
    st.markdown("---")
    
    # Data Sources section
    st.markdown("<h3 style='color: #000000;'>Data Sources</h3>", unsafe_allow_html=True)
    st.markdown("""
    - **UniProt**: Universal Protein Resource (primary)
    - **NCBI**: National Center for Biotechnology Information
    - **PDB**: Protein Data Bank
    - **AlphaFold**: AI-predicted protein structures
    - **STRING**: Protein-Protein Interactions
    - **DisGeNET**: Disease-Gene Associations
    - **DrugBank**: Drug Information
    """)
    
    st.markdown("---")
    
    # Help section
    st.markdown("<h3 style='color: #000000;'>Help</h3>", unsafe_allow_html=True)
    with st.expander("Search Tips"):
        st.markdown("""
        - Search by gene symbol (e.g., TP53, BRCA1)
        - Search by protein name (e.g., Insulin, Albumin)
        - For best results, use official gene symbols
        - You can ask follow-up questions in the chat
        """)

# Function to get protein data
def get_protein_data(query):
    """Get protein data using the ProteinDataService"""
    if not query or query.strip() == "":
        st.error("Please enter a protein or gene name")
        return {"error": "Empty query"}
        
    try:
        # Get protein data from both sources
        with st.spinner(f"Retrieving protein data for '{query}' from biological databases..."):
            protein_data = protein_service.get_protein_data(query)
            
        # Check for errors
        if "error" in protein_data:
            st.error(protein_data["error"])
            return protein_data
            
        # Store the current protein and data
        st.session_state.current_protein = query
        st.session_state.protein_data = protein_data
        
        # Store search in Supabase
        supabase_manager.store_search(protein_data)
        
        # Display data source info
        data_source = protein_data.get("data_source", "Combined")
        st.success(f"Data retrieved from {data_source}")
        
        return protein_data
        
    except Exception as e:
        logger.error(f"Error getting protein data: {str(e)}")
        st.error(f"Error retrieving protein data: {str(e)}")
        return {"error": str(e)}

# Function to handle chat interactions
def handle_chat_interaction(query, user_question):
    """Handle a chat interaction with the protein data service"""
    try:
        # Get chat history from session state
        chat_history = []
        for message in st.session_state.messages:
            chat_history.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        # Get response from service
        logger.info(f"Getting chat response for protein {query}, question: {user_question}")
        response = protein_service.get_protein_chat_response(query, chat_history, user_question)
        
        if "error" in response:
            logger.warning(f"Error in chat response: {response['error']}")
            return f"I'm sorry, I couldn't answer that question: {response['error']}"
        
        return response["response"]
    except Exception as e:
        logger.error(f"Error in chat interaction: {str(e)}")
        return f"I encountered an error while processing your question: {str(e)}"

# Function to display protein information
def display_protein_info(protein_data):
    """Display protein information in a structured format"""
    # Basic information
    basic_info = protein_data.get("basic_info", {})
    
    if basic_info:
        st.markdown("<div class='protein-card'>", unsafe_allow_html=True)
        st.subheader("Basic Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Protein Name:** {basic_info.get('protein_name', 'Unknown')}")
            
            # Display gene names properly
            gene_names = basic_info.get('gene_names', [])
            if isinstance(gene_names, list) and gene_names:
                st.markdown(f"**Gene Names:** {', '.join(gene_names)}")
            elif basic_info.get('gene_symbol'):
                st.markdown(f"**Gene Symbol:** {basic_info.get('gene_symbol', 'Unknown')}")
            else:
                st.markdown("**Gene Names:** Unknown")
            
            st.markdown(f"**UniProt ID:** {basic_info.get('uniprot_id', 'Unknown')}")
            st.markdown(f"**Organism:** {basic_info.get('organism', 'Unknown')}")
        
        with col2:
            st.markdown(f"**Length:** {basic_info.get('length', 'Unknown')} amino acids")
            
            # Display subcellular location properly
            locations = basic_info.get('subcellular_location', [])
            if isinstance(locations, list) and locations:
                st.markdown(f"**Subcellular Location:** {', '.join(locations)}")
            else:
                st.markdown("**Subcellular Location:** Unknown")
            
            # Add UniProt link if available
            if basic_info.get('uniprot_id') and basic_info.get('data_source') == "UniProt":
                uniprot_id = basic_info.get('uniprot_id')
                st.markdown(f"[View in UniProt](https://www.uniprot.org/uniprotkb/{uniprot_id})")
            elif basic_info.get('uniprot_id') and basic_info.get('data_source') == "NCBI":
                ncbi_id = basic_info.get('uniprot_id')
                st.markdown(f"[View in NCBI](https://www.ncbi.nlm.nih.gov/protein/{ncbi_id})")
        
        # Display summary if available
        summary = basic_info.get('summary', '')
        function = basic_info.get('function', '')
        
        # If summary is empty but function exists, use function as summary
        if not summary and function:
            summary = function
        
        # If both are empty, show a more helpful message
        if summary:
            st.markdown("<h4>Summary</h4>", unsafe_allow_html=True)
            st.markdown(summary)
        else:
            st.markdown("<h4>Summary</h4>", unsafe_allow_html=True)
            st.info("Summary information not available from current data sources")
        
        # Display function if available (only if different from summary)
        if function and function != summary:
            st.markdown("<h4>Function</h4>", unsafe_allow_html=True)
            st.markdown(function)
        elif not function:
            st.markdown("<h4>Function</h4>", unsafe_allow_html=True)
            st.info("Function information not available from current data sources")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Structure section - always shown
    st.markdown("<div class='protein-card'>", unsafe_allow_html=True)
    st.subheader("Protein Structure Viewer")
    
    # Get structure info from protein data
    structure_info = protein_data.get("structure", {})
    
    # Show exact match if available
    if structure_info:
        st.markdown(f"<p>Showing structure for: <strong>{protein_data['basic_info'].get('name', '')}</strong></p>", 
                   unsafe_allow_html=True)
        
        # Display structure with metadata
        from utils.visualization import display_protein_structure
        display_protein_structure(structure_info)
    else:
        st.info("No exact structure found for this protein")
        
        # Try to show similar structures if available
        if protein_data['basic_info'].get('uniprot_id'):
            st.markdown("<p>Searching for similar structures...</p>", 
                       unsafe_allow_html=True)
            
            # Create a temporary structure info with just the UniProt ID
            temp_info = {
                'uniprot_id': protein_data['basic_info']['uniprot_id'],
                'name': protein_data['basic_info'].get('name', '')
            }
            
            # This will automatically search for similar structures
            from utils.visualization import display_protein_structure
            display_protein_structure(temp_info)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Protein-protein interactions
    interactions = protein_data.get("interactions", {}).get("interactions", [])
    
    if interactions:
        st.markdown("<div class='protein-card'>", unsafe_allow_html=True)
        st.subheader("Protein-Protein Interactions")
        
        # Create a network visualization
        try:
            network_chart = create_interaction_network(interactions)
            if network_chart:
                st.plotly_chart(network_chart, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating interaction network: {str(e)}")
        
        # List top interactions
        st.markdown("### Top Interactions")
        
        interaction_cols = st.columns(3)
        for i, interaction in enumerate(interactions[:6]):
            with interaction_cols[i % 3]:
                st.markdown(f"**{interaction.get('interactor_name', 'Unknown')}**")
                st.markdown(f"Score: {interaction.get('score', 'Unknown')}")
                st.markdown(f"Type: {interaction.get('interaction_type', 'Unknown')}")
        
        # Add link to STRING if available
        if protein_data.get("interactions", {}).get("network_url"):
            st.markdown(f"[View full interaction network]({protein_data['interactions']['network_url']})")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Disease and drug associations
    diseases = protein_data.get("disease_drug", {}).get("diseases", [])
    drugs = protein_data.get("disease_drug", {}).get("drugs", [])
    
    if diseases or drugs:
        st.markdown("<div class='protein-card'>", unsafe_allow_html=True)
        st.subheader("Disease & Drug Associations")
        
        if diseases:
            st.markdown("### Associated Diseases")
            
            # Create a disease chart
            try:
                disease_chart = create_disease_chart(diseases)
                if disease_chart:
                    st.plotly_chart(disease_chart, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating disease chart: {str(e)}")
            
            # List top diseases
            for disease in diseases[:5]:
                st.markdown(f"**{disease.get('disease_name', 'Unknown')}**")
                if disease.get('description'):
                    st.markdown(f"{disease.get('description')}")
                st.markdown(f"Score: {disease.get('score', 'Unknown')}")
                st.markdown("---")
        
        if drugs:
            st.markdown("### Associated Drugs")
            
            # Create a drug chart
            try:
                drug_chart = create_drug_chart(drugs)
                if drug_chart:
                    st.plotly_chart(drug_chart, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating drug chart: {str(e)}")
            
            # List top drugs
            for drug in drugs[:5]:
                st.markdown(f"**{drug.get('name', 'Unknown')}**")
                st.markdown(f"Type: {drug.get('type', 'Unknown')}")
                if drug.get('mechanism'):
                    st.markdown(f"Mechanism: {drug.get('mechanism')}")
                st.markdown(f"Status: {', '.join(drug.get('groups', ['Unknown']))}")
                st.markdown("---")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Sequence information
    if basic_info.get("sequence"):
        st.markdown("<div class='protein-card'>", unsafe_allow_html=True)
        st.subheader("Protein Sequence")
        
        sequence = basic_info.get("sequence", "")
        if len(sequence) > 100:
            st.markdown(f"```\n{sequence[:50]}...{sequence[-50:]}\n```")
            st.caption(f"Showing first and last 50 amino acids of {len(sequence)} total")
        else:
            st.markdown(f"```\n{sequence}\n```")
        
        # Add a button to show the full sequence
        if st.button("Show Full Sequence"):
            st.markdown(f"```\n{sequence}\n```")
        
        st.markdown("</div>", unsafe_allow_html=True)

# Function to display chat interface
def display_chat_interface():
    """Display the chat interface for follow-up questions"""
    st.markdown("<div class='protein-card'>", unsafe_allow_html=True)
    st.subheader("Ask Follow-up Questions")
    
    # Add data source indicator
    if st.session_state.protein_data:
        data_source = st.session_state.protein_data.get("data_source", "Unknown")
        st.caption(f"Using data from {data_source}")
    
    # Display chat history
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"<div class='chat-user'><strong>You:</strong> {message['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-assistant'><strong>While(1)Amino:</strong> {message['content']}</div>", unsafe_allow_html=True)
    
    # Input for new questions
    if st.session_state.current_protein:
        # Create a form for question submission
        with st.form("chat_form"):
            question = st.text_input(
                "Ask a question about this protein:", 
                placeholder="E.g., What diseases is this protein associated with?"
            )
            submit_button = st.form_submit_button("Submit")
            
            if submit_button and question:
                # Add user message to chat
                st.session_state.messages.append({"role": "user", "content": question})
                
                # Get answer from service
                with st.spinner("While(1)Amino is thinking..."):
                    try:
                        chat_history = []
                        for message in st.session_state.messages[:-1]:
                            chat_history.append({
                                "role": message["role"],
                                "content": message["content"]
                            })
                        
                        response = protein_service.get_protein_chat_response(
                            st.session_state.current_protein, 
                            chat_history, 
                            question
                        )
                        
                        if "error" in response:
                            answer_text = f"Error: {response['error']}"
                        else:
                            answer_text = response["response"]
                            
                    except Exception as e:
                        logger.error(f"Error processing question: {str(e)}")
                        answer_text = f"Error: I couldn't process your question. {str(e)}"
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": answer_text})
                
                # Force rerun to update the display
                st.rerun()
    else:
        st.info("Search for a protein first to ask follow-up questions.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Add download report button after chat interface
    if st.session_state.protein_data:
        st.markdown("<div class='protein-card'>", unsafe_allow_html=True)
        st.subheader("Download Report")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.download_button(
                label="📄 Download Medical Report",
                data=create_medical_report(st.session_state.protein_data),
                file_name=f"{st.session_state.protein_data.get('basic_info', {}).get('uniprot_id', 'protein')}_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            ):
                st.success("Report downloaded successfully!")
        st.markdown("</div>", unsafe_allow_html=True)

def main():
    """Main function to run the app"""
    # Header
    st.title("🧬 While(1)Amino")
    st.caption("Interactive Protein Analysis Platform")
    
    # Search bar
    st.markdown("<div class='search-container'>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    
    with col1:
        protein_query = st.text_input(
            "Enter a protein name or gene symbol:", 
            placeholder="e.g., BRCA1, TP53, Insulin",
            key="protein_search"
        )
    
    with col2:
        st.markdown("<div style='margin-top: 25px;'>", unsafe_allow_html=True)
        if st.button("Search", type="primary", use_container_width=True):
            if protein_query:
                # Reset chat history when searching for a new protein
                if protein_query != st.session_state.current_protein:
                    st.session_state.messages = []
                
                # Set current protein
                st.session_state.current_protein = protein_query
                
                # Get protein data
                with st.spinner(f"Searching for {protein_query}..."):
                    protein_data = get_protein_data(protein_query)
                    
                    # Store in session state
                    st.session_state.protein_data = protein_data
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Display protein information if available
    if st.session_state.current_protein and st.session_state.protein_data:
        if "error" not in st.session_state.protein_data:
            # Display data source indicator
            data_source = st.session_state.protein_data.get("data_source", "Unknown")
            st.success(f"Data retrieved from {data_source}")
            
            # Display protein information
            display_protein_info(st.session_state.protein_data)
            
            # Display chat interface
            display_chat_interface()
        else:
            st.error(f"Error: {st.session_state.protein_data['error']}")
            
            # Suggest similar proteins or common proteins
            st.markdown("### Try searching for these common proteins instead:")
            common_proteins = ["TP53", "BRCA1", "APOE", "INS", "APP", "EGFR"]
            cols = st.columns(3)
            for i, protein in enumerate(common_proteins):
                with cols[i % 3]:
                    if st.button(protein, key=f"suggest_{protein}"):
                        st.session_state.current_protein = protein
                        st.rerun()
    else:
        # Welcome message
        st.markdown("""
        <div class='protein-card'>
        <h3>Welcome to While(1)Amino!</h3>
        <p>Search for a protein or gene to get started. You can:</p>
        <ul>
            <li>View comprehensive protein information from NCBI or UniProt</li>
            <li>Explore 3D structures from PDB and AlphaFold</li>
            <li>Discover protein-protein interactions from STRING</li>
            <li>Learn about disease associations and potential drug targets</li>
            <li>Ask follow-up questions in a chat interface</li>
        </ul>
        <p>Try searching for example proteins like TP53, BRCA1, or Insulin using the search bar above.</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
