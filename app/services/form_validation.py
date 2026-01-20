"""
JSONSchema validation service for form submissions
Supports all JSONSchema validation rules including conditional logic
"""
from typing import Dict, Any, List, Optional, Tuple
import jsonschema
from jsonschema import validate, ValidationError as JsonSchemaValidationError, Draft7Validator
from app.schemas.forms import ValidationResult, ValidationError as ValidationErrorSchema


class FormValidationService:
    """
    Service for validating form submissions against JSONSchema
    Supports conditional validation, dependencies, and custom business rules
    """
    
    @staticmethod
    def validate_submission(data: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
        """
        Validate submission data against a JSONSchema
        
        Args:
            data: Form submission data
            schema: JSONSchema to validate against
            
        Returns:
            ValidationResult with is_valid flag and list of errors
        """
        try:
            # Use Draft7Validator for better error messages
            validator = Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
            
            # Collect all validation errors
            errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
            
            if not errors:
                return ValidationResult(
                    is_valid=True,
                    errors=[],
                    message="Validation successful"
                )
            
            # Transform JSONSchema errors into user-friendly format
            validation_errors = FormValidationService._format_validation_errors(errors)
            
            return ValidationResult(
                is_valid=False,
                errors=validation_errors,
                message=f"Validation failed with {len(validation_errors)} error(s)"
            )
            
        except Exception as e:
            # Handle schema itself being invalid
            return ValidationResult(
                is_valid=False,
                errors=[ValidationErrorSchema(
                    field="__schema__",
                    message=f"Schema validation error: {str(e)}",
                    constraint="schema_error"
                )],
                message="Invalid schema configuration"
            )
    
    @staticmethod
    def validate_with_custom_rules(
        data: Dict[str, Any], 
        schema: Dict[str, Any], 
        custom_validators: Optional[Dict[str, callable]] = None
    ) -> ValidationResult:
        """
        Validate with both JSONSchema and custom business rules
        
        Args:
            data: Form submission data
            schema: JSONSchema to validate against
            custom_validators: Dict of field_name -> validation_function
            
        Returns:
            ValidationResult combining schema and custom validation
        """
        # First run JSONSchema validation
        result = FormValidationService.validate_submission(data, schema)
        
        # If custom validators provided, run them
        if custom_validators and result.is_valid:
            custom_errors = []
            for field_name, validator_func in custom_validators.items():
                try:
                    value = FormValidationService._get_nested_value(data, field_name)
                    is_valid, error_message = validator_func(value, data)
                    
                    if not is_valid:
                        custom_errors.append(ValidationErrorSchema(
                            field=field_name,
                            message=error_message,
                            constraint="custom_validation"
                        ))
                except Exception as e:
                    custom_errors.append(ValidationErrorSchema(
                        field=field_name,
                        message=f"Custom validation error: {str(e)}",
                        constraint="custom_validation_error"
                    ))
            
            if custom_errors:
                result.is_valid = False
                result.errors.extend(custom_errors)
                result.message = f"Validation failed with {len(result.errors)} error(s)"
        
        return result
    
    @staticmethod
    def _format_validation_errors(errors: List[JsonSchemaValidationError]) -> List[ValidationErrorSchema]:
        """
        Transform JSONSchema validation errors into user-friendly format
        
        Args:
            errors: List of jsonschema ValidationError objects
            
        Returns:
            List of formatted ValidationError schemas
        """
        formatted_errors = []
        
        for error in errors:
            # Build field path (e.g., "address.city" or "items[0].name")
            field_path = FormValidationService._build_field_path(error.absolute_path)
            
            # Get user-friendly error message
            message = FormValidationService._get_error_message(error)
            
            # Determine constraint type
            constraint = error.validator if hasattr(error, 'validator') else "unknown"
            
            formatted_errors.append(ValidationErrorSchema(
                field=field_path or "__root__",
                message=message,
                constraint=constraint
            ))
        
        return formatted_errors
    
    @staticmethod
    def _build_field_path(path) -> str:
        """
        Build a dot-notation field path from JSONSchema path
        
        Examples:
            ['address', 'city'] -> 'address.city'
            ['items', 0, 'name'] -> 'items[0].name'
        """
        if not path:
            return ""
        
        parts = []
        for item in path:
            if isinstance(item, int):
                parts[-1] = f"{parts[-1]}[{item}]"
            else:
                parts.append(str(item))
        
        return ".".join(parts)
    
    @staticmethod
    def _get_error_message(error: JsonSchemaValidationError) -> str:
        """
        Generate user-friendly error message from JSONSchema error
        """
        validator = error.validator
        
        # Customize messages based on validator type
        if validator == "required":
            missing_property = error.message.split("'")[1] if "'" in error.message else "field"
            return f"Required field '{missing_property}' is missing"
        
        elif validator == "type":
            expected_type = error.validator_value
            return f"Expected type '{expected_type}', got '{type(error.instance).__name__}'"
        
        elif validator == "minLength":
            min_len = error.validator_value
            actual_len = len(error.instance) if error.instance else 0
            return f"Must be at least {min_len} characters (got {actual_len})"
        
        elif validator == "maxLength":
            max_len = error.validator_value
            actual_len = len(error.instance) if error.instance else 0
            return f"Must be at most {max_len} characters (got {actual_len})"
        
        elif validator == "pattern":
            pattern = error.validator_value
            return f"Must match pattern: {pattern}"
        
        elif validator == "format":
            format_type = error.validator_value
            return f"Must be a valid {format_type}"
        
        elif validator == "minimum":
            min_val = error.validator_value
            return f"Must be at least {min_val}"
        
        elif validator == "maximum":
            max_val = error.validator_value
            return f"Must be at most {max_val}"
        
        elif validator == "minItems":
            min_items = error.validator_value
            return f"Must have at least {min_items} item(s)"
        
        elif validator == "maxItems":
            max_items = error.validator_value
            return f"Must have at most {max_items} item(s)"
        
        elif validator == "uniqueItems":
            return "All items must be unique"
        
        elif validator == "enum":
            allowed_values = error.validator_value
            return f"Must be one of: {', '.join(map(str, allowed_values))}"
        
        elif validator == "const":
            expected = error.validator_value
            return f"Must be exactly: {expected}"
        
        elif validator in ("oneOf", "anyOf", "allOf"):
            return f"Does not satisfy {validator} schema constraint"
        
        else:
            # Fallback to default message
            return error.message
    
    @staticmethod
    def _get_nested_value(data: Dict[str, Any], field_path: str) -> Any:
        """
        Get value from nested dictionary using dot notation
        
        Examples:
            data = {"address": {"city": "NYC"}}
            _get_nested_value(data, "address.city") -> "NYC"
        """
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        
        return value
    
    @staticmethod
    def check_conditional_requirements(
        data: Dict[str, Any], 
        schema: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Check if conditional requirements (if/then/else) are satisfied
        
        Args:
            data: Form submission data
            schema: JSONSchema with conditional logic
            
        Returns:
            Tuple of (all_satisfied, list_of_issues)
        """
        issues = []
        
        # Check if schema has conditional logic
        if "if" in schema:
            # Evaluate the 'if' condition
            if_schema = schema["if"]
            try:
                validate(instance=data, schema=if_schema)
                # If condition is satisfied, check 'then' schema
                if "then" in schema:
                    then_schema = schema["then"]
                    try:
                        validate(instance=data, schema=then_schema)
                    except JsonSchemaValidationError as e:
                        issues.append(f"Conditional 'then' failed: {e.message}")
            except JsonSchemaValidationError:
                # If condition is not satisfied, check 'else' schema
                if "else" in schema:
                    else_schema = schema["else"]
                    try:
                        validate(instance=data, schema=else_schema)
                    except JsonSchemaValidationError as e:
                        issues.append(f"Conditional 'else' failed: {e.message}")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def get_required_fields(schema: Dict[str, Any], data: Dict[str, Any] = None) -> List[str]:
        """
        Get list of required fields considering conditional logic
        
        Args:
            schema: JSONSchema
            data: Optional current form data to evaluate conditionals
            
        Returns:
            List of required field names
        """
        required = schema.get("required", [])
        
        # If data provided, check conditional requirements
        if data and "if" in schema:
            try:
                validate(instance=data, schema=schema["if"])
                # If condition satisfied, add 'then' required fields
                if "then" in schema and "required" in schema["then"]:
                    required = list(set(required + schema["then"]["required"]))
            except JsonSchemaValidationError:
                # If condition not satisfied, add 'else' required fields
                if "else" in schema and "required" in schema["else"]:
                    required = list(set(required + schema["else"]["required"]))
        
        return required



# Example custom validators
def example_custom_validators():
    """
    Example custom validation functions for business logic
    Each validator should return (is_valid: bool, error_message: str)
    """
    
    def validate_loan_amount(value: Any, full_data: Dict) -> Tuple[bool, str]:
        """Ensure loan amount doesn't exceed 5x annual income"""
        annual_income = full_data.get("annual_income", 0)
        if value and annual_income and value > annual_income * 5:
            return False, "Loan amount cannot exceed 5x annual income"
        return True, ""
    
    def validate_end_date_after_start(value: Any, full_data: Dict) -> Tuple[bool, str]:
        """Ensure end_date is after start_date"""
        start_date = full_data.get("start_date")
        if value and start_date and value <= start_date:
            return False, "End date must be after start date"
        return True, ""
    
    return {
        "loan_amount": validate_loan_amount,
        "end_date": validate_end_date_after_start
    }
