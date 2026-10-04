"""
tools.py - 10 Dummy Tools for LangChain AI Agent.
Each tool is annotated with @tool from langchain_core.tools with detailed docstrings,
typed parameters, and realistic dummy data responses.
"""

from typing import Optional
from langchain_core.tools import tool
import re


@tool
def calculator(expression: str) -> str:
    """Perform mathematical calculations, arithmetic expressions, percentages, multiplications, and divisions.
    Args:
        expression: The mathematical expression to evaluate (e.g., '120 * 0.15', '25 * 48', '500 / 12').
    """
    try:
        # Clean expression to allow only safe math characters
        cleaned = re.sub(r"[^0-9+\-*/().% ]", "", expression)
        # Handle percentage (e.g. 15% -> 0.15)
        cleaned = re.sub(r"(\d+(\.\d+)?)%", r"(\1/100.0)", cleaned)
        # Safe evaluation of arithmetic
        result = eval(cleaned, {"__builtins__": None}, {})
        return f"Calculation Result: {expression} = {result}"
    except Exception as e:
        return f"Error evaluating expression '{expression}': {str(e)}"


@tool
def get_weather(city: str, days: int = 1) -> str:
    """Get the current weather forecast, temperature, precipitation, and conditions for a given city.
    Args:
        city: The name of the city or location (e.g., 'Seattle', 'New York', 'Tokyo').
        days: Number of forecast days to look ahead (default is 1).
    """
    weather_database = {
        "seattle": "58°F (14°C), Light Rain, Humidity 82%, Wind 9 mph SW. Forecast: 60% chance of showers tomorrow.",
        "new york": "72°F (22°C), Sunny, Humidity 45%, Wind 6 mph NE. Forecast: Clear skies for the next 3 days.",
        "tokyo": "68°F (20°C), Clear, Humidity 50%, Wind 4 mph SE. Forecast: Mild autumn conditions.",
        "london": "55°F (13°C), Overcast with drizzle, Humidity 88%, Wind 12 mph W. Forecast: Continued cloudiness.",
        "san francisco": "64°F (18°C), Partly Cloudy with coastal fog, Humidity 75%, Wind 14 mph W.",
        "chicago": "61°F (16°C), Breezy, Humidity 52%, Wind 18 mph N. Forecast: Sunny and crisp.",
    }
    key = city.lower().strip()
    report = weather_database.get(
        key,
        f"65°F (18°C), Partly Cloudy, Humidity 60%, Wind 8 mph. Standard seasonal conditions for {city}."
    )
    return f"Weather Report for {city.title()} ({days}-day outlook):\n{report}"


@tool
def search_knowledge_base(query: str, department: str = "general") -> str:
    """Search internal company knowledge base, employee policies, HR benefits, IT setup guides, and handbooks.
    Args:
        query: The topic or policy to search for (e.g., 'parental leave', 'travel reimbursement', 'vpn setup').
        department: Optional department filter ('hr', 'it', 'finance', 'general').
    """
    kb_records = {
        "parental leave": (
            "HR Policy Section 4.2 - Parental Leave: Full-time employees are eligible for up to 16 weeks "
            "of 100% paid parental leave for the birth, adoption, or foster placement of a child. "
            "Leave can be taken continuously or in two separate blocks within the first 12 months."
        ),
        "travel reimbursement": (
            "Finance Policy Section 7.1 - Travel Expenses: Daily meal per diem is up to $85/day without receipts. "
            "Flight bookings must be economy class booked at least 14 days in advance via Navan portal."
        ),
        "vpn setup": (
            "IT Helpdesk Doc #104 - Remote VPN Access: Connect via GlobalProtect client using your SSO credentials "
            "and Duo 2-Factor push. Gateway address: vpn.internal.acme.corp."
        ),
        "vacation policy": (
            "HR Policy Section 3.1 - Paid Time Off (PTO): Standard accrual is 20 days per year plus 11 company holidays. "
            "Up to 5 unused PTO days can roll over to the next calendar year."
        ),
        "health insurance": (
            "HR Benefits Section 2.0 - Medical, Dental & Vision: Company covers 90% of employee premiums and 75% "
            "for dependents. Open enrollment occurs every November."
        ),
    }

    query_lower = query.lower()
    for topic, content in kb_records.items():
        if topic in query_lower or any(word in query_lower for word in topic.split()):
            return f"Knowledge Base Result [{department.upper()}]:\n{content}"

    return (
        f"Knowledge Base Result for '{query}' [{department.upper()}]:\n"
        f"Found standard company documentation regarding '{query}'. Employees should consult the intranet portal "
        f"or contact the {department} team at support@company.internal for specific approvals."
    )


@tool
def check_order_status(order_id: str) -> str:
    """Track shipment status, package location, delivery dates, and carrier details for customer orders.
    Args:
        order_id: The order identifier (e.g., '#ORD-98214', 'ORD-1234', '10928').
    """
    cleaned_id = order_id.strip().upper()
    return (
        f"Order Status for {cleaned_id}:\n"
        f"- Status: Out for Delivery (Scheduled by 4:30 PM Today)\n"
        f"- Carrier: FedEx Express (Tracking #FX-{abs(hash(cleaned_id)) % 1000000000:09d})\n"
        f"- Items: 2 items (Standard Express Shipping)\n"
        f"- Destination: Customer Delivery Address on file\n"
        f"- Delivery Signature: Not Required"
    )


@tool
def check_flight_status(flight_number: str) -> str:
    """Lookup real-time flight status, departure/arrival times, gate numbers, and delays for airline flights.
    Args:
        flight_number: Airline flight code (e.g., 'UA412', 'AA100', 'DL2045').
    """
    cleaned_flight = flight_number.strip().upper()
    return (
        f"Flight Information for {cleaned_flight}:\n"
        f"- Status: On Time (En Route)\n"
        f"- Route: San Francisco (SFO) -> Chicago O'Hare (ORD)\n"
        f"- Scheduled Departure: 1:15 PM PDT (Actual: 1:18 PM PDT)\n"
        f"- Scheduled Arrival: 7:22 PM CDT (Estimated: 7:15 PM CDT)\n"
        f"- Arrival Terminal: Terminal 1, Gate B14\n"
        f"- Baggage Claim: Carousel 4"
    )


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount of money from one currency to another using real-time foreign exchange rates.
    Args:
        amount: Numerical money amount (e.g., 250.0).
        from_currency: 3-letter source currency code (e.g., 'EUR', 'USD', 'GBP', 'JPY').
        to_currency: 3-letter target currency code (e.g., 'USD', 'EUR', 'CAD', 'JPY').
    """
    # Sample FX rates against USD
    rates_to_usd = {
        "USD": 1.0,
        "EUR": 1.09,
        "GBP": 1.30,
        "CAD": 0.74,
        "JPY": 0.0068,
        "AUD": 0.67,
        "CHF": 1.16,
    }
    src = from_currency.strip().upper()
    dst = to_currency.strip().upper()

    src_rate = rates_to_usd.get(src, 1.0)
    dst_rate = rates_to_usd.get(dst, 1.0)

    # Convert src -> USD -> dst
    amount_in_usd = amount * src_rate
    converted_amount = amount_in_usd / dst_rate
    exchange_rate = src_rate / dst_rate

    return (
        f"Currency Conversion:\n"
        f"{amount:,.2f} {src} = {converted_amount:,.2f} {dst}\n"
        f"Exchange Rate: 1 {src} = {exchange_rate:.4f} {dst} (Market midpoint rate)"
    )


@tool
def check_inventory_stock(item_name_or_sku: str, warehouse: str = "all") -> str:
    """Check product warehouse stock levels, SKU availability, reserve counts, and restocking dates.
    Args:
        item_name_or_sku: The product name or SKU code (e.g., 'MacBook Pro 16 inch', 'SKU-MBP16').
        warehouse: Warehouse location filter ('main', 'chicago', 'new_york', 'all').
    """
    item = item_name_or_sku.strip()
    return (
        f"Inventory Stock Report for '{item}':\n"
        f"- SKU: SKU-{abs(hash(item)) % 100000:05d}\n"
        f"- Total Available Quantity: 28 units\n"
        f"- Reserved / Pending Shipments: 4 units\n"
        f"- Location Distribution: Chicago Warehouse (18 units), Dallas Warehouse (10 units)\n"
        f"- Status: In Stock (Ready for immediate fulfillment)\n"
        f"- Next Incoming Restock: +50 units scheduled for next Tuesday"
    )


@tool
def lookup_customer_crm(identifier: str) -> str:
    """Retrieve customer account details, subscription tier, lifetime spend, and account manager from CRM.
    Args:
        identifier: Customer email address, phone number, or customer ID (e.g., 'john.doe@example.com').
    """
    ident = identifier.strip()
    return (
        f"CRM Customer Profile for '{ident}':\n"
        f"- Customer ID: CUST-78219\n"
        f"- Name: Johnathan Doe\n"
        f"- Email: {ident if '@' in ident else 'j.doe@example.com'}\n"
        f"- Account Tier: Enterprise Gold (Member since 2022)\n"
        f"- Lifetime Value (LTV): $18,450.00\n"
        f"- Open Support Tickets: 0\n"
        f"- Account Executive: Sarah Jenkins (East Coast Enterprise Team)"
    )


@tool
def refund_transaction(order_id: str, amount: float, reason: str) -> str:
    """Process a payment refund or transaction chargeback for a customer order with a specified reason.
    Args:
        order_id: The order identifier to refund (e.g., '#ORD-1234', 'ORD-98214').
        amount: Dollar amount to be refunded (e.g., 45.0).
        reason: Explanation for the refund (e.g., 'damaged item', 'duplicate billing', 'wrong size').
    """
    refund_id = f"REF-{abs(hash(order_id + str(amount))) % 1000000:06d}"
    return (
        f"Refund Confirmation:\n"
        f"- Status: APPROVED & PROCESSED\n"
        f"- Refund ID: {refund_id}\n"
        f"- Order ID: {order_id.strip().upper()}\n"
        f"- Amount Credited: ${amount:,.2f} USD\n"
        f"- Reason Logged: '{reason}'\n"
        f"- Payment Method: Original Credit Card (ending in 4092)\n"
        f"- Processing Timeline: Credited to customer statement within 2-3 business days"
    )


@tool
def send_email_notification(recipient: str, subject: str, message: str) -> str:
    """Send an email notification, dispatch alerts, or customer communication to a recipient email.
    Args:
        recipient: Email address of the recipient (e.g., 'sarah@acme.com').
        subject: Subject line of the email.
        message: The email body content or message to send.
    """
    return (
        f"Email Dispatch Confirmation:\n"
        f"- Recipient: {recipient.strip()}\n"
        f"- Subject: {subject.strip()}\n"
        f"- Delivery Status: 250 OK - Message accepted for delivery\n"
        f"- Message Preview: \"{message[:80]}{'...' if len(message) > 80 else ''}\"\n"
        f"- Timestamp: Sent successfully via Acme SMTP Relay"
    )


# All 10 dummy tools organized in a list
ALL_TOOLS = [
    calculator,
    get_weather,
    search_knowledge_base,
    check_order_status,
    check_flight_status,
    convert_currency,
    check_inventory_stock,
    lookup_customer_crm,
    refund_transaction,
    send_email_notification,
]

# Mapping tool name -> tool object
TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}

# Criteria mapping for the Laya decision model
LAYA_TOOL_CRITERIA = {
    "calculator": "calculating tips, bill subtotals, performing arithmetic calculations, math equations, percentages, operations, multiplication, division",
    "get_weather": "weather forecasts, current weather, temperature, rain, climate in a city or location",
    "search_knowledge_base": "searching internal company policies, HR benefits, employee handbook, IT guides, vacation rules",
    "check_order_status": "tracking packages, delivery dates, shipping status, carrier tracking for customer orders",
    "check_flight_status": "checking airline flight status, departures, arrivals, airport gate numbers, flight delays",
    "convert_currency": "converting money amounts between currencies like USD, EUR, GBP, JPY, foreign exchange",
    "check_inventory_stock": "checking warehouse product stock, SKU quantities, inventory counts, product availability",
    "lookup_customer_crm": "retrieving customer contact info, account tiers, CRM profiles, lifetime value by email or name",
    "refund_transaction": "processing refunds, returning customer money, order chargebacks, billing reimbursements",
    "send_email_notification": "sending email messages, drafts, dispatching alerts and emails to recipients",
    "none": "casual small talk, greetings like hello or hi, conversational chit-chat without any task",
}
