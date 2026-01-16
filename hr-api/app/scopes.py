import enum


class HRScopeEnum(str, enum.Enum):
    """HR API OAuth2 Scopes"""

    # Employee scopes
    EMPLOYEES_READ = "employees:read"
    EMPLOYEES_WRITE = "employees:write"
    EMPLOYEES_READ_SENSITIVE = "employees:read:sensitive"  # View salary

    # Department scopes
    DEPARTMENTS_READ = "departments:read"
    DEPARTMENTS_WRITE = "departments:write"
    DEPARTMENTS_MANAGE = "departments:manage"  # View budget, assign managers

    @classmethod
    def all_values(cls):
        """Get all scope values as a list"""
        return [scope.value for scope in cls]

    @classmethod
    def default_scopes(cls):
        """Get default scopes for new client registrations"""
        return [cls.EMPLOYEES_READ.value, cls.DEPARTMENTS_READ.value]

    @classmethod
    def sensitive_scopes(cls):
        """Get scopes that provide access to sensitive information"""
        return [
            cls.EMPLOYEES_READ_SENSITIVE.value,
            cls.DEPARTMENTS_MANAGE.value
        ]
