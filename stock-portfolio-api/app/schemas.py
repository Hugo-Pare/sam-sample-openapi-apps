from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


# Stock Schemas
class StockBase(BaseModel):
    symbol: str = Field(..., max_length=10, description="Stock ticker symbol")
    company_name: str = Field(..., max_length=200, description="Company name")
    sector: str = Field(..., max_length=100, description="Business sector")
    current_price: Decimal = Field(..., gt=0, description="Current stock price")


class StockCreate(StockBase):
    pass


class StockUpdate(BaseModel):
    symbol: Optional[str] = Field(None, max_length=10)
    company_name: Optional[str] = Field(None, max_length=200)
    sector: Optional[str] = Field(None, max_length=100)
    current_price: Optional[Decimal] = Field(None, gt=0)


class Stock(StockBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Portfolio Schemas
class PortfolioBase(BaseModel):
    stock_id: int = Field(..., description="ID of the stock")
    shares: int = Field(..., gt=0, description="Number of shares")
    purchase_price: Decimal = Field(..., gt=0, description="Purchase price per share")
    purchase_date: date = Field(..., description="Date of purchase")
    notes: Optional[str] = Field(None, description="Additional notes")


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioUpdate(BaseModel):
    shares: Optional[int] = Field(None, gt=0)
    purchase_price: Optional[Decimal] = Field(None, gt=0)
    purchase_date: Optional[date] = None
    notes: Optional[str] = None


class Portfolio(PortfolioBase):
    id: int
    created_at: datetime
    updated_at: datetime
    stock: Stock

    class Config:
        from_attributes = True


class PortfolioWithMetrics(Portfolio):
    current_value: Decimal
    total_cost: Decimal
    profit_loss: Decimal
    profit_loss_percentage: Decimal


class PortfolioSummary(BaseModel):
    total_holdings: int
    total_invested: Decimal
    current_value: Decimal
    total_profit_loss: Decimal
    profit_loss_percentage: Decimal
