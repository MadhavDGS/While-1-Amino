# While(1)Amino - Protein Insights Platform

A Streamlit web application that provides biological insights about human proteins/genes with a ChatGPT-like interface. Retrieves data from multiple biological databases including:

- UniProt
- PDB
- AlphaFold  
- STRING
- DisGeNET
- DrugBank

## Features

- Protein/gene search with instant biological insights
- Protein structure visualization
- Protein-protein interaction networks
- Disease and drug associations
- Natural language Q&A interface

## Installation

```bash
git clone https://github.com/MadhavDGS/While-1-Amino.git
cd While-1-Amino
pip install -r requirements.txt
```

## Usage

```bash
streamlit run streamlit_app.py
```

## Data Sources

This application integrates data from multiple authoritative biological databases to provide comprehensive protein insights.

## License

MIT License

## Project Structure

```
AminoVerse/
├── streamlit_app.py   # Main Streamlit application
├── data/              # Data integration modules
│   ├── protein_data_service.py  # Main service
│   ├── uniprot_api.py           # UniProt connector
│   ├── structure_api.py         # PDB/AlphaFold connector
│   ├── interaction_api.py       # STRING connector
│   └── disease_drug_api.py      # DisGeNET/DrugBank connector
├── utils/             # Utility functions
│   └── visualization.py         # Visualization components
├── run_streamlit_only.py  # Script to run the application
├── requirements.txt   # Dependencies
└── README.md          # Documentation
```
## Future Improvements

- Add more advanced NLP for follow-up questions
- Integrate additional biological databases
- Implement user accounts and saved searches
- Add more interactive visualizations
- Enhance mobile responsiveness

## Acknowledgments

- This project uses free public APIs from UniProt, PDB, AlphaFold, STRING, DisGeNET, and DrugBank
- Built with Streamlit and Flask
