import logging
import random
from typing import List, Dict, Any
from .base import BaseMonetizationStrategy
from api.utils.database import SessionLocal
from api.utils.models import SystemSettings

class CryptoStrategy(BaseMonetizationStrategy):
    """
    Crypto/Donations strategy - Accept crypto tips or donations
    """
    
    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        """
        Fetches crypto wallet addresses from database configuration.
        Returns available crypto wallets for donations/tips.
        """
        db = SessionLocal()
        try:
            # Check for configured crypto wallets
            wallets_setting = db.query(SystemSettings).filter(
                SystemSettings.key == "crypto_wallets"
            ).first()
            
            if not wallets_setting or not wallets_setting.value:
                logging.warning(f"[CryptoStrategy] No crypto wallets configured. Set 'crypto_wallets' in settings (format: BTC:addr,ETH:addr).")
                return []
            
            # Parse wallets (format: BTC:addr,ETH:addr,USDT:addr)
            assets = []
            wallet_str = wallets_setting.value
            
            if "BTC" in wallet_str.upper():
                btc_addr = self._extract_wallet(wallet_str, "BTC")
                if btc_addr:
                    assets.append({
                        "id": "btc_wallet",
                        "name": "Bitcoin",
                        "symbol": "BTC",
                        "address": btc_addr,
                        "type": "crypto"
                    })
            
            if "ETH" in wallet_str.upper():
                eth_addr = self._extract_wallet(wallet_str, "ETH")
                if eth_addr:
                    assets.append({
                        "id": "eth_wallet",
                        "name": "Ethereum", 
                        "symbol": "ETH",
                        "address": eth_addr,
                        "type": "crypto"
                    })
            
            if "USDT" in wallet_str.upper():
                usdt_addr = self._extract_wallet(wallet_str, "USDT")
                if usdt_addr:
                    assets.append({
                        "id": "usdt_wallet",
                        "name": "Tether (USDT)",
                        "symbol": "USDT",
                        "address": usdt_addr,
                        "type": "crypto"
                    })
            
            # Add generic donation link if configured
            donation_setting = db.query(SystemSettings).filter(
                SystemSettings.key == "donation_link"
            ).first()
            
            if donation_setting and donation_setting.value:
                assets.append({
                    "id": "donation_link",
                    "name": "Support via PayPal/Donation",
                    "url": donation_setting.value,
                    "type": "donation"
                })
            
            if not assets:
                logging.warning(f"[CryptoStrategy] Could not parse crypto wallets from: {wallets_setting.value}")
                return []
            
            return assets
        finally:
            db.close()
    
    def _extract_wallet(self, wallet_str: str, symbol: str) -> str:
        """Extract wallet address for a given symbol"""
        try:
            parts = wallet_str.split(",")
            for part in parts:
                if symbol.upper() in part.upper():
                    addr = part.split(":")[-1].strip()
                    if addr and len(addr) > 10:  # Basic validation
                        return addr
        except Exception:
            pass
        return None

    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generates a call to action for crypto tips/donations.
        """
        assets = await self.get_assets(niche)
        
        if assets:
            crypto_asset = next((a for a in assets if a.get("type") == "crypto"), assets[0])
            if crypto_asset.get("type") == "crypto":
                symbol = crypto_asset.get("symbol", "crypto")
                address = crypto_asset.get("address", "")[:10] + "..."
                options = [
                    f"Loved this content? Send a tip in {symbol}! \n📱 {address}",
                    f"Support this channel with {symbol}! Every bit helps: \n📱 {address}",
                    f"Appreciate the content? Drop a {symbol} tip: \n📱 {address}",
                    f"Help us create more content! {symbol} donations: \n📱 {address}"
                ]
            else:
                # Donation link
                url = crypto_asset.get("url", "https://donate.ettametta.ai")
                options = [
                    f"Enjoyed this? Support us here: \n🔗 {url}",
                    f"Help keep this channel going! Donate: \n🔗 {url}",
                    f"Any support helps! Link in bio: \n🔗 {url}"
                ]
        else:
            options = [
                "Enjoyed this? Support the channel! Link in bio 💜",
                "Help us create more content! Every bit helps 💜",
                "Like what you see? Support us! Link below 💜"
            ]
        
        return random.choice(options)
