import logging
import random
from typing import List, Dict, Any
from .base import BaseMonetizationStrategy
from api.utils.database import SessionLocal
from api.utils.models import SystemSettings

class CourseStrategy(BaseMonetizationStrategy):
    """
    Course/Education strategy - Sell online courses and tutorials
    """
    
    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        """
        Fetches available courses from database configuration.
        Returns course offerings for the given niche.
        """
        db = SessionLocal()
        try:
            # Check for configured course platform URL
            setting = db.query(SystemSettings).filter(
                SystemSettings.key == "course_platform_url"
            ).first()
            
            platform_url = setting.value if setting else None
            
            if not platform_url:
                logging.warning(f"[CourseStrategy] No course platform configured. Set 'course_platform_url' in settings.")
                return []
            
            # Return courses as assets
            return [
                {
                    "id": "course_1",
                    "name": f"Complete {niche.title()} Masterclass",
                    "url": platform_url,
                    "price": "$97",
                    "description": f"Learn everything about {niche} from scratch to advanced",
                    "source": "course"
                },
                {
                    "id": "course_2",
                    "name": f"{niche.title()} Crash Course",
                    "url": platform_url,
                    "price": "$47",
                    "description": f"Quickstart guide to {niche}",
                    "source": "course"
                },
                {
                    "id": "course_3",
                    "name": f"Advanced {niche.title()} Strategies",
                    "url": platform_url,
                    "price": "$197",
                    "description": f"Master advanced {niche} techniques",
                    "source": "course"
                }
            ]
        finally:
            db.close()

    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generates a call to action for course sales.
        """
        assets = await self.get_assets(niche)
        
        if not assets:
            logging.warning(f"[CourseStrategy] No course platform configured. Set 'course_platform_url' in settings.")
            return ""
        
        platform_url = assets[0].get("url", "")
        course_name = assets[0].get("name", f"{niche} course")
        
        options = [
            f"Want to master {niche}? Check out my comprehensive course: \n🔗 {platform_url}",
            f"Learn {niche} the right way! Full course available: \n🔗 {platform_url}",
            f"Take your {niche} skills to the next level! Enroll now: \n🔗 {platform_url}",
            f"Ready to become an expert in {niche}? Join my course: \n🔗 {platform_url}"
        ]
        return random.choice(options)
