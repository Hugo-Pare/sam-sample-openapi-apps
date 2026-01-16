from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class EmploymentStatusEnum(str, enum.Enum):
    """Employee employment status"""
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


# User/Member model for OAuth2 authentication
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# OAuth2 Client model (Extended for RFC 7591 Dynamic Client Registration)
class OAuth2Client(Base):
    __tablename__ = "oauth2_clients"

    id = Column(Integer, primary_key=True, index=True)

    # Core OAuth2 fields
    client_id = Column(String(100), unique=True, nullable=False, index=True)
    client_secret_hash = Column(String(255), nullable=False)
    client_name = Column(String(100), nullable=False)
    redirect_uris = Column(Text, nullable=False)  # JSON array stored as text
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # RFC 7591 Dynamic Client Registration fields
    client_uri = Column(String(500), nullable=True)
    logo_uri = Column(String(500), nullable=True)
    contacts = Column(Text, nullable=True)  # JSON array of emails
    tos_uri = Column(String(500), nullable=True)
    policy_uri = Column(String(500), nullable=True)

    # OAuth configuration
    grant_types = Column(Text, nullable=False, default='["authorization_code", "refresh_token"]')  # JSON array
    response_types = Column(Text, nullable=False, default='["code"]')  # JSON array
    scope = Column(String(1000), nullable=True)  # Space-separated scopes
    token_endpoint_auth_method = Column(String(50), nullable=False, default="client_secret_post")

    # Registration metadata
    client_id_issued_at = Column(Integer, nullable=False)  # Unix timestamp
    client_secret_expires_at = Column(Integer, nullable=False, default=0)  # 0 = never
    registration_access_token_hash = Column(String(255), nullable=True, index=True)

    # Audit
    registration_ip = Column(String(45), nullable=True)  # IPv6 support


# OAuth2 Authorization Code model
class OAuth2AuthCode(Base):
    __tablename__ = "oauth2_auth_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    client_id = Column(String(100), ForeignKey("oauth2_clients.client_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    redirect_uri = Column(String(500), nullable=False)
    scope = Column(String(500))
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# OAuth2 Access Token model
class OAuth2Token(Base):
    __tablename__ = "oauth2_tokens"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=True, index=True)
    client_id = Column(String(100), ForeignKey("oauth2_clients.client_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scope = Column(String(500))
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Department model
class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    location = Column(String(100))
    budget = Column(Numeric(12, 2))  # Sensitive field - requires departments:manage scope
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    employees = relationship("Employee", back_populates="department", foreign_keys="Employee.department_id")
    manager = relationship("Employee", back_populates="managed_departments", foreign_keys=[manager_id])


# Employee model
class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_number = Column(String(20), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False, index=True)
    last_name = Column(String(50), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    address = Column(Text)

    # Job information
    job_title = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    hire_date = Column(Date, nullable=False)
    employment_status = Column(String(20), nullable=False, default="active")

    # Sensitive information - requires employees:read:sensitive scope
    salary = Column(Numeric(10, 2), nullable=False)

    # System fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = relationship("Department", back_populates="employees", foreign_keys=[department_id])
    managed_departments = relationship("Department", back_populates="manager", foreign_keys="Department.manager_id")
