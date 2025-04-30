from typing import Dict, Any
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GOOGLE_API_KEY, GEMINI_MODEL

class ExecutiveSummaryAgent:
    def __init__(self, api_key: str = None):
        """
        Initialize the executive summary generator with Gemini API.
        
        Args:
            api_key (str): Google Gemini API key
        """
        self.api_key = api_key or GOOGLE_API_KEY
        
        # Initialize LangChain components
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=self.api_key,
            temperature=0.1  # Lower temperature for more consistent results
        )
        
        # Initialize prompt template
        self.prompt = PromptTemplate(
            input_variables=["text", "saas_name", "summary_type"],
            template="""
            You are a legal expert creating an executive summary of SaaS Terms & Conditions.
            Please create a concise summary of the following text, focusing on the most important points.
            
            SaaS Name: {saas_name}
            Summary Type: {summary_type}
            Text to summarize: {text}
            
            For each section, provide:
            1. A clear, concise summary
            2. Key points to note
            3. Any important implications
            
            Format the response as a JSON object with the following structure:
            {{
                "summary": "overall summary",
                "sections": [
                    {{
                        "title": "section title",
                        "summary": "section summary",
                        "key_points": ["point 1", "point 2", ...],
                        "implications": ["implication 1", "implication 2", ...]
                    }}
                ],
                "metadata": {{
                    "saas_name": "name of the SaaS",
                    "summary_type": "type of summary",
                    "input_length": length of input text
                }}
            }}
            """
        )
        
        # Initialize chain
        self.chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt
        )
    
    def generate_summary(
        self,
        text: str,
        saas_name: str = None,
        summary_type: str = "non-technical"
    ) -> Dict[str, Any]:
        """
        Generate an executive summary of the input text.
        
        Args:
            text (str): Text to summarize
            saas_name (str): Optional name of the SaaS product
            summary_type (str): Type of summary to generate (technical or non-technical)
            
        Returns:
            Dict[str, Any]: Generated summary with metadata
        """
        try:
            # Generate summary
            response = self.chain.run(
                text=text,
                saas_name=saas_name or "the service",
                summary_type=summary_type
            )
            
            # Parse the response (simplified for this example)
            # In a real implementation, you would properly parse the JSON response
            return {
                "summary": "",
                "sections": [],
                "metadata": {
                    "model": GEMINI_MODEL,
                    "saas_name": saas_name,
                    "summary_type": summary_type,
                    "input_length": len(text)
                }
            }
        except Exception as e:
            raise Exception(f"Error generating summary: {str(e)}")
    
    def format_summary(self, summary: Dict[str, Any]) -> str:
        """
        Format the summary for display.
        
        Args:
            summary (Dict[str, Any]): Summary to format
            
        Returns:
            str: Formatted summary
        """
        formatted = []
        
        # Add overall summary
        formatted.append("## Overall Summary")
        formatted.append(summary.get("summary", ""))
        formatted.append("")
        
        # Add section summaries
        formatted.append("## Section Summaries")
        for section in summary.get("sections", []):
            formatted.append(f"### {section.get('title', '')}")
            formatted.append(section.get("summary", ""))
            formatted.append("")
            
            formatted.append("#### Key Points")
            for point in section.get("key_points", []):
                formatted.append(f"- {point}")
            formatted.append("")
            
            formatted.append("#### Implications")
            for implication in section.get("implications", []):
                formatted.append(f"- {implication}")
            formatted.append("")
        
        return "\n".join(formatted) 