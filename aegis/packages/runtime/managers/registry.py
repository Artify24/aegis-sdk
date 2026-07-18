from typing import Sequence, Any, Dict, List
from packages.models import ToolMetadata, RegisteredTool

class ToolRegistryError(Exception):
    """Base exception for ToolRegistry errors."""
    pass

class ToolNotFoundError(ToolRegistryError):
    """Raised when a tool is not found in the registry."""
    pass

class ToolRegistry:
    """
    The Tool Registry is the source of truth for all executable tools.
    It manages tool registration, metadata extraction, and lookup.
    """
    def __init__(self):
        self._tools: Dict[str, RegisteredTool] = {}

    def register_tool(self, executable: Any, metadata: ToolMetadata | None = None) -> None:
        """
        Registers an executable tool. If metadata is not provided, attempts to 
        extract it from the executable (e.g., LangChain BaseTool properties).
        """
        if metadata is None:
            metadata = self._extract_metadata(executable)
            
        if not metadata.name:
            raise ToolRegistryError("Tool must have a name.")
            
        self._tools[metadata.name] = RegisteredTool(
            metadata=metadata,
            executable=executable
        )

    def _extract_metadata(self, executable: Any) -> ToolMetadata:
        """Extracts metadata from various tool formats."""
        name = getattr(executable, "name", getattr(executable, "__name__", "unknown"))
        description = getattr(executable, "description", getattr(executable, "__doc__", ""))
        
        return ToolMetadata(
            name=name,
            description=description.strip() if description else ""
        )

    def get_tool(self, name: str) -> RegisteredTool:
        """Retrieves a registered tool by name. Raises ToolNotFoundError if missing."""
        tool = self._tools.get(name)
        if not tool:
            raise ToolNotFoundError(f"Tool '{name}' is not registered.")
        return tool
        
    def get_metadata(self, name: str) -> ToolMetadata:
        """Retrieves only the metadata for a specific tool."""
        return self.get_tool(name).metadata

    def list_tools(self, include_disabled: bool = False) -> List[RegisteredTool]:
        """Lists all registered tools."""
        return [
            tool for tool in self._tools.values()
            if include_disabled or tool.metadata.enabled
        ]
        
    def get_enabled_tools(self) -> List[RegisteredTool]:
        """Returns only enabled tools."""
        return self.list_tools(include_disabled=False)

