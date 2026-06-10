from typing import Callable, List, Dict, Any

class PluginRegistry:
    """Enterprise plugin architecture for custom business logic."""
    def __init__(self):
        self.matchers: List[Callable] = []
        self.validators: List[Callable] = []
        self.planners: List[Callable] = []

    def register_matcher(self, func: Callable):
        self.matchers.append(func)
        return func

    def register_validator(self, func: Callable):
        self.validators.append(func)
        return func

    def register_planner_hook(self, func: Callable):
        self.planners.append(func)
        return func

    def run_validators(self, sql: str, plan: Any) -> List[str]:
        errors = []
        for v in self.validators:
            err = v(sql, plan)
            if err:
                errors.append(err)
        return errors

# Global instance for the platform
registry = PluginRegistry()
