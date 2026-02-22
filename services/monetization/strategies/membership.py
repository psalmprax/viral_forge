import logging
import random
from typing import List, Dict, Any
from .base import BaseMonetizationStrategy
from api.utils.database import SessionLocal
from api.utils.models import SystemSettings

class MembershipStrategy(BaseMonetizationStrategy):
    """
    Patreon/Membership strategy - Recurring revenue through supporter tiers
    """
    
    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        """
        Fetches membership tiers from database configuration.
        Returns available membership programs for the given niche.
        """
        db = SessionLocal()
        try:
            # Check for configured membership platform URL
            setting = db.query(SystemSettings).filter(
                SystemSettings.key == "membership_platform_url"
            ).first()
            
            platform_url = setting.value if setting else None
            
            if not platform_url:
                logging.warning(f"[MembershipStrategy] No membership platform configured. Set 'membership_platform_url' in settings.")
                return []
            
            # Return membership tiers as assets
            return [
                {
                    "id": "tier_1",
                    "name": "Supporter",
                    "url": platform_url,
                    "price": "$5",
                    "perk": "Early access & behind the scenes",
                    "source": "membership"
                },
                {
                    "id": "tier_2", 
                    "name": "Premium Supporter",
                    "url": platform_url,
                    "price": "$15",
                    "perk": "All perks + exclusive content",
                    "source": "membership"
                },
                {
                    "id": "tier_3",
                    "name": "VIP Member",
                    "url": platform_url,
                    "price": "$50",
                    "perk": "1-on-1 coaching + all perks",
                    "source": "membership"
                }
            ]
        finally:
            db.close()

    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generates a call to action for membership/support.
        """
        assets = await self.get_assets(niche)
        
        if not assets:
            logging.warning(f"[MembershipStrategy] No membership platform configured. Set 'membership_platform_url' in settings.")
            return ""
        
        platform_url = assets[0].get("url", "")
        
        options = [
            f"Support my work! Join the inner circle: \n🔗 {platform_url}",
            f"Want exclusive content and early access? Become a supporter: \n🔗 {platform_url}",
            f"Help me keep creating! Join my membership program: \n🔗 {platform_url}",
            f"Support the channel! Get perks and exclusive content: \n🔗 {platform_url}"
        ]
        return random.choice(options)
