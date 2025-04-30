from typing import Dict, List, Any
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GOOGLE_API_KEY, GEMINI_MODEL

class SummarizerAgent:
    def __init__(self, api_key: str = None):
        """
        Initialize the summarizer agent with Gemini API.
        
        Args:
            api_key (str): Google Gemini API key
        """
        self.api_key = api_key or GOOGLE_API_KEY
        
        # Initialize LangChain components
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=self.api_key,
            temperature=0.3
        )
        
        # Initialize prompt templates
        self.non_tech_prompt = PromptTemplate(
            input_variables=["text", "saas_name"],
            template="""
            You are a legal expert explaining SaaS Terms & Conditions in plain English.
            Please summarize the following text in simple, non-technical language that
            a regular person can understand. If a SaaS name is provided, use it in the
            explanation.
            
            SaaS Name: {saas_name}
            Text to summarize: {text}
            
            Please provide:
            1. A brief overview
            2. Key points in bullet form
            3. Any important implications for the user
            
            Keep the language simple and avoid legal jargon.
            """
        )
        
        self.tech_prompt = PromptTemplate(
            input_variables=["text", "saas_name"],
            template="""
            You are a technical expert analyzing SaaS Terms & Conditions.
            Please provide a technical summary of the following text, focusing on:
            - Technical requirements
            - API usage policies
            - Data handling procedures
            - Integration capabilities
            
            SaaS Name: {saas_name}
            Text to summarize: {text}
            
            Please provide:
            1. Technical overview
            2. Key technical specifications
            3. Integration requirements
            4. Technical limitations
            
            Use appropriate technical terminology but keep explanations clear.
            """
        )
        
        # Initialize chains
        self.non_tech_chain = LLMChain(
            llm=self.llm,
            prompt=self.non_tech_prompt
        )
        
        self.tech_chain = LLMChain(
            llm=self.llm,
            prompt=self.tech_prompt
        )
    
    def summarize(
        self,
        text: str,
        summary_type: str = "non-technical",
        saas_name: str = None
    ) -> Dict[str, Any]:
        """
        Generate a summary of the input text.
        
        Args:
            text (str): Text to summarize
            summary_type (str): Type of summary ("non-technical" or "technical")
            saas_name (str): Optional name of the SaaS product
            
        Returns:
            Dict[str, Any]: Summary with metadata
        """
        try:
            # Select appropriate chain
            chain = (
                self.non_tech_chain if summary_type == "non-technical"
                else self.tech_chain
            )
            
            # Generate summary
            response = chain.run(
                text=text,
                saas_name=saas_name or "the service"
            )
            
            return {
                "summary": response,
                "type": summary_type,
                "metadata": {
                    "model": GEMINI_MODEL,
                    "saas_name": saas_name,
                    "input_length": len(text),
                    "output_length": len(response)
                }
            }
        except Exception as e:
            raise Exception(f"Error generating summary: {str(e)}")
    
    def categorize_summary(self, summary: str) -> Dict[str, List[str]]:
        """
        Categorize the summary into different sections.
        
        Args:
            summary (str): Generated summary
            
        Returns:
            Dict[str, List[str]]: Categorized summary points
        """
        try:
            # Create categorization prompt
            categorization_prompt = PromptTemplate(
                input_variables=["summary"],
                template="""
                Please categorize the following summary points into these categories:
                - Data Use
                - Payments
                - Termination
                - Other
                
                Summary: {summary}
                
                Return the categorization as a JSON object with arrays for each category.
                """
            )
            
            # Create chain
            chain = LLMChain(
                llm=self.llm,
                prompt=categorization_prompt
            )
            
            # Get categorization
            response = chain.run(summary=summary)
            
            # Parse response (simplified for this example)
            # In a real implementation, you would properly parse the JSON response
            return {
                "Data Use": [],
                "Payments": [],
                "Termination": [],
                "Other": []
            }
        except Exception as e:
            raise Exception(f"Error categorizing summary: {str(e)}") 