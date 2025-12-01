import os
import asyncio
import sys
from dotenv import load_dotenv
from loguru import logger

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.adk_agents.bargainer.atomic_tools import initiate_call
from agents.adk_agents.shared.types import TripContext

# Load env vars
load_dotenv()

def main():
    print("\n📞 DesiYatra Live Agent Test 📞\n")
    print("This script will trigger a REAL call to your phone.")
    print("You will act as the Vendor. The Agent will negotiate with you.\n")

    # 1. Get User Input
    user_phone = input("Enter your phone number (e.g., +919876543210): ").strip()
    if not user_phone:
        print("Phone number is required!")
        return

    print("\nChoose your role:")
    print("1. Taxi Driver (Manali Trip)")
    print("2. Hotel Manager (Room Booking)")
    print("3. Restaurant Manager (Dinner Table)")
    choice = input("Selection [1]: ").strip() or "1"

    # 2. Setup Context
    if choice == "1":
        vendor_type = "Taxi"
        destination = "Manali"
        market_rate = 2500.0
        budget_max = 3000.0
        requirements = "one-way trip for 2 people"
        vendor_name = "Raju Taxi Service"
    elif choice == "2":
        vendor_type = "Hotel"
        destination = "Manali"
        market_rate = 1500.0
        budget_max = 2000.0
        requirements = "deluxe room with breakfast"
        vendor_name = "Hotel Mountain View"
    elif choice == "3":
        vendor_type = "Restaurant"
        destination = "Manali"
        market_rate = 800.0
        budget_max = 1000.0
        requirements = "dinner table for 4"
        vendor_name = "Sher-e-Punjab Dhaba"
    else:
        print("Invalid choice.")
        return

    print(f"\n🚀 Initiating call as '{vendor_name}' ({vendor_type})...")
    print(f"Agent Budget: ₹{budget_max} | Market Rate: ₹{market_rate}")
    
    # 3. Prepare Data
    party_size = 2
    if choice == "3":
        party_size = 4

    vendor = {
        "name": vendor_name,
        "phone": user_phone,
        "category": vendor_type.lower()
    }
    
    trip_context = {
        "destination": destination,
        "market_rate": market_rate,
        "budget_max": budget_max,
        "vendor_type": vendor_type,
        "requirements": requirements,
        "party_size": party_size
    }

    # 4. Trigger Call
    try:
        result = initiate_call(vendor, trip_context, use_real_twilio=True)
        
        if "error" in result:
            logger.error(f"Call failed: {result['error']}")
        else:
            logger.info(f"✅ Call initiated! SID: {result.get('twilio_call_sid')}")
            print("\n📲 Check your phone! The agent should be calling shortly.")
            print("Speak naturally in Hindi/Hinglish.")
            
    except Exception as e:
        logger.error(f"Script error: {e}")

if __name__ == "__main__":
    main()
