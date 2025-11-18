from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from datetime import date
import os

from app.database import engine, get_db, Base
from app import models, schemas

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Stock Portfolio API",
    description="A sample API for managing stock portfolios with OpenAPI specification",
    version="1.0.0"
)


# Sample data to populate on startup
SAMPLE_STOCKS = [
    {"symbol": "AAPL", "company_name": "Apple Inc.", "sector": "Technology", "current_price": 178.50},
    {"symbol": "GOOGL", "company_name": "Alphabet Inc.", "sector": "Technology", "current_price": 142.30},
    {"symbol": "MSFT", "company_name": "Microsoft Corporation", "sector": "Technology", "current_price": 378.91},
    {"symbol": "TSLA", "company_name": "Tesla Inc.", "sector": "Automotive", "current_price": 242.84},
    {"symbol": "AMZN", "company_name": "Amazon.com Inc.", "sector": "E-commerce", "current_price": 155.33},
    {"symbol": "NVDA", "company_name": "NVIDIA Corporation", "sector": "Technology", "current_price": 495.22},
    {"symbol": "META", "company_name": "Meta Platforms Inc.", "sector": "Technology", "current_price": 338.80},
    {"symbol": "JPM", "company_name": "JPMorgan Chase & Co.", "sector": "Finance", "current_price": 157.42},
    {"symbol": "JNJ", "company_name": "Johnson & Johnson", "sector": "Healthcare", "current_price": 156.73},
    {"symbol": "V", "company_name": "Visa Inc.", "sector": "Finance", "current_price": 258.12},
    {"symbol": "WMT", "company_name": "Walmart Inc.", "sector": "Retail", "current_price": 165.45},
    {"symbol": "PG", "company_name": "Procter & Gamble Co.", "sector": "Consumer Goods", "current_price": 153.89},
    {"symbol": "DIS", "company_name": "The Walt Disney Company", "sector": "Entertainment", "current_price": 91.25},
    {"symbol": "NFLX", "company_name": "Netflix Inc.", "sector": "Entertainment", "current_price": 445.73},
    {"symbol": "XOM", "company_name": "Exxon Mobil Corporation", "sector": "Energy", "current_price": 102.56},
]

SAMPLE_PORTFOLIO = [
    {"stock_symbol": "AAPL", "shares": 50, "purchase_price": 150.00, "purchase_date": "2023-01-15", "notes": "Long term hold"},
    {"stock_symbol": "GOOGL", "shares": 30, "purchase_price": 120.50, "purchase_date": "2023-03-20", "notes": "Tech diversification"},
    {"stock_symbol": "MSFT", "shares": 25, "purchase_price": 320.00, "purchase_date": "2022-11-10", "notes": "Blue chip investment"},
    {"stock_symbol": "TSLA", "shares": 15, "purchase_price": 200.00, "purchase_date": "2023-06-05", "notes": "Growth potential"},
    {"stock_symbol": "NVDA", "shares": 20, "purchase_price": 400.00, "purchase_date": "2023-02-28", "notes": "AI exposure"},
]


@app.on_event("startup")
async def startup_event():
    """Load sample data on startup if database is empty"""
    db = next(get_db())
    try:
        # Check if stocks already exist
        existing_stocks = db.query(models.Stock).count()
        if existing_stocks == 0:
            # Add sample stocks
            for stock_data in SAMPLE_STOCKS:
                stock = models.Stock(**stock_data)
                db.add(stock)
            db.commit()
            
            # Add sample portfolio holdings
            for holding_data in SAMPLE_PORTFOLIO:
                stock_symbol = holding_data.pop("stock_symbol")
                stock = db.query(models.Stock).filter(models.Stock.symbol == stock_symbol).first()
                if stock:
                    holding = models.Portfolio(
                        stock_id=stock.id,
                        shares=holding_data["shares"],
                        purchase_price=holding_data["purchase_price"],
                        purchase_date=date.fromisoformat(holding_data["purchase_date"]),
                        notes=holding_data.get("notes")
                    )
                    db.add(holding)
            db.commit()
    finally:
        db.close()


# Root endpoint
@app.get("/", tags=["General"])
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "Stock Portfolio API",
        "version": "1.0.0",
        "documentation": "/docs",
        "openapi_spec": "/openapi.json"
    }


# Health check endpoint
@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Stock endpoints
@app.get("/stocks", response_model=List[schemas.Stock], tags=["Stocks"])
def get_stocks(
    skip: int = 0,
    limit: int = 100,
    sector: str = None,
    db: Session = Depends(get_db)
):
    """Get all stocks with optional filtering by sector"""
    query = db.query(models.Stock)
    if sector:
        query = query.filter(models.Stock.sector == sector)
    stocks = query.offset(skip).limit(limit).all()
    return stocks


@app.get("/stocks/{stock_id}", response_model=schemas.Stock, tags=["Stocks"])
def get_stock(stock_id: int, db: Session = Depends(get_db)):
    """Get a specific stock by ID"""
    stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock


@app.get("/stocks/symbol/{symbol}", response_model=schemas.Stock, tags=["Stocks"])
def get_stock_by_symbol(symbol: str, db: Session = Depends(get_db)):
    """Get a stock by its symbol"""
    stock = db.query(models.Stock).filter(models.Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock


@app.post("/stocks", response_model=schemas.Stock, status_code=status.HTTP_201_CREATED, tags=["Stocks"])
def create_stock(stock: schemas.StockCreate, db: Session = Depends(get_db)):
    """Create a new stock"""
    # Check if stock with symbol already exists
    existing_stock = db.query(models.Stock).filter(models.Stock.symbol == stock.symbol.upper()).first()
    if existing_stock:
        raise HTTPException(status_code=400, detail="Stock with this symbol already exists")
    
    db_stock = models.Stock(**stock.dict())
    db_stock.symbol = db_stock.symbol.upper()
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock


@app.put("/stocks/{stock_id}", response_model=schemas.Stock, tags=["Stocks"])
def update_stock(stock_id: int, stock: schemas.StockUpdate, db: Session = Depends(get_db)):
    """Update a stock"""
    db_stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not db_stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    update_data = stock.dict(exclude_unset=True)
    if "symbol" in update_data:
        update_data["symbol"] = update_data["symbol"].upper()
        # Check if new symbol conflicts with existing stock
        existing = db.query(models.Stock).filter(
            models.Stock.symbol == update_data["symbol"],
            models.Stock.id != stock_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Stock with this symbol already exists")
    
    for field, value in update_data.items():
        setattr(db_stock, field, value)
    
    db.commit()
    db.refresh(db_stock)
    return db_stock


@app.delete("/stocks/{stock_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Stocks"])
def delete_stock(stock_id: int, db: Session = Depends(get_db)):
    """Delete a stock"""
    db_stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not db_stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    db.delete(db_stock)
    db.commit()
    return None


# Portfolio endpoints
@app.get("/portfolio", response_model=List[schemas.PortfolioWithMetrics], tags=["Portfolio"])
def get_portfolio(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all portfolio holdings with calculated metrics"""
    holdings = db.query(models.Portfolio).offset(skip).limit(limit).all()
    
    result = []
    for holding in holdings:
        current_value = holding.stock.current_price * holding.shares
        total_cost = holding.purchase_price * holding.shares
        profit_loss = current_value - total_cost
        profit_loss_pct = (profit_loss / total_cost * 100) if total_cost > 0 else Decimal(0)
        
        holding_dict = {
            "id": holding.id,
            "stock_id": holding.stock_id,
            "shares": holding.shares,
            "purchase_price": holding.purchase_price,
            "purchase_date": holding.purchase_date,
            "notes": holding.notes,
            "created_at": holding.created_at,
            "updated_at": holding.updated_at,
            "stock": holding.stock,
            "current_value": current_value,
            "total_cost": total_cost,
            "profit_loss": profit_loss,
            "profit_loss_percentage": profit_loss_pct
        }
        result.append(holding_dict)
    
    return result


@app.get("/portfolio/{holding_id}", response_model=schemas.PortfolioWithMetrics, tags=["Portfolio"])
def get_portfolio_holding(holding_id: int, db: Session = Depends(get_db)):
    """Get a specific portfolio holding with metrics"""
    holding = db.query(models.Portfolio).filter(models.Portfolio.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Portfolio holding not found")
    
    current_value = holding.stock.current_price * holding.shares
    total_cost = holding.purchase_price * holding.shares
    profit_loss = current_value - total_cost
    profit_loss_pct = (profit_loss / total_cost * 100) if total_cost > 0 else Decimal(0)
    
    return {
        "id": holding.id,
        "stock_id": holding.stock_id,
        "shares": holding.shares,
        "purchase_price": holding.purchase_price,
        "purchase_date": holding.purchase_date,
        "notes": holding.notes,
        "created_at": holding.created_at,
        "updated_at": holding.updated_at,
        "stock": holding.stock,
        "current_value": current_value,
        "total_cost": total_cost,
        "profit_loss": profit_loss,
        "profit_loss_percentage": profit_loss_pct
    }


@app.post("/portfolio", response_model=schemas.Portfolio, status_code=status.HTTP_201_CREATED, tags=["Portfolio"])
def create_portfolio_holding(holding: schemas.PortfolioCreate, db: Session = Depends(get_db)):
    """Add a stock to portfolio"""
    # Verify stock exists
    stock = db.query(models.Stock).filter(models.Stock.id == holding.stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    db_holding = models.Portfolio(**holding.dict())
    db.add(db_holding)
    db.commit()
    db.refresh(db_holding)
    return db_holding


@app.put("/portfolio/{holding_id}", response_model=schemas.Portfolio, tags=["Portfolio"])
def update_portfolio_holding(holding_id: int, holding: schemas.PortfolioUpdate, db: Session = Depends(get_db)):
    """Update a portfolio holding"""
    db_holding = db.query(models.Portfolio).filter(models.Portfolio.id == holding_id).first()
    if not db_holding:
        raise HTTPException(status_code=404, detail="Portfolio holding not found")
    
    update_data = holding.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_holding, field, value)
    
    db.commit()
    db.refresh(db_holding)
    return db_holding


@app.delete("/portfolio/{holding_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Portfolio"])
def delete_portfolio_holding(holding_id: int, db: Session = Depends(get_db)):
    """Remove a holding from portfolio"""
    db_holding = db.query(models.Portfolio).filter(models.Portfolio.id == holding_id).first()
    if not db_holding:
        raise HTTPException(status_code=404, detail="Portfolio holding not found")
    
    db.delete(db_holding)
    db.commit()
    return None


@app.get("/portfolio/summary/total", response_model=schemas.PortfolioSummary, tags=["Portfolio"])
def get_portfolio_summary(db: Session = Depends(get_db)):
    """Get portfolio summary with total metrics"""
    holdings = db.query(models.Portfolio).all()
    
    if not holdings:
        return {
            "total_holdings": 0,
            "total_invested": Decimal(0),
            "current_value": Decimal(0),
            "total_profit_loss": Decimal(0),
            "profit_loss_percentage": Decimal(0)
        }
    
    total_invested = Decimal(0)
    current_value = Decimal(0)
    
    for holding in holdings:
        total_invested += holding.purchase_price * holding.shares
        current_value += holding.stock.current_price * holding.shares
    
    total_profit_loss = current_value - total_invested
    profit_loss_pct = (total_profit_loss / total_invested * 100) if total_invested > 0 else Decimal(0)
    
    return {
        "total_holdings": len(holdings),
        "total_invested": total_invested,
        "current_value": current_value,
        "total_profit_loss": total_profit_loss,
        "profit_loss_percentage": profit_loss_pct
    }


# Run with: uvicorn app.main:app --reload --port <PORT>
# Default port is 8000, or set PORT environment variable
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
