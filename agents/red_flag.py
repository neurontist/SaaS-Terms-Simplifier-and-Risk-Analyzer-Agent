from typing import Dict, List, Any
import google.generativeai as genai
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GOOGLE_API_KEY, GEMINI_MODEL
import json

class RedFlagAgent:
    def __init__(self, api_key: str = None):
        """
        Initialize the red flag detection agent with Gemini API.
        
        Args:
            api_key (str): Google Gemini API key
        """
        self.api_key = api_key or GOOGLE_API_KEY
        genai.configure(api_key=self.api_key)
        
        # Initialize LangChain components
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=self.api_key,
            temperature=0.1  # Lower temperature for more consistent results
        )
        
        # Initialize prompt template
        self.prompt = PromptTemplate(
            input_variables=["text", "saas_name"],
            template="""
            You are a legal expert analyzing SaaS Terms & Conditions for potential risks.
            Please analyze the following text and identify any concerning clauses or red flags.
            
            SaaS Name: {saas_name}
            Text to analyze: {text}
            
            For each red flag found, provide:
            1. The exact clause or phrase
            2. Category (Data Privacy, Termination, Payment, etc.)
            3. Severity level (Low, Medium, High)
            4. Explanation of the risk
            5. Potential impact on users
            
            Format the response as a JSON object with the following structure:
            {{
                "red_flags": [
                    {{
                        "clause": "exact text of the concerning clause",
                        "category": "category name",
                        "severity": "severity level",
                        "explanation": "detailed explanation",
                        "impact": "potential impact on users"
                    }}
                ]
            }}

            Ensure the response is a valid JSON object. Do not include any text before or after the JSON.
            """
        )
        
        # Initialize chain
        self.chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt
        )
    
    def detect_red_flags(
        self,
        text: str,
        saas_name: str = None
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Detect red flags in the input text.
        
        Args:
            text (str): Text to analyze
            saas_name (str): Optional name of the SaaS product
            
        Returns:
            Dict[str, List[Dict[str, str]]]: Detected red flags with metadata
        """
        try:
            # Generate analysis
            response = self.chain.run(
                text=text,
                saas_name=saas_name or "the service"
            )
            
            # Parse the JSON response
            try:
                result = json.loads(response)
                red_flags = result.get("red_flags", [])
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from the response
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    try:
                        result = json.loads(response[start:end])
                        red_flags = result.get("red_flags", [])
                    except json.JSONDecodeError:
                        red_flags = []
                else:
                    red_flags = []
            
            # Validate and clean up red flags
            validated_flags = []
            for flag in red_flags:
                if all(key in flag for key in ["clause", "category", "severity", "explanation", "impact"]):
                    # Ensure severity is one of the expected values
                    flag["severity"] = flag["severity"].title()
                    if flag["severity"] not in ["Low", "Medium", "High"]:
                        flag["severity"] = "Medium"
                    validated_flags.append(flag)
            
            return {
                "red_flags": validated_flags,
                "metadata": {
                    "model": GEMINI_MODEL,
                    "saas_name": saas_name,
                    "input_length": len(text),
                    "flags_found": len(validated_flags)
                }
            }
        except Exception as e:
            print(f"Error in detect_red_flags: {str(e)}")  # Add debugging
            return {
                "red_flags": [],
                "metadata": {
                    "model": GEMINI_MODEL,
                    "saas_name": saas_name,
                    "input_length": len(text),
                    "error": str(e)
                }
            }
    
    def get_severity_color(self, severity: str) -> str:
        """
        Get the color code for a severity level.
        
        Args:
            severity (str): Severity level (Low, Medium, High)
            
        Returns:
            str: Color code
        """
        severity_colors = {
            "Low": "🟢",
            "Medium": "🟡",
            "High": "🔴"
        }
        return severity_colors.get(severity, "⚪")
    
    def group_by_category(
        self,
        red_flags: List[Dict[str, str]]
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Group red flags by category.
        
        Args:
            red_flags (List[Dict[str, str]]): List of red flags
            
        Returns:
            Dict[str, List[Dict[str, str]]]: Red flags grouped by category
        """
        categories = {}
        for flag in red_flags:
            category = flag.get("category", "Other")
            if category not in categories:
                categories[category] = []
            categories[category].append(flag)
        return categories 