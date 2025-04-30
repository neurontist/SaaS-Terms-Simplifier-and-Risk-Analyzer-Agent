from typing import Dict, Any
import json
import markdown
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO

class OutputParser:
    def __init__(self):
        """Initialize the output parser with custom styles."""
        self.styles = self.define_custom_styles()
    
    def define_custom_styles(self):
        """Define all custom styles for the document."""
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20
        ))
        styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=15
        ))
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=10
        ))
        return styles
    
    def generate_pdf(self, data: Dict[str, Any]) -> bytes:
        """
        Generate a PDF report from the analysis data.
        
        Args:
            data (Dict[str, Any]): Analysis data including summaries and red flags
            
        Returns:
            bytes: PDF file content as bytes
        """
        # Create a buffer for the PDF
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create the story (content)
        story = []
        
        # Add title
        story.append(Paragraph("SaaS Terms Analysis Report", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        # Add metadata
        story.append(Paragraph("Metadata", self.styles['CustomHeading2']))
        metadata = data.get("metadata", {})
        story.append(Paragraph(f"SaaS Name: {metadata.get('saas_name', 'Not specified')}", self.styles['CustomBody']))
        story.append(Paragraph(f"Summary Type: {metadata.get('summary_type', 'Not specified')}", self.styles['CustomBody']))
        story.append(Paragraph(f"Model: {metadata.get('model', 'Not specified')}", self.styles['CustomBody']))
        story.append(Spacer(1, 12))
        
        # Add executive summary
        if "executive_summary" in data:
            story.append(Paragraph("Executive Summary", self.styles['CustomHeading2']))
            story.append(Paragraph(data["executive_summary"].get("summary", "No executive summary available."), self.styles['CustomBody']))
            story.append(Spacer(1, 12))
        
        # Add detailed summaries
        if "summaries" in data:
            story.append(Paragraph("Detailed Section Summaries", self.styles['CustomHeading2']))
            for i, summary in enumerate(data["summaries"], 1):
                story.append(Paragraph(f"Section {i}", self.styles['CustomHeading2']))
                story.append(Paragraph(summary.get("summary", "No summary available."), self.styles['CustomBody']))
                story.append(Spacer(1, 12))
        
        # Add red flags
        if "red_flags" in data:
            story.append(Paragraph("Red Flags", self.styles['CustomHeading2']))
            
            # Group flags by severity
            severity_groups = {
                "High": [],
                "Medium": [],
                "Low": []
            }
            
            for flag in data["red_flags"]:
                severity = flag.get("severity", "Unknown")
                if severity in severity_groups:
                    severity_groups[severity].append(flag)
            
            # Add flags by severity
            severity_emojis = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
            for severity, flags in severity_groups.items():
                if flags:
                    story.append(Paragraph(f"{severity_emojis.get(severity, '')} {severity} Severity", self.styles['CustomHeading2']))
                    for flag in flags:
                        story.append(Paragraph(flag.get('category', 'Uncategorized'), self.styles['CustomHeading2']))
                        story.append(Paragraph(f"Clause: {flag.get('clause', 'Not specified')}", self.styles['CustomBody']))
                        story.append(Paragraph(f"Explanation: {flag.get('explanation', 'Not provided')}", self.styles['CustomBody']))
                        story.append(Paragraph(f"Impact: {flag.get('impact', 'Not specified')}", self.styles['CustomBody']))
                        story.append(Spacer(1, 12))
        
        # Build the PDF
        doc.build(story)
        
        # Get the value of the BytesIO buffer
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def export_to_json(self, data: Dict[str, Any], output_path: str) -> str:
        """Export data to JSON format."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return output_path
    
    def export_to_markdown(self, data: Dict[str, Any], output_path: str) -> str:
        """Export data to Markdown format."""
        markdown_content = []
        
        # Add title and metadata
        markdown_content.append("# SaaS Terms Analysis Report\n")
        
        # Add metadata
        metadata = data.get("metadata", {})
        if metadata:
            markdown_content.append("## Analysis Details")
            markdown_content.append(f"- SaaS Name: {metadata.get('saas_name', 'Not specified')}")
            markdown_content.append(f"- Summary Type: {metadata.get('summary_type', 'Not specified')}")
            markdown_content.append(f"- Model: {metadata.get('model', 'Not specified')}\n")
        
        # Add executive summary
        if "executive_summary" in data:
            markdown_content.append("## Executive Summary")
            markdown_content.append(data["executive_summary"].get("summary", ""))
            markdown_content.append("")
        
        # Add detailed summaries
        if "summaries" in data:
            markdown_content.append("## Detailed Summaries")
            for i, summary in enumerate(data["summaries"], 1):
                markdown_content.append(f"### Section {i}")
                markdown_content.append(summary.get("summary", ""))
                markdown_content.append("")
        
        # Add red flags
        if "red_flags" in data:
            markdown_content.append("## Red Flags")
            
            # Group by severity
            severity_groups = {
                "High": "🔴",
                "Medium": "🟡",
                "Low": "🟢"
            }
            
            for severity, emoji in severity_groups.items():
                flags = [f for f in data["red_flags"] if f.get("severity") == severity]
                if flags:
                    markdown_content.append(f"\n### {emoji} {severity} Severity")
                    for flag in flags:
                        markdown_content.append(f"\n#### {flag.get('category', '')}")
                        markdown_content.append(f"**Clause:** {flag.get('clause', '')}")
                        markdown_content.append(f"**Explanation:** {flag.get('explanation', '')}")
                        markdown_content.append(f"**Impact:** {flag.get('impact', '')}\n")
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_content))
        
        return output_path
    
    def export_to_pdf(
        self,
        data: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Export data to PDF format.
        
        Args:
            data (Dict[str, Any]): Data to export
            output_path (str): Output file path
            
        Returns:
            str: Path to the exported file
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Add title
        title = Paragraph(
            f"SaaS Terms Analysis: {data.get('saas_name', 'Unknown Service')}",
            self.styles['CustomHeading1']
        )
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Add summary
        if 'summary' in data:
            story.append(Paragraph("Summary", self.styles['CustomHeading2']))
            story.append(Spacer(1, 12))
            story.append(Paragraph(data['summary'], self.styles['CustomBody']))
        
        # Add red flags
        if 'red_flags' in data:
            story.append(Paragraph("Red Flags", self.styles['CustomHeading2']))
            story.append(Spacer(1, 12))
            
            for flag in data['red_flags']:
                severity_emoji = {
                    'Low': '🟢',
                    'Medium': '🟡',
                    'High': '🔴'
                }.get(flag.get('severity', 'Unknown'), '⚪')
                
                story.append(Paragraph(
                    f"{severity_emoji} {flag.get('category', 'Unknown')}",
                    self.styles['CustomHeading2']
                ))
                story.append(Paragraph(
                    f"Clause: {flag.get('clause', '')}",
                    self.styles['CustomBody']
                ))
                story.append(Paragraph(
                    f"Explanation: {flag.get('explanation', '')}",
                    self.styles['CustomBody']
                ))
                story.append(Paragraph(
                    f"Impact: {flag.get('impact', '')}",
                    self.styles['CustomBody']
                ))
                story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        return output_path

    def generate_markdown(self, data: dict) -> str:
        """Generate a markdown formatted string from the analysis data."""
        markdown = []
        
        # Add title and metadata
        markdown.append("# SaaS Terms Analysis Report\n")
        
        # Add metadata section
        markdown.append("## Metadata\n")
        metadata = data.get("metadata", {})
        markdown.append(f"- **SaaS Name**: {metadata.get('saas_name', 'Not specified')}")
        markdown.append(f"- **Summary Type**: {metadata.get('summary_type', 'Not specified')}")
        markdown.append(f"- **Model**: {metadata.get('model', 'Not specified')}\n")
        
        # Add executive summary section
        if "executive_summary" in data:
            markdown.append("## Executive Summary\n")
            markdown.append(data["executive_summary"].get("summary", "No executive summary available."))
            markdown.append("\n")
        
        # Add detailed summaries section
        if "summaries" in data:
            markdown.append("## Detailed Section Summaries\n")
            for i, summary in enumerate(data["summaries"], 1):
                markdown.append(f"### Section {i}\n")
                markdown.append(summary.get("summary", "No summary available."))
                markdown.append("\n")
        
        # Add red flags section
        if "red_flags" in data:
            markdown.append("## Red Flags\n")
            
            # Group flags by severity
            severity_groups = {
                "High": [],
                "Medium": [],
                "Low": []
            }
            
            for flag in data["red_flags"]:
                severity = flag.get("severity", "Unknown")
                if severity in severity_groups:
                    severity_groups[severity].append(flag)
            
            # Add flags by severity
            severity_emojis = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
            for severity, flags in severity_groups.items():
                if flags:
                    markdown.append(f"### {severity_emojis.get(severity, '')} {severity} Severity\n")
                    for flag in flags:
                        markdown.append(f"#### {flag.get('category', 'Uncategorized')}\n")
                        markdown.append(f"- **Clause**: {flag.get('clause', 'Not specified')}")
                        markdown.append(f"- **Explanation**: {flag.get('explanation', 'Not provided')}")
                        markdown.append(f"- **Impact**: {flag.get('impact', 'Not specified')}\n")
        
        return "\n".join(markdown) 