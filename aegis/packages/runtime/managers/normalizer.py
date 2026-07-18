import json
import logging
from typing import Any, Tuple
from packages.models import NormalizedExecutionResult, ExecutionMetadata

logger = logging.getLogger(__name__)

class ResultNormalizer:
    """
    Normalizes raw tool outputs into a standard format to protect the LLM context
    from massive payloads, binary data, and unhandled errors.
    """
    def __init__(self, max_length: int = 4000):
        self.max_length = max_length
        
    def normalize(self, execution_output: Tuple[Any, ExecutionMetadata]) -> NormalizedExecutionResult:
        """
        Takes the tuple from TimeoutManager/RetryManager and returns a safe, truncated
        NormalizedExecutionResult ready for the Planner.
        """
        raw_output, metadata = execution_output
        logger.debug(f"Normalizing output for {metadata.tool_name}")
        
        output_str = ""
        
        # 1. Handle Errors
        if not metadata.success:
            error_details = metadata.exception_details or "Unknown Error"
            output_str = f"Execution Failed: {error_details}\nRaw Output: {raw_output}"
            output_str = self._truncate(output_str)
            return self._build_result(metadata, output_str)
            
        # 2. Handle Binary Data
        if isinstance(raw_output, bytes) or isinstance(raw_output, bytearray):
            output_str = f"[BINARY DATA OMITTED: {len(raw_output)} bytes]"
            return self._build_result(metadata, output_str)
            
        # 3. Handle JSON / Dictionaries
        if isinstance(raw_output, (dict, list)):
            try:
                # Compact JSON is better for LLM context than highly indented JSON,
                # but indentation helps readability. We use a middle ground (indent=2)
                # up to the truncation limit.
                output_str = json.dumps(raw_output, indent=2)
            except Exception:
                output_str = str(raw_output)
                
        # 4. Handle Strings (Text / HTML)
        elif isinstance(raw_output, str):
            output_str = raw_output
            if output_str.strip().startswith("<html") or output_str.strip().startswith("<!DOCTYPE html>"):
                logger.debug("HTML document detected.")
                # Future expansion: strip tags using BeautifulSoup to save tokens.
        else:
            output_str = str(raw_output)
            
        # 5. Apply Universal Truncation
        output_str = self._truncate(output_str)
        
        return self._build_result(metadata, output_str)
        
    def _truncate(self, text: str) -> str:
        if len(text) > self.max_length:
            return text[:self.max_length] + f"\n... [TRUNCATED {len(text) - self.max_length} characters]"
        return text
        
    def _build_result(self, metadata: ExecutionMetadata, output_str: str) -> NormalizedExecutionResult:
        return NormalizedExecutionResult(
            tool_name=metadata.tool_name,
            success=metadata.success,
            output=output_str,
            metadata=metadata
        )
