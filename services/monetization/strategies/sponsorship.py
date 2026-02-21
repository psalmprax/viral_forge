import logging
import random
from typing import List, Dict, Any
from .base import BaseMonetizationStrategy
from api.utils.database import SessionLocal
from api.utils.models import SystemSettings

class SponsorshipStrategy(BaseMonetizationStrategy):
    """
    Sponsorship strategy - Brand deals and sponsored content
    """
    
    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        """
        Fetches sponsorship deals from database configuration.
        Returns available brand sponsorships for the given niche.
        """
        db = SessionLocal()
        try:
            # Check for configured sponsorship info
            setting = db.query(SystemSettings).filter(
                SystemSettings.key == "sponsorship_contact"
            ).first()
            
            contact_email = setting.value if setting else "sponsors@ettametta.ai"
            
            # Check for brand partners
            brands_setting = db.query(SystemSettings).filter(
                SystemSettings.key == "brand_partners"
            ).first()
            
            brand_partners = brands_setting.value.split(",") if brands_setting and brands_setting.value else []
            
            if not brand_partners:
                logging.warning(f"[SponsorshipStrategy] No brand partners configured. Set 'brand_partners' in settings.")
                return []
            
            # Return brand partnerships as assets
            assets = []
            for i, brand in enumerate(brand_partners[:5], 1):  # Limit to 5 brands
                assets.append({
                    "id": f"sponsor_{i}",
                    "name": brand.strip(),
                    "url": f"https://{brand.strip().lower().replace(' ', '')}.com",
                    "contact": contact_email,
                    "type": "sponsorship",
                    "source": "sponsorship"
                })
            
            return assets
        finally:
            db.close()

    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generates a call to action for sponsorships.
        """
        assets = await self.get_assets(niche)
        
        if assets:
            brand_name = assets[0].get("name", "our sponsors")
        else:
            brand_name = "amazing brands"
        
        options = [
            f"Huge thanks to {brand_name} for sponsoring this video! Check them out!",
            f"Proud to partner with {brand_name} - they make this content possible!",
            f"Shoutout to {brand_name} for supporting the channel!",
            f"{brand_name} - thanks for making this content happen!"
        ]
        return random.choice(options)
