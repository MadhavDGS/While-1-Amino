from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import io

def create_medical_report(protein_data):
    """
    Create a professional medical-style PDF report for protein analysis
    """
    # Create a buffer to store the PDF
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Initialize story (content) for the PDF
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#2c3e50')
    ))
    
    # Add header
    story.append(Paragraph("While(1)Amino Protein Analysis Report", styles['CustomTitle']))
    story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Basic Information Section
    basic_info = protein_data.get('basic_info', {})
    story.append(Paragraph("Basic Information", styles['SectionHeader']))
    
    basic_info_data = [
        ['Protein Name:', basic_info.get('protein_name', 'N/A')],
        ['Gene Names:', ', '.join(basic_info.get('gene_names', ['N/A']))],
        ['UniProt ID:', basic_info.get('uniprot_id', 'N/A')],
        ['Organism:', basic_info.get('organism', 'N/A')],
        ['Length:', f"{basic_info.get('length', 'N/A')} amino acids"],
    ]
    
    table = Table(basic_info_data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6'))
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Summary Section
    if basic_info.get('summary'):
        story.append(Paragraph("Summary", styles['SectionHeader']))
        story.append(Paragraph(basic_info.get('summary', ''), styles['Normal']))
        story.append(Spacer(1, 20))
    
    # Function Section
    if basic_info.get('function'):
        story.append(Paragraph("Function", styles['SectionHeader']))
        story.append(Paragraph(basic_info.get('function', ''), styles['Normal']))
        story.append(Spacer(1, 20))
    
    # Disease Associations
    diseases = protein_data.get('disease_drug', {}).get('diseases', [])
    if diseases:
        story.append(Paragraph("Disease Associations", styles['SectionHeader']))
        disease_data = [[
            'Disease Name',
            'Score',
            'Description'
        ]]
        for disease in diseases[:5]:  # Top 5 diseases
            disease_data.append([
                disease.get('disease_name', 'N/A'),
                str(disease.get('score', 'N/A')),
                disease.get('description', 'N/A')[:100] + '...' if disease.get('description', '') else 'N/A'
            ])
        
        table = Table(disease_data, colWidths=[2*inch, 1*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6'))
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
    
    # Drug Associations
    drugs = protein_data.get('disease_drug', {}).get('drugs', [])
    if drugs:
        story.append(Paragraph("Drug Associations", styles['SectionHeader']))
        drug_data = [[
            'Drug Name',
            'Type',
            'Status'
        ]]
        for drug in drugs[:5]:  # Top 5 drugs
            drug_data.append([
                drug.get('name', 'N/A'),
                drug.get('type', 'N/A'),
                ', '.join(drug.get('groups', ['N/A']))
            ])
        
        table = Table(drug_data, colWidths=[2*inch, 2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6'))
        ]))
        story.append(table)
    
    # Footer
    story.append(Spacer(1, 30))
    footer_text = (
        "This report was generated by While(1)Amino - Protein Insights Platform. "
        "The information provided is based on data from various biological databases "
        "including UniProt, NCBI, PDB, AlphaFold, STRING, and more. This report is "
        "for research purposes only."
    )
    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray
    )))
    
    # Build the PDF
    doc.build(story)
    buffer.seek(0)
    return buffer 