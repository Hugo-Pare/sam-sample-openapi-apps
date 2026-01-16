from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, timedelta
import os

from app.database import get_db, engine, Base
from app import models, schemas, oauth2
from app.scopes import HRScopeEnum

# Create all database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="HR Management API",
    description="OAuth2-only HR API with RFC 8414 Discovery and RFC 7591 Dynamic Client Registration",
    version="1.0.0"
)


# ============================================================================
# STARTUP EVENT - LOAD SAMPLE DATA
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Load sample data on startup if database is empty"""
    db = next(get_db())
    try:
        existing_depts = db.query(models.Department).count()
        if existing_depts == 0:
            print("\n" + "="*80)
            print("LOADING SAMPLE HR DATA...")
            print("="*80)

            # Create departments first
            departments_data = [
                {"code": "ENG", "name": "Engineering", "description": "Software development and engineering", "location": "San Francisco, CA", "budget": 5000000.00},
                {"code": "SALES", "name": "Sales", "description": "Enterprise and SMB sales", "location": "Austin, TX", "budget": 3000000.00},
                {"code": "HR", "name": "Human Resources", "description": "Employee relations and recruitment", "location": "New York, NY", "budget": 1500000.00},
                {"code": "FIN", "name": "Finance", "description": "Accounting and financial planning", "location": "New York, NY", "budget": 1200000.00},
                {"code": "OPS", "name": "Operations", "description": "Business operations and support", "location": "Chicago, IL", "budget": 2000000.00},
            ]

            dept_map = {}
            for dept_data in departments_data:
                department = models.Department(**dept_data)
                db.add(department)
                db.flush()
                dept_map[dept_data["code"]] = department.id

            db.commit()
            print(f"✓ Created {len(departments_data)} departments")

            # Create users
            users_data = [
                {"username": "admin", "password": "admin123", "email": "admin@company.com", "full_name": "Admin User", "is_admin": True},
                {"username": "sarah.johnson", "password": "password123", "email": "sarah.johnson@company.com", "full_name": "Sarah Johnson", "is_admin": False},
                {"username": "michael.chen", "password": "password123", "email": "michael.chen@company.com", "full_name": "Michael Chen", "is_admin": False},
            ]

            for user_data in users_data:
                password = user_data.pop("password")
                user = models.User(
                    **user_data,
                    hashed_password=oauth2.hash_password(password),
                    is_active=True
                )
                db.add(user)

            db.commit()
            print(f"✓ Created {len(users_data)} users")

            # Create employees
            employees_data = [
                {"employee_number": "EMP001", "first_name": "Sarah", "last_name": "Johnson", "email": "sarah.johnson@company.com",
                 "job_title": "VP of Engineering", "department": "ENG", "hire_date": "2020-01-15", "salary": 180000.00,
                 "phone": "+1-415-555-0101", "address": "123 Market St, San Francisco, CA 94105"},
                {"employee_number": "EMP002", "first_name": "Michael", "last_name": "Chen", "email": "michael.chen@company.com",
                 "job_title": "Senior Software Engineer", "department": "ENG", "hire_date": "2021-03-20", "salary": 145000.00,
                 "phone": "+1-415-555-0102", "address": "456 Valencia St, San Francisco, CA 94110"},
                {"employee_number": "EMP003", "first_name": "Emily", "last_name": "Rodriguez", "email": "emily.rodriguez@company.com",
                 "job_title": "HR Manager", "department": "HR", "hire_date": "2019-06-10", "salary": 95000.00,
                 "phone": "+1-212-555-0201", "address": "789 Broadway, New York, NY 10003"},
                {"employee_number": "EMP004", "first_name": "David", "last_name": "Kim", "email": "david.kim@company.com",
                 "job_title": "Sales Director", "department": "SALES", "hire_date": "2020-09-01", "salary": 125000.00,
                 "phone": "+1-512-555-0301", "address": "321 Congress Ave, Austin, TX 78701"},
                {"employee_number": "EMP005", "first_name": "Jennifer", "last_name": "White", "email": "jennifer.white@company.com",
                 "job_title": "Senior Accountant", "department": "FIN", "hire_date": "2021-02-14", "salary": 85000.00,
                 "phone": "+1-212-555-0401", "address": "555 Park Ave, New York, NY 10021"},
                {"employee_number": "EMP006", "first_name": "Robert", "last_name": "Davis", "email": "robert.davis@company.com",
                 "job_title": "Financial Controller", "department": "FIN", "hire_date": "2018-11-05", "salary": 135000.00,
                 "phone": "+1-212-555-0501", "address": "900 Park Ave, New York, NY 10021"},
                {"employee_number": "EMP007", "first_name": "Lisa", "last_name": "Thompson", "email": "lisa.thompson@company.com",
                 "job_title": "Software Engineer", "department": "ENG", "hire_date": "2022-01-10", "salary": 120000.00,
                 "phone": "+1-415-555-0103", "address": "234 Howard St, San Francisco, CA 94105"},
                {"employee_number": "EMP008", "first_name": "James", "last_name": "Wilson", "email": "james.wilson@company.com",
                 "job_title": "Operations Manager", "department": "OPS", "hire_date": "2021-07-15", "salary": 105000.00,
                 "phone": "+1-312-555-0601", "address": "567 Michigan Ave, Chicago, IL 60611"},
            ]

            employee_map = {}
            for emp_data in employees_data:
                dept_code = emp_data.pop("department")
                hire_date_str = emp_data.pop("hire_date")
                emp_data["hire_date"] = date.fromisoformat(hire_date_str)
                emp_data["department_id"] = dept_map[dept_code]
                emp_data["employment_status"] = "active"

                employee = models.Employee(**emp_data)
                db.add(employee)
                db.flush()
                employee_map[emp_data["employee_number"]] = employee.id

            db.commit()
            print(f"✓ Created {len(employees_data)} employees")

            # Assign department managers
            dept_updates = [
                ("ENG", "EMP001"),  # Sarah Johnson
                ("HR", "EMP003"),   # Emily Rodriguez
                ("SALES", "EMP004"), # David Kim
                ("FIN", "EMP006"),   # Robert Davis
                ("OPS", "EMP008"),   # James Wilson
            ]

            for dept_code, emp_num in dept_updates:
                dept = db.query(models.Department).filter_by(code=dept_code).first()
                if dept and emp_num in employee_map:
                    dept.manager_id = employee_map[emp_num]

            db.commit()
            print(f"✓ Assigned department managers")

            print("\n" + "="*80)
            print("🎉 SAMPLE DATA LOADED SUCCESSFULLY!")
            print("="*80)
            print("\n🔐 OAuth2 Client Registration:")
            print(f"  Discovery: GET http://localhost:{os.getenv('PORT', '8005')}/.well-known/oauth-authorization-server")
            print(f"  Register:  POST http://localhost:{os.getenv('PORT', '8005')}/oauth/register")
            print("\n👤 Test Users:")
            print("  Admin:  username=admin, password=admin123")
            print("  User 1: username=sarah.johnson, password=password123")
            print("  User 2: username=michael.chen, password=password123")
            print("\n📊 Sample Data:")
            print(f"  - {len(departments_data)} Departments")
            print(f"  - {len(employees_data)} Employees")
            print(f"  - {len(users_data)} Users")
            print("\n" + "="*80 + "\n")
    finally:
        db.close()


# ============================================================================
# PUBLIC ENDPOINTS
# ============================================================================

@app.get("/", tags=["Public"])
def root():
    """API information"""
    return {
        "message": "HR Management API",
        "version": "1.0.0",
        "authentication": "OAuth2 only (authorization code flow with refresh tokens)",
        "discovery": "/.well-known/oauth-authorization-server",
        "registration": "/oauth/register",
        "documentation": "/docs",
        "openapi_spec": "/openapi.json"
    }


@app.get("/health", tags=["Public"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# ============================================================================
# RFC 8414: OAUTH2 DISCOVERY ENDPOINT
# ============================================================================

@app.get("/.well-known/oauth-authorization-server", tags=["OAuth2 Discovery"])
def oauth_server_metadata(request: Request):
    """
    RFC 8414 Authorization Server Metadata endpoint.
    Returns OAuth2 server configuration and capabilities.
    """
    base_url = str(request.base_url).rstrip('/')
    return oauth2.get_server_metadata(base_url)


# ============================================================================
# RFC 7591: DYNAMIC CLIENT REGISTRATION
# ============================================================================

@app.post("/oauth/register", response_model=schemas.OAuth2ClientRegistrationResponse,
          status_code=status.HTTP_201_CREATED, tags=["OAuth2 Registration"])
def register_client(
    registration_data: schemas.OAuth2ClientRegistrationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    RFC 7591 Dynamic Client Registration endpoint.
    Allows clients to self-register with the authorization server.
    """
    # Get client IP for audit logging
    client_ip = request.client.host

    # Register the client
    db_client, client_secret, registration_access_token = oauth2.register_oauth2_client(
        client_name=registration_data.client_name,
        redirect_uris=registration_data.redirect_uris,
        client_uri=registration_data.client_uri,
        logo_uri=registration_data.logo_uri,
        contacts=registration_data.contacts,
        tos_uri=registration_data.tos_uri,
        policy_uri=registration_data.policy_uri,
        grant_types=registration_data.grant_types,
        response_types=registration_data.response_types,
        scope=registration_data.scope,
        token_endpoint_auth_method=registration_data.token_endpoint_auth_method,
        request_ip=client_ip,
        db=db
    )

    # Build response
    import json
    return schemas.OAuth2ClientRegistrationResponse(
        client_id=db_client.client_id,
        client_secret=client_secret,  # Only returned once!
        client_id_issued_at=db_client.client_id_issued_at,
        client_secret_expires_at=db_client.client_secret_expires_at,
        redirect_uris=json.loads(db_client.redirect_uris),
        client_name=db_client.client_name,
        client_uri=db_client.client_uri,
        logo_uri=db_client.logo_uri,
        contacts=json.loads(db_client.contacts) if db_client.contacts else None,
        tos_uri=db_client.tos_uri,
        policy_uri=db_client.policy_uri,
        grant_types=json.loads(db_client.grant_types),
        response_types=json.loads(db_client.response_types),
        scope=db_client.scope,
        token_endpoint_auth_method=db_client.token_endpoint_auth_method,
        registration_access_token=registration_access_token
    )


# ============================================================================
# OAUTH2 AUTHORIZATION FLOW
# ============================================================================

@app.get("/oauth/authorize", response_class=HTMLResponse, tags=["OAuth2 Flow"])
def oauth_authorize_get(
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    OAuth2 authorization endpoint (Step 1: Show login form).
    Displays an HTML login form for user authentication.
    """
    # Validate client
    client = db.query(models.OAuth2Client).filter(
        models.OAuth2Client.client_id == client_id,
        models.OAuth2Client.is_active == True
    ).first()

    if not client:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    # Validate redirect URI
    if not oauth2.validate_redirect_uri(client, redirect_uri):
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")

    # Validate response type
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Unsupported response_type")

    # Display login form
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>HR API - Login</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }}
            h2 {{ color: #333; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }}
            button {{ width: 100%; padding: 10px; background-color: #007bff; color: white; border: none;
                      border-radius: 4px; cursor: pointer; font-size: 16px; }}
            button:hover {{ background-color: #0056b3; }}
            .info {{ background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h2>🔐 HR API Login</h2>
        <div class="info">
            <strong>Client:</strong> {client.client_name}<br>
            <strong>Requested scopes:</strong> {scope or "default"}
        </div>
        <form method="post" action="/oauth/authorize">
            <input type="hidden" name="client_id" value="{client_id}">
            <input type="hidden" name="redirect_uri" value="{redirect_uri}">
            <input type="hidden" name="response_type" value="{response_type}">
            <input type="hidden" name="scope" value="{scope or ''}">
            <input type="hidden" name="state" value="{state or ''}">

            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>

            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>

            <button type="submit">Authorize</button>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/oauth/authorize", tags=["OAuth2 Flow"])
def oauth_authorize_post(
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    response_type: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    scope: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    OAuth2 authorization endpoint (Step 2: Process login).
    Validates credentials and redirects with authorization code.
    """
    # Validate client
    client = db.query(models.OAuth2Client).filter(
        models.OAuth2Client.client_id == client_id,
        models.OAuth2Client.is_active == True
    ).first()

    if not client:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    # Validate redirect URI
    if not oauth2.validate_redirect_uri(client, redirect_uri):
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")

    # Authenticate user
    user = db.query(models.User).filter(
        models.User.username == username,
        models.User.is_active == True
    ).first()

    if not user or not oauth2.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create authorization code
    code = oauth2.create_authorization_code(
        client_id=client_id,
        user_id=user.id,
        redirect_uri=redirect_uri,
        scope=scope,
        db=db
    )

    # Build redirect URL with code
    redirect_url = f"{redirect_uri}?code={code}"
    if state:
        redirect_url += f"&state={state}"

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@app.post("/oauth/token", response_model=schemas.OAuth2TokenResponse, tags=["OAuth2 Flow"])
def oauth_token(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    refresh_token: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    OAuth2 token endpoint.
    Exchanges authorization code for access token or refreshes access token.
    """
    # Validate client credentials
    client = oauth2.validate_client(client_id, client_secret, db)

    if grant_type == "authorization_code":
        # Exchange code for token
        if not code or not redirect_uri:
            raise HTTPException(status_code=400, detail="code and redirect_uri required")

        return oauth2.exchange_code_for_token(code, client_id, redirect_uri, db)

    elif grant_type == "refresh_token":
        # Refresh access token
        if not refresh_token:
            raise HTTPException(status_code=400, detail="refresh_token required")

        return oauth2.refresh_access_token(refresh_token, client_id, db)

    else:
        raise HTTPException(status_code=400, detail="Unsupported grant_type")


# ============================================================================
# DEPARTMENT ENDPOINTS
# ============================================================================

@app.get("/departments", response_model=List[schemas.Department], tags=["Departments"])
def list_departments(
    include_inactive: bool = False,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all departments (public endpoint).
    Returns basic department information without budget.
    """
    query = db.query(models.Department)

    if not include_inactive:
        query = query.filter(models.Department.is_active == True)

    if location:
        query = query.filter(models.Department.location.ilike(f"%{location}%"))

    departments = query.all()
    return departments


@app.get("/departments/{department_id}", tags=["Departments"])
def get_department(
    department_id: int,
    current_user: models.User = Depends(oauth2.require_scope(HRScopeEnum.DEPARTMENTS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Get department details.
    Budget field only visible with departments:manage scope.
    """
    department = db.query(models.Department).filter(
        models.Department.id == department_id
    ).first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # Check if user has manage scope to see budget
    has_manage = oauth2.has_scope(current_user, HRScopeEnum.DEPARTMENTS_MANAGE.value)

    if has_manage:
        return schemas.DepartmentFull.from_orm(department)
    else:
        return schemas.Department.from_orm(department)


@app.post("/departments", response_model=schemas.DepartmentFull,
          status_code=status.HTTP_201_CREATED, tags=["Departments"])
def create_department(
    department: schemas.DepartmentCreate,
    current_user: models.User = Depends(oauth2.require_scope(HRScopeEnum.DEPARTMENTS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Create a new department.
    Requires departments:write scope.
    """
    # Check for duplicate code or name
    existing = db.query(models.Department).filter(
        (models.Department.code == department.code) |
        (models.Department.name == department.name)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Department code or name already exists")

    # Validate manager if provided
    if department.manager_id:
        manager = db.query(models.Employee).filter(
            models.Employee.id == department.manager_id
        ).first()
        if not manager:
            raise HTTPException(status_code=400, detail="Manager not found")

    db_department = models.Department(**department.dict())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)

    return db_department


@app.patch("/departments/{department_id}", response_model=schemas.DepartmentFull, tags=["Departments"])
def update_department(
    department_id: int,
    department_update: schemas.DepartmentUpdate,
    current_user: models.User = Depends(oauth2.require_scope(HRScopeEnum.DEPARTMENTS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Update department information.
    Requires departments:write scope.
    Updating budget or manager requires departments:manage scope.
    """
    db_department = db.query(models.Department).filter(
        models.Department.id == department_id
    ).first()

    if not db_department:
        raise HTTPException(status_code=404, detail="Department not found")

    # Check if updating budget or manager (requires manage scope)
    if (department_update.budget is not None or department_update.manager_id is not None):
        if not oauth2.has_scope(current_user, HRScopeEnum.DEPARTMENTS_MANAGE.value):
            raise HTTPException(
                status_code=403,
                detail="departments:manage scope required to update budget or manager"
            )

    # Validate manager if being changed
    if department_update.manager_id:
        manager = db.query(models.Employee).filter(
            models.Employee.id == department_update.manager_id
        ).first()
        if not manager:
            raise HTTPException(status_code=400, detail="Manager not found")

    # Update fields
    update_data = department_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_department, field, value)

    db.commit()
    db.refresh(db_department)

    return db_department


@app.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Departments"])
def delete_department(
    department_id: int,
    current_user: models.User = Depends(oauth2.require_scope(HRScopeEnum.DEPARTMENTS_MANAGE.value)),
    db: Session = Depends(get_db)
):
    """
    Soft delete department (sets is_active=False).
    Requires departments:manage scope.
    Cannot delete department with active employees.
    """
    db_department = db.query(models.Department).filter(
        models.Department.id == department_id
    ).first()

    if not db_department:
        raise HTTPException(status_code=404, detail="Department not found")

    # Check for active employees
    active_employees = db.query(models.Employee).filter(
        models.Employee.department_id == department_id,
        models.Employee.is_active == True
    ).count()

    if active_employees > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete department with {active_employees} active employees"
        )

    db_department.is_active = False
    db.commit()


@app.get("/departments/{department_id}/employees", response_model=List[schemas.EmployeeSummary], tags=["Departments"])
def list_department_employees(
    department_id: int,
    current_user: models.User = Depends(oauth2.require_scope(
        HRScopeEnum.DEPARTMENTS_READ.value,
        HRScopeEnum.EMPLOYEES_READ.value
    )),
    db: Session = Depends(get_db)
):
    """
    List all employees in a department.
    Requires both departments:read and employees:read scopes.
    """
    department = db.query(models.Department).filter(
        models.Department.id == department_id
    ).first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    employees = db.query(models.Employee).filter(
        models.Employee.department_id == department_id,
        models.Employee.is_active == True
    ).all()

    return employees


# ============================================================================
# EMPLOYEE ENDPOINTS
# ============================================================================

@app.get("/employees", response_model=List[schemas.Employee], tags=["Employees"])
def list_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    department_id: Optional[int] = None,
    employment_status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: models.User = Depends(oauth2.require_scope(HRScopeEnum.EMPLOYEES_READ.value)),
    db: Session = Depends(get_db)
):
    """
    List employees with pagination and filtering.
    Requires employees:read scope.
    Salary information not included (requires employees:read:sensitive).
    """
    query = db.query(models.Employee).filter(models.Employee.is_active == True)

    if department_id:
        query = query.filter(models.Employee.department_id == department_id)

    if employment_status:
        query = query.filter(models.Employee.employment_status == employment_status)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (models.Employee.first_name.ilike(search_filter)) |
            (models.Employee.last_name.ilike(search_filter)) |
            (models.Employee.email.ilike(search_filter)) |
            (models.Employee.employee_number.ilike(search_filter))
        )

    # Pagination
    offset = (page - 1) * page_size
    employees = query.offset(offset).limit(page_size).all()

    return employees


@app.get("/employees/{employee_id}", tags=["Employees"])
def get_employee(
    employee_id: int,
    current_user: models.User = Depends(oauth2.require_scope(HRScopeEnum.EMPLOYEES_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Get employee details.
    Salary field only visible with employees:read:sensitive scope.
    """
    employee = db.query(models.Employee).filter(
        models.Employee.id == employee_id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Check if user has sensitive scope to see salary
    has_sensitive = oauth2.has_scope(current_user, HRScopeEnum.EMPLOYEES_READ_SENSITIVE.value)

    if has_sensitive:
        return schemas.EmployeeFull.from_orm(employee)
    else:
        return schemas.Employee.from_orm(employee)


@app.post("/employees", response_model=schemas.EmployeeFull,
          status_code=status.HTTP_201_CREATED, tags=["Employees"])
def create_employee(
    employee: schemas.EmployeeCreate,
    current_user: models.User = Depends(oauth2.require_scope(HRScopeEnum.EMPLOYEES_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Create a new employee.
    Requires employees:write scope.
    """
    # Check for duplicate employee_number or email
    existing = db.query(models.Employee).filter(
        (models.Employee.employee_number == employee.employee_number) |
        (models.Employee.email == employee.email)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Employee number or email already exists")

    # Validate department exists
    department = db.query(models.Department).filter(
        models.Department.id == employee.department_id
    ).first()

    if not department:
        raise HTTPException(status_code=400, detail="Department not found")

    db_employee = models.Employee(**employee.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)

    return db_employee


@app.patch("/employees/{employee_id}", response_model=schemas.EmployeeFull, tags=["Employees"])
def update_employee(
    employee_id: int,
    employee_update: schemas.EmployeeUpdate,
    current_user: models.User = Depends(oauth2.require_scope(HRScopeEnum.EMPLOYEES_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Update employee information.
    Requires employees:write scope.
    Updating salary requires employees:read:sensitive scope as well.
    """
    db_employee = db.query(models.Employee).filter(
        models.Employee.id == employee_id
    ).first()

    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Check if updating salary (requires sensitive scope)
    if employee_update.salary is not None:
        if not oauth2.has_scope(current_user, HRScopeEnum.EMPLOYEES_READ_SENSITIVE.value):
            raise HTTPException(
                status_code=403,
                detail="employees:read:sensitive scope required to update salary"
            )

    # Validate department if being changed
    if employee_update.department_id:
        department = db.query(models.Department).filter(
            models.Department.id == employee_update.department_id
        ).first()
        if not department:
            raise HTTPException(status_code=400, detail="Department not found")

    # Update fields
    update_data = employee_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_employee, field, value)

    db.commit()
    db.refresh(db_employee)

    return db_employee


@app.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Employees"])
def delete_employee(
    employee_id: int,
    current_user: models.User = Depends(oauth2.require_scope(HRScopeEnum.EMPLOYEES_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Soft delete employee (sets is_active=False).
    Requires employees:write scope.
    """
    db_employee = db.query(models.Employee).filter(
        models.Employee.id == employee_id
    ).first()

    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    db_employee.is_active = False
    db.commit()


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)
