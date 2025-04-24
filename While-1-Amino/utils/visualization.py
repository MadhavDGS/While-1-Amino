import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import py3Dmol
import base64
import io
import requests
import streamlit as st
from stmol import showmol
from data.structure_api import ProteinStructureAPI

def create_interaction_network(interactions):
    """Create a network visualization of protein-protein interactions"""
    if not interactions or not isinstance(interactions, list):
        return None
    
    # Create nodes and edges for the network
    nodes = set()
    edges = []
    
    for interaction in interactions:
        source = interaction.get("source_name", "")
        target = interaction.get("target_name", "")
        score = interaction.get("score", 0)
        
        if source and target:
            nodes.add(source)
            nodes.add(target)
            edges.append((source, target, score))
    
    # Convert to dataframes
    nodes_df = pd.DataFrame({"name": list(nodes)})
    edges_df = pd.DataFrame(edges, columns=["source", "target", "score"])
    
    # Create network graph
    fig = go.Figure()
    
    # Add edges as lines
    for _, edge in edges_df.iterrows():
        source_idx = nodes_df[nodes_df["name"] == edge["source"]].index[0]
        target_idx = nodes_df[nodes_df["name"] == edge["target"]].index[0]
        
        # Calculate positions (in a real implementation, use a proper layout algorithm)
        x0, y0 = source_idx % 5, source_idx // 5
        x1, y1 = target_idx % 5, target_idx // 5
        
        # Line width based on score
        width = edge["score"] / 200  # Scale appropriately
        
        fig.add_trace(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode="lines",
            line=dict(width=width, color="rgba(150,150,150,0.5)"),
            hoverinfo="none"
        ))
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=[i % 5 for i in range(len(nodes))],
        y=[i // 5 for i in range(len(nodes))],
        mode="markers+text",
        text=list(nodes),
        textposition="bottom center",
        marker=dict(
            size=20,
            color="rgba(0,0,255,0.8)",
            line=dict(width=2, color="rgba(0,0,0,0.8)")
        ),
        hoverinfo="text"
    ))
    
    # Update layout
    fig.update_layout(
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=20, b=20),
        height=500,
        width=800,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    
    return fig

def create_disease_chart(diseases):
    """Create a chart showing disease associations"""
    if not diseases or not isinstance(diseases, list):
        return None
    
    # Prepare data
    df = pd.DataFrame(diseases)
    df = df.sort_values("score", ascending=False).head(10)
    
    # Create bar chart
    fig = px.bar(
        df,
        x="score",
        y="disease_name",
        orientation="h",
        title="Top Disease Associations",
        labels={"score": "Association Score", "disease_name": "Disease"},
        color="score",
        color_continuous_scale="Blues"
    )
    
    # Update layout
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
        width=800,
        showlegend=False
    )
    
    return fig

def fetch_pdb_structure(pdb_id):
    """Fetch a PDB structure from RCSB PDB"""
    try:
        url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            # Try alternative URL format
            url = f"https://files.rcsb.org/view/{pdb_id}.pdb"
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
        return None
    except Exception as e:
        print(f"Error fetching PDB structure: {str(e)}")
        return None

def fetch_alphafold_structure(uniprot_id):
    """Fetch an AlphaFold structure from EBI"""
    try:
        # First check if the file exists
        check_url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
        check_response = requests.get(check_url)
        
        if check_response.status_code != 200:
            return None
        
        # Fetch the actual structure
        url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v4.pdb"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.text
            
        # Try alternative version
        url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v3.pdb"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.text
            
        # Try v2 model as last resort
        url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v2.pdb"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.text
            
        return None
    except Exception as e:
        print(f"Error fetching AlphaFold structure: {str(e)}")
        return None

def create_3d_protein_viewer(structure_info):
    """Returns interactive 3D viewer with protein structure"""
    import py3Dmol
    import sys
    from pathlib import Path
    
    # Add project root to Python path
    project_root = str(Path(__file__).parent.parent.absolute())
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    from data.pdb_api import find_similar_pdb_structures
    from data.structure_api import ProteinStructureAPI
    
    # Validate structure info
    if not structure_info:
        raise ValueError("No structure information provided")
    
    if not isinstance(structure_info, dict):
        raise ValueError("Structure info must be a dictionary")
    
    # Validate and normalize structure info using ProteinStructureAPI
    structure_api = ProteinStructureAPI()
    try:
        structure_info = structure_api.validate_structure_info(structure_info)
    except ValueError as e:
        raise ValueError(f"Invalid structure info: {str(e)}")
    
    # Try to fetch structure based on source
    pdb_data = None
    if structure_info["source"] == "pdb":
        pdb_data = fetch_pdb_structure(structure_info["id"])
    elif structure_info["source"] == "alphafold":
        pdb_data = fetch_alphafold_structure(structure_info["id"])
    else:
        raise ValueError(f"Unsupported structure source: {structure_info.get('source')}")
    
    # If structure not found, try to find similar ones
    if not pdb_data and structure_info.get('uniprot_id'):
        try:
            similar_structures = find_similar_pdb_structures(structure_info['uniprot_id'])
            if similar_structures:
                # Use first similar structure
                first_structure = similar_structures[0]
                structure_info.update({
                    "id": first_structure['pdb_id'],
                    "source": "pdb",  # Similar structures are always from PDB
                    "method": first_structure['method'],
                    "resolution": first_structure['resolution'],
                    "title": first_structure.get('title', ''),
                    "description": f"Similar structure to {structure_info.get('name', 'target')}",
                    "similar_used": True,
                    "similar_structures": similar_structures,
                    "similarity_score": first_structure.get('similarity_score', 1.0)
                })
                # Validate the updated structure info
                structure_info = structure_api.validate_structure_info(structure_info)
                pdb_data = fetch_pdb_structure(first_structure['pdb_id'])
        except Exception as e:
            print(f"Error finding similar structures: {str(e)}")
    
    # If no structure found, raise an error
    if not pdb_data:
        raise ValueError(f"No structure data found for {structure_info.get('id', 'unknown protein')}")
    
    # Create viewer with the found structure
    view = py3Dmol.view(width=800, height=600)
    view.addModel(pdb_data, "pdb")
    
    # Style and annotate
    view.setStyle({'cartoon': {'color': 'spectrum'}})
    view.addSurface(py3Dmol.VDW, {'opacity': 0.7, 'color': 'white'})
    view.zoomTo()
    view.setBackgroundColor(0xeeeeee)
    
    return view, structure_info

def display_protein_structure(structure):
    """Displays protein structure with search results and PDB link"""
    import streamlit as st
    
    with st.expander("3D Protein Structure", expanded=True):
        try:
            # Validate structure info first
            if not structure:
                raise ValueError("No structure information provided")
                
            structure_api = ProteinStructureAPI()
            found_structure = False
            structure_info = None
            view = None
            error_messages = []
            
            # Try different structure sources
            try:
                # If structure is a list of structures, try each one
                if isinstance(structure, dict) and "structures" in structure:
                    structures_to_try = structure["structures"]
                else:
                    structures_to_try = [structure]
                
                for struct in structures_to_try:
                    try:
                        view, structure_info = create_3d_protein_viewer(struct)
                        found_structure = True
                        break
                    except ValueError as e:
                        error_messages.append(str(e))
                        continue
                    
                # If no direct structure found, try finding similar structures
                if not found_structure and isinstance(structure, dict):
                    # Try with UniProt ID
                    uniprot_id = structure.get('uniprot_id') or structure.get('id')
                    if uniprot_id:
                        try:
                            similar_structures = find_similar_pdb_structures(uniprot_id)
                            if similar_structures:
                                for similar in similar_structures:
                                    try:
                                        similar_info = {
                                            "id": similar['pdb_id'],
                                            "source": "pdb",
                                            "method": similar.get('method'),
                                            "resolution": similar.get('resolution'),
                                            "title": similar.get('title', ''),
                                            "description": f"Similar structure to {structure.get('name', 'target')}",
                                            "similar_used": True,
                                            "similarity_score": similar.get('similarity_score', 1.0),
                                            "similar_structures": similar_structures
                                        }
                                        view, structure_info = create_3d_protein_viewer(similar_info)
                                        found_structure = True
                                        break
                                    except Exception as e:
                                        error_messages.append(f"Error with similar structure {similar['pdb_id']}: {str(e)}")
                                        continue
                        except Exception as e:
                            error_messages.append(f"Error finding similar structures: {str(e)}")
            
            except Exception as e:
                error_messages.append(f"Error processing structures: {str(e)}")
            
            if not found_structure:
                raise ValueError("\n".join(error_messages))
            
            # Display the found structure
            showmol(view, height=600, width=800)
            
            # Show detailed structure information
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(f"{structure_info.get('name', 'Protein')} Structure")
                st.caption(f"Source: {structure_info['source'].upper()}")
                
                # Add source-specific links
                if structure_info['source'] == 'pdb':
                    pdb_id = structure_info['id']
                    st.markdown(f"[View on PDB](https://www.rcsb.org/structure/{pdb_id})")
                elif structure_info['source'] == 'alphafold':
                    uniprot_id = structure_info['id']
                    st.markdown(f"[View on AlphaFold](https://alphafold.ebi.ac.uk/entry/{uniprot_id})")
                
                st.caption(f"ID: {structure_info['id']}")
                if structure_info.get('uniprot_id'):
                    st.caption(f"UniProt ID: {structure_info['uniprot_id']}")
                
                if structure_info.get('title'):
                    st.caption(f"Title: {structure_info['title']}")
            
            with col2:
                st.caption(f"Method: {structure_info.get('method', 'Unavailable')}")
                if structure_info.get('resolution'):
                    st.caption(f"Resolution: {structure_info['resolution']}")
                if structure_info.get('description'):
                    st.caption(structure_info['description'])
            
            # Show search results if similar structures were used
            if structure_info.get('similar_used'):
                if structure_info.get('is_exact_match'):
                    st.success("✓ Exact structure match found")
                else:
                    similarity_score = structure_info.get('similarity_score', 0) * 100
                    st.info(f"Showing similar structure (Similarity: {similarity_score:.1f}%)")
                
                # Show other similar structures if available
                if structure_info.get('similar_structures'):
                    st.subheader("Other Similar Structures")
                    for similar in structure_info['similar_structures'][1:4]:  # Show up to 3 more similar structures
                        similarity = similar.get('similarity_score', 1.0) * 100
                        match_type = "Exact Match" if similar.get('is_exact_match') else f"Similarity: {similarity:.1f}%"
                        
                        st.markdown(
                            f"- [{similar['pdb_id']}]({similar['viewer_url']}) "
                            f"({similar['method']}, {similar['resolution']}) - {match_type}\n"
                            f"  {similar.get('title', '')}"
                        )
            
        except ValueError as e:
            st.error("Could not find any suitable structure")
            st.error("Detailed errors:")
            for line in str(e).split("\n"):
                st.caption(f"• {line}")
            
            st.markdown("""
            ### Suggestions:
            1. Check if the protein identifier is correct
            2. Try searching with a different identifier (UniProt ID, PDB ID, etc.)
            3. The protein structure may not have been experimentally determined yet
            4. Try searching for homologous proteins with known structures
            """)
        except Exception as e:
            st.error(f"Error displaying structure: {str(e)}")
            st.markdown("""
            ### Troubleshooting:
            1. Make sure you have a valid protein identifier
            2. Check that the structure source is either 'pdb' or 'alphafold'
            3. Ensure all required structure information is provided
            4. Try with a different protein if the issue persists
            """)
    
    return True

def create_go_terms_chart(go_terms):
    """Create a visualization of GO terms"""
    if not go_terms or not isinstance(go_terms, list):
        return None
    
    # Group by category
    categories = {}
    for term in go_terms:
        category = term.get("category", "Other")
        if category not in categories:
            categories[category] = []
        categories[category].append(term)
    
    # Create sunburst chart
    labels = []
    parents = []
    values = []
    
    # Add root
    labels.append("GO Terms")
    parents.append("")
    values.append(1)
    
    # Add categories
    for category, terms in categories.items():
        labels.append(category)
        parents.append("GO Terms")
        values.append(len(terms))
        
        # Add terms
        for term in terms:
            labels.append(term.get("term", ""))
            parents.append(category)
            values.append(1)
    
    # Create figure
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total"
    ))
    
    # Update layout
    fig.update_layout(
        title="GO Terms",
        margin=dict(t=30, l=0, r=0, b=0),
        height=500
    )
    
    return fig

def create_drug_chart(drugs):
    """Create a chart showing drug associations"""
    if not drugs or not isinstance(drugs, list):
        return None
    
    # Prepare data
    df = pd.DataFrame(drugs)
    
    # If score is not available, create a count-based visualization
    if "score" not in df.columns:
        # Count drug types and approval status
        drug_types = {}
        drug_groups = {"approved": 0, "investigational": 0, "experimental": 0, "other": 0}
        
        for drug in drugs:
            # Count drug types
            drug_type = drug.get("type", "Unknown")
            if drug_type in drug_types:
                drug_types[drug_type] += 1
            else:
                drug_types[drug_type] = 1
            
            # Count approval status
            groups = drug.get("groups", [])
            if groups:
                for group in groups:
                    group_lower = group.lower()
                    if group_lower in drug_groups:
                        drug_groups[group_lower] += 1
                    else:
                        drug_groups["other"] += 1
            else:
                drug_groups["other"] += 1
        
        # Create subplots
        from plotly.subplots import make_subplots
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "pie"}, {"type": "bar"}]],
            subplot_titles=("Drug Types", "Approval Status")
        )
        
        # Add pie chart for drug types
        fig.add_trace(
            go.Pie(
                labels=list(drug_types.keys()),
                values=list(drug_types.values()),
                hole=0.3 if len(drug_types) > 2 else 0,  # Only use hole for more than 2 types
                name="Drug Types",
                marker=dict(colors=px.colors.qualitative.Pastel),
                textinfo='label+percent',
                textposition='outside',
                pull=[0.1] * len(drug_types) if len(drug_types) == 2 else None  # Add slight pull for 2 types
            ),
            row=1, col=1
        )
        
        # Add bar chart for drug groups
        fig.add_trace(
            go.Bar(
                x=list(drug_groups.keys()),
                y=list(drug_groups.values()),
                marker_color=px.colors.qualitative.Pastel[1],
                name="Approval Status",
                text=list(drug_groups.values()),
                textposition='auto'
            ),
            row=1, col=2
        )
        
        # Update layout
        fig.update_layout(
            title="Drug Types and Approval Status",
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=20, r=20, t=60, b=20),
            height=400,
            width=800,
            showlegend=False,
            uniformtext_minsize=12,
            uniformtext_mode='hide'
        )
        
        # Update pie chart annotations
        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
            row=1, col=1
        )
        
        # Update bar chart annotations
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
            row=1, col=2
        )
        
        return fig
    
    # If score is available, create the original score-based visualization
    df = df.sort_values("score", ascending=False).head(10)
    
    # Create bar chart
    fig = px.bar(
        df,
        x="score",
        y="name",
        orientation="h",
        title="Top Drug Associations",
        labels={"score": "Association Score", "name": "Drug"},
        color="score",
        color_continuous_scale="Greens"
    )
    
    # Update layout
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
        width=800,
        showlegend=False
    )
    
    return fig
