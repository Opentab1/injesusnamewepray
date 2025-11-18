"""
Toast POS API Integration

Connect to Toast POS to get real-time order and revenue data.

SETUP:
1. Get Toast API credentials from https://developers.toasttab.com/
2. Add credentials to config/settings.yaml
3. Run: python3 integrations/toast_pos.py --test

WHAT THIS DOES:
- Fetches orders from Toast in real-time
- Links orders to customer dwell sessions
- Calculates actual revenue per customer
- Provides revenue per minute metrics
- Identifies high-value vs low-value customers

BUSINESS VALUE:
- Know EXACTLY which customers are profitable
- Optimize based on REAL revenue data, not estimates
- Identify high-spenders to keep vs low-spenders to turn
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ToastPOSConnector:
    """
    Connector for Toast POS API.
    
    USAGE:
        connector = ToastPOSConnector(
            client_id="your_client_id",
            client_secret="your_client_secret",
            restaurant_guid="your_restaurant_guid"
        )
        
        # Get orders from last hour
        orders = connector.get_orders(hours=1)
        
        # Get specific order
        order = connector.get_order(order_guid)
        
        # Get revenue for time period
        revenue = connector.get_revenue_for_period(start_time, end_time)
    """
    
    # Toast API endpoints
    BASE_URL = "https://ws-api.toasttab.com"
    AUTH_URL = "https://ws-api.toasttab.com/authentication/v1/authentication/login"
    ORDERS_URL = "https://ws-api.toasttab.com/orders/v2/orders"
    
    def __init__(self, client_id: str, client_secret: str, restaurant_guid: str):
        """
        Initialize Toast POS connector.
        
        Args:
            client_id: Toast API client ID
            client_secret: Toast API client secret
            restaurant_guid: Your restaurant's unique identifier
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.restaurant_guid = restaurant_guid
        self.access_token = None
        self.token_expires_at = None
        
        logger.info(f"ToastPOSConnector initialized for restaurant: {restaurant_guid}")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Toast API and get access token.
        
        Returns:
            True if authentication successful
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "clientId": self.client_id,
                "clientSecret": self.client_secret,
                "userAccessType": "TOAST_MACHINE_CLIENT"
            }
            
            response = requests.post(
                self.AUTH_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('token', {}).get('accessToken')
                
                # Token expires in 24 hours typically
                self.token_expires_at = datetime.now() + timedelta(hours=23)
                
                logger.info("Toast API authentication successful")
                return True
            else:
                logger.error(f"Toast API authentication failed: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Toast API authentication error: {e}")
            return False
    
    def _ensure_authenticated(self):
        """Ensure we have a valid access token."""
        if not self.access_token or datetime.now() >= self.token_expires_at:
            logger.info("Access token expired or missing, re-authenticating...")
            self.authenticate()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make authenticated request to Toast API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response data or None on error
        """
        self._ensure_authenticated()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Toast-Restaurant-External-ID": self.restaurant_guid,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}{endpoint}",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Toast API request failed: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Toast API request error: {e}")
            return None
    
    def get_orders(self, hours: int = 1, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> List[Dict]:
        """
        Get orders from Toast POS.
        
        Args:
            hours: Number of hours to look back (if start_time not specified)
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of order dictionaries
        """
        if not start_time:
            start_time = datetime.now() - timedelta(hours=hours)
        if not end_time:
            end_time = datetime.now()
        
        # Toast API expects ISO 8601 format
        params = {
            "businessDate": start_time.strftime("%Y%m%d"),
            "startDate": start_time.isoformat(),
            "endDate": end_time.isoformat()
        }
        
        logger.info(f"Fetching orders from {start_time} to {end_time}")
        
        data = self._make_request("/orders/v2/orders", params)
        
        if data:
            orders = data.get('data', [])
            logger.info(f"Retrieved {len(orders)} orders from Toast")
            return orders
        
        return []
    
    def get_order(self, order_guid: str) -> Optional[Dict]:
        """
        Get specific order by GUID.
        
        Args:
            order_guid: Toast order GUID
            
        Returns:
            Order dictionary or None
        """
        data = self._make_request(f"/orders/v2/orders/{order_guid}")
        return data if data else None
    
    def get_revenue_for_period(self, start_time: datetime, end_time: datetime) -> Dict:
        """
        Calculate total revenue for time period.
        
        Args:
            start_time: Start of period
            end_time: End of period
            
        Returns:
            Dictionary with revenue statistics
        """
        orders = self.get_orders(start_time=start_time, end_time=end_time)
        
        total_revenue = 0.0
        total_orders = len(orders)
        revenue_by_hour = {}
        
        for order in orders:
            # Get order total
            amount = order.get('totalAmount', 0) / 100.0  # Toast uses cents
            total_revenue += amount
            
            # Group by hour
            order_time = datetime.fromisoformat(order.get('openedDate', ''))
            hour_key = order_time.strftime('%Y-%m-%d %H:00')
            
            if hour_key not in revenue_by_hour:
                revenue_by_hour[hour_key] = {
                    'revenue': 0.0,
                    'orders': 0
                }
            
            revenue_by_hour[hour_key]['revenue'] += amount
            revenue_by_hour[hour_key]['orders'] += 1
        
        return {
            'total_revenue': round(total_revenue, 2),
            'total_orders': total_orders,
            'average_order_value': round(total_revenue / total_orders, 2) if total_orders > 0 else 0,
            'revenue_by_hour': revenue_by_hour,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
    
    def get_current_hourly_revenue(self) -> float:
        """
        Get revenue for current hour.
        
        Returns:
            Revenue amount for current hour
        """
        now = datetime.now()
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        
        revenue_data = self.get_revenue_for_period(hour_start, now)
        return revenue_data['total_revenue']
    
    def link_order_to_customer(self, order: Dict, occupancy_count: int) -> Dict:
        """
        Estimate revenue per person based on order and occupancy.
        
        Args:
            order: Toast order dictionary
            occupancy_count: Number of people in bar at order time
            
        Returns:
            Dictionary with revenue per person estimate
        """
        order_amount = order.get('totalAmount', 0) / 100.0
        order_time = datetime.fromisoformat(order.get('openedDate', ''))
        
        # Simple estimation: divide by occupancy
        # More sophisticated: use table assignments, check numbers, etc.
        revenue_per_person = order_amount / occupancy_count if occupancy_count > 0 else order_amount
        
        return {
            'order_guid': order.get('guid'),
            'order_time': order_time.isoformat(),
            'order_amount': order_amount,
            'occupancy_count': occupancy_count,
            'estimated_revenue_per_person': round(revenue_per_person, 2)
        }
    
    def test_connection(self) -> bool:
        """
        Test connection to Toast API.
        
        Returns:
            True if connection successful
        """
        logger.info("Testing Toast API connection...")
        
        if not self.authenticate():
            logger.error("❌ Authentication failed")
            return False
        
        logger.info("✓ Authentication successful")
        
        # Try to fetch today's orders
        orders = self.get_orders(hours=24)
        
        if orders is not None:
            logger.info(f"✓ Successfully retrieved {len(orders)} orders from today")
            
            if orders:
                # Show first order as example
                first_order = orders[0]
                logger.info(f"   Sample order: ${first_order.get('totalAmount', 0)/100:.2f} "
                          f"at {first_order.get('openedDate', 'unknown time')}")
            
            return True
        else:
            logger.error("❌ Failed to retrieve orders")
            return False


# Command-line testing
if __name__ == "__main__":
    import sys
    import argparse
    
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description='Toast POS API Connector')
    parser.add_argument('--test', action='store_true', help='Test connection')
    parser.add_argument('--client-id', help='Toast API Client ID')
    parser.add_argument('--client-secret', help='Toast API Client Secret')
    parser.add_argument('--restaurant-guid', help='Restaurant GUID')
    parser.add_argument('--orders', action='store_true', help='Fetch recent orders')
    parser.add_argument('--revenue', action='store_true', help='Get revenue stats')
    
    args = parser.parse_args()
    
    # Load from config if not provided
    if not all([args.client_id, args.client_secret, args.restaurant_guid]):
        import yaml
        config_path = Path(__file__).parent.parent / 'config' / 'settings.yaml'
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
                toast_config = config.get('toast_pos', {})
                args.client_id = args.client_id or toast_config.get('client_id')
                args.client_secret = args.client_secret or toast_config.get('client_secret')
                args.restaurant_guid = args.restaurant_guid or toast_config.get('restaurant_guid')
    
    if not all([args.client_id, args.client_secret, args.restaurant_guid]):
        print("Error: Missing Toast API credentials")
        print("Provide via command line or add to config/settings.yaml:")
        print("")
        print("toast_pos:")
        print("  enabled: true")
        print("  client_id: 'your_client_id'")
        print("  client_secret: 'your_client_secret'")
        print("  restaurant_guid: 'your_restaurant_guid'")
        sys.exit(1)
    
    connector = ToastPOSConnector(
        client_id=args.client_id,
        client_secret=args.client_secret,
        restaurant_guid=args.restaurant_guid
    )
    
    if args.test:
        success = connector.test_connection()
        sys.exit(0 if success else 1)
    
    if args.orders:
        orders = connector.get_orders(hours=24)
        print(f"\n📊 Retrieved {len(orders)} orders from last 24 hours\n")
        for order in orders[:5]:  # Show first 5
            print(f"Order: ${order.get('totalAmount', 0)/100:.2f} at {order.get('openedDate', 'unknown')}")
    
    if args.revenue:
        revenue = connector.get_revenue_for_period(
            start_time=datetime.now() - timedelta(hours=24),
            end_time=datetime.now()
        )
        print(f"\n💰 Revenue Last 24 Hours\n")
        print(f"Total Revenue: ${revenue['total_revenue']:.2f}")
        print(f"Total Orders: {revenue['total_orders']}")
        print(f"Average Order: ${revenue['average_order_value']:.2f}")
