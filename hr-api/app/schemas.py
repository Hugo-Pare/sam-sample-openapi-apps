from pydantic import BaseModel, EmailStr, Field, validator
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal


# ============================================================================
# OAUTH2 SCHEMAS (RFC 7591 & RFC 8414)
# ============================================================================

class OAuth2ServerMetadata(BaseModel):
    """RFC 8414 Authorization Server Metadata (Discovery)"""
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: Optional[str] = None
    scopes_supported: Optional[List[str]] = None
    response_types_supported: List[str]
    grant_types_supported: Optional[List[str]] = None
    token_endpoint_auth_methods_supported: Optional[List[str]] = None
    service_documentation: Optional[str] = None


class OAuth2ClientRegistrationRequest(BaseModel):
    """RFC 7591 Client Registration Request"""
    redirect_uris: List[str] = Field(..., min_items=1, description="Array of redirect URIs")
    client_name: Optional[str] = Field(None, max_length=100, description="Human-readable client name")
    client_uri: Optional[str] = Field(None, description="URL of client's homepage")
    logo_uri: Optional[str] = Field(None, description="URL of client's logo")
    contacts: Optional[List[EmailStr]] = Field(None, description="Contact emails for client")
    tos_uri: Optional[str] = Field(None, description="URL of Terms of Service")
    policy_uri: Optional[str] = Field(None, description="URL of Privacy Policy")
    grant_types: Optional[List[str]] = Field(
        default=None,
        description="OAuth grant types requested"
    )
    response_types: Optional[List[str]] = Field(
        default=None,
        description="OAuth response types"
    )
    scope: Optional[str] = Field(
        None,
        description="Space-separated list of scopes"
    )
    token_endpoint_auth_method: Optional[str] = Field(
        default=None,
        description="Method of authenticating at token endpoint"
    )


class OAuth2ClientRegistrationResponse(BaseModel):
    """RFC 7591 Client Registration Response"""
    client_id: str = Field(..., description="Unique client identifier")
    client_secret: str = Field(..., description="Client secret (only returned once)")
    client_id_issued_at: int = Field(..., description="Unix timestamp when issued")
    client_secret_expires_at: int = Field(
        default=0,
        description="Unix timestamp when secret expires (0 = never)"
    )
    redirect_uris: List[str]
    client_name: Optional[str] = None
    client_uri: Optional[str] = None
    logo_uri: Optional[str] = None
    contacts: Optional[List[str]] = None
    tos_uri: Optional[str] = None
    policy_uri: Optional[str] = None
    grant_types: List[str]
    response_types: List[str]
    scope: Optional[str] = None
    token_endpoint_auth_method: str
    registration_access_token: Optional[str] = Field(
        None,
        description="Token to access registration management endpoint"
    )


class OAuth2TokenResponse(BaseModel):
    """OAuth2 Token Response"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


# ============================================================================
# DEPARTMENT SCHEMAS
# ============================================================================

class DepartmentBase(BaseModel):
    """Base Department schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=100)


class DepartmentCreate(DepartmentBase):
    """Department creation schema"""
    code: str = Field(..., min_length=1, max_length=20)
    manager_id: Optional[int] = None
    budget: Optional[Decimal] = Field(None, ge=0)


class DepartmentUpdate(BaseModel):
    """Department update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    location: Optional[str] = None
    manager_id: Optional[int] = None
    budget: Optional[Decimal] = Field(None, ge=0)


class DepartmentSummary(BaseModel):
    """Department summary for nested references"""
    id: int
    code: str
    name: str
    location: Optional[str]

    class Config:
        from_attributes = True


class Department(DepartmentBase):
    """Department response (public - no budget)"""
    id: int
    code: str
    manager_id: Optional[int]
    location: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepartmentFull(Department):
    """Department response with budget (requires departments:manage scope)"""
    budget: Optional[Decimal]

    class Config:
        from_attributes = True


# ============================================================================
# EMPLOYEE SCHEMAS
# ============================================================================

class EmployeeBase(BaseModel):
    """Base Employee schema"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    job_title: str = Field(..., min_length=1, max_length=100)
    department_id: int
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    """Employee creation schema"""
    employee_number: str = Field(..., min_length=1, max_length=20)
    hire_date: date
    salary: Decimal = Field(..., gt=0)
    employment_status: str = Field(default="active", pattern="^(active|on_leave|terminated)$")


class EmployeeUpdate(BaseModel):
    """Employee update schema"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    job_title: Optional[str] = None
    department_id: Optional[int] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    employment_status: Optional[str] = Field(None, pattern="^(active|on_leave|terminated)$")
    salary: Optional[Decimal] = Field(None, gt=0)


class EmployeeSummary(BaseModel):
    """Employee summary for nested references"""
    id: int
    employee_number: str
    first_name: str
    last_name: str
    job_title: str
    email: EmailStr

    class Config:
        from_attributes = True


class Employee(EmployeeBase):
    """Employee response (public - no salary)"""
    id: int
    employee_number: str
    hire_date: date
    employment_status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    department: DepartmentSummary

    class Config:
        from_attributes = True


class EmployeeFull(Employee):
    """Employee response with salary (requires employees:read:sensitive scope)"""
    salary: Decimal

    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    """Paginated employee list response"""
    total: int
    page: int
    page_size: int
    employees: List[Employee]


class DepartmentWithEmployees(DepartmentFull):
    """Department with employee list"""
    employees: List[EmployeeSummary] = []

    class Config:
        from_attributes = True


class DepartmentListResponse(BaseModel):
    """Paginated department list response"""
    total: int
    page: int
    page_size: int
    departments: List[Department]


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    """Base User schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8)


class User(UserBase):
    """User response schema"""
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True
