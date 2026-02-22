"""
Billing API Routes for ettametta
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from api.utils.user_models import UserDB
from api.routes.auth import get_current_user
from api.utils.database import SessionLocal
from api.config import settings

router = APIRouter(prefix="/billing", tags=["Billing"])


class CreateCheckoutRequest(BaseModel):
    tier: str  # "creator" or "empire"


class SubscriptionResponse(BaseModel):
    tier: str
    status: str
    current_period_end: Optional[str] = None


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: UserDB = Depends(get_current_user)
):
    """Create a Stripe checkout session for subscription"""
    from services.payment.stripe_service import get_payment_service, SUBSCRIPTION_TIERS
    
    # Validate tier
    if request.tier not in SUBSCRIPTION_TIERS:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    tier_info = SUBSCRIPTION_TIERS[request.tier]
    if not tier_info.get("price_id"):
        raise HTTPException(status_code=400, detail="Tier not available for purchase")
    
    # Get or create Stripe customer
    db = SessionLocal()
    try:
        # Check if user has stripe_customer_id
        stripe_customer_id = getattr(current_user, 'stripe_customer_id', None)
        
        if not stripe_customer_id:
            # Create Stripe customer
            payment_service = get_payment_service()
            customer = await payment_service.create_customer(
                email=current_user.email,
                user_id=current_user.id
            )
            stripe_customer_id = customer["stripe_customer_id"]
            
            # TODO: Save stripe_customer_id to user record
            # current_user.stripe_customer_id = stripe_customer_id
            # db.commit()
        
        # Create checkout session
        payment_service = get_payment_service()
        result = await payment_service.create_subscription(
            stripe_customer_id=stripe_customer_id,
            tier=request.tier
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")
    finally:
        db.close()


@router.get("/subscription")
async def get_subscription(current_user: UserDB = Depends(get_current_user)):
    """Get current user's subscription status"""
    # TODO: Implement - query user's subscription from DB
    return {
        "tier": "free",
        "status": "active",
        "features": SUBSCRIPTION_TIERS["free"]["features"]
    }


@router.post("/cancel")
async def cancel_subscription(current_user: UserDB = Depends(get_current_user)):
    """Cancel current subscription"""
    # TODO: Implement - cancel Stripe subscription
    raise HTTPException(status_code=501, detail="Subscription cancellation not yet implemented")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    from services.payment.stripe_service import get_payment_service
    
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe webhook not configured")
    
    try:
        payment_service = get_payment_service()
        result = await payment_service.handle_webhook(
            payload=payload,
            signature=signature,
            webhook_secret=settings.STRIPE_WEBHOOK_SECRET
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")
