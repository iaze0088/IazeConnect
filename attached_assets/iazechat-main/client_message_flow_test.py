#!/usr/bin/env python3
"""
🔴 CRITICAL TEST: Client Message → Ticket Creation Flow
Testing the fix for status mismatch issue where clients couldn't send messages.

CONTEXT:
- Backend was creating tickets with "EM_ESPERA" but frontend filtered for "open"
- Fix applied: Changed server.py lines 1732 and 1753 to use status="open"
- Need to verify complete flow works end-to-end

BACKEND URL: https://wppconnect-fix.preview.emergentagent.com
DATABASE: support_chat (NOT zendesk_ai)
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com"
TEST_CLIENT_WHATSAPP = "5511999999999"
TEST_CLIENT_PIN = "00"

class BackendTester:
    def __init__(self):
        self.session = None
        self.client_token = None
        self.client_id = None
        self.agent_token = None
        self.agent_id = None
        self.ticket_id = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")
        if details:
            print(f"     {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        if not success:
            print(f"❌ CRITICAL FAILURE in {test_name}")
    
    async def test_client_login(self):
        """Test 1: Client Login"""
        try:
            url = f"{BACKEND_URL}/api/auth/client/login"
            payload = {
                "whatsapp": TEST_CLIENT_WHATSAPP,
                "pin": TEST_CLIENT_PIN
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.client_token = data.get("token")
                    self.client_id = data.get("user_data", {}).get("id")
                    
                    if self.client_token and self.client_id:
                        self.log_test("Client Login", True, f"Client ID: {self.client_id[:8]}...")
                        return True
                    else:
                        self.log_test("Client Login", False, "Missing token or client_id in response")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Client Login", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Client Login", False, f"Exception: {str(e)}")
            return False
    
    async def test_get_agents(self):
        """Test 2: Get Available Agents"""
        try:
            url = f"{BACKEND_URL}/api/agents"
            headers = {"Authorization": f"Bearer {self.client_token}"}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    agents = await response.json()
                    if agents and len(agents) > 0:
                        self.agent_id = agents[0]["id"]
                        agent_name = agents[0].get("name", "Unknown")
                        self.log_test("Get Agents", True, f"Found {len(agents)} agents, using: {agent_name}")
                        return True
                    else:
                        self.log_test("Get Agents", False, "No agents found")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Get Agents", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Get Agents", False, f"Exception: {str(e)}")
            return False
    
    async def test_send_client_message(self):
        """Test 3: Send Message from Client"""
        try:
            url = f"{BACKEND_URL}/api/messages"
            headers = {"Authorization": f"Bearer {self.client_token}"}
            
            test_message = f"Teste de mensagem do cliente - {datetime.now().strftime('%H:%M:%S')}"
            
            payload = {
                "ticket_id": "",  # Empty for new ticket
                "from_type": "client",
                "from_id": self.client_id,
                "to_type": "agent", 
                "to_id": self.agent_id,
                "kind": "text",
                "text": test_message,
                "file_url": ""
            }
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    message_id = data.get("message_id")
                    
                    if message_id:
                        self.log_test("Send Client Message", True, f"Message sent successfully, Message ID: {message_id[:8]}...")
                        # We'll find the ticket_id in the next step by looking for recent tickets
                        return True
                    else:
                        self.log_test("Send Client Message", False, f"No message_id found in response: {data}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Send Client Message", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Send Client Message", False, f"Exception: {str(e)}")
            return False
    
    async def login_as_agent(self):
        """Helper: Login as agent to check tickets"""
        try:
            # First try admin login (can see all tickets regardless of tenant)
            admin_url = f"{BACKEND_URL}/api/auth/admin/login"
            admin_payload = {"password": "102030@ab"}
            
            async with self.session.post(admin_url, json=admin_payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.agent_token = data.get("token")
                    if self.agent_token:
                        print(f"     ✅ Admin login successful")
                        return True
            
            # Fallback to agent login
            url = f"{BACKEND_URL}/api/auth/agent/login"
            
            # Try common agent credentials
            test_credentials = [
                {"login": "fabio123", "password": "fabio123"},
                {"login": "admin", "password": "admin123"},
                {"login": "agent1", "password": "123456"},
                {"login": "teste", "password": "123"}
            ]
            
            for creds in test_credentials:
                async with self.session.post(url, json=creds) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.agent_token = data.get("token")
                        if self.agent_token:
                            print(f"     ✅ Agent login successful: {creds['login']}")
                            return True
            
            print(f"     ⚠️ Could not login as agent with test credentials")
            return False
            
        except Exception as e:
            print(f"     ❌ Agent login failed: {str(e)}")
            return False
    
    async def test_verify_ticket_creation(self):
        """Test 4: Verify Ticket Created with status='open'"""
        try:
            # We need to login as agent to check tickets
            if not await self.login_as_agent():
                self.log_test("Verify Ticket Creation", False, "Could not login as agent")
                return False
            
            url = f"{BACKEND_URL}/api/tickets"
            headers = {"Authorization": f"Bearer {self.agent_token}"}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    tickets = await response.json()
                    
                    # Find the most recent ticket for our client
                    our_ticket = None
                    for ticket in tickets:
                        if ticket.get("client_id") == self.client_id:
                            # This is a ticket for our client, check if it's the most recent
                            if not our_ticket or ticket.get("created_at", "") > our_ticket.get("created_at", ""):
                                our_ticket = ticket
                    
                    if our_ticket:
                        self.ticket_id = our_ticket.get("id")  # Store for later tests
                        status = our_ticket.get("status")
                        client_id = our_ticket.get("client_id")
                        ticket_origin = our_ticket.get("ticket_origin")
                        
                        if status == "open":
                            self.log_test("Verify Ticket Creation", True, 
                                        f"Ticket found with status='open', ticket_id={self.ticket_id[:8]}..., origin={ticket_origin}")
                            return True
                        else:
                            self.log_test("Verify Ticket Creation", False, 
                                        f"Ticket found but status='{status}' (should be 'open')")
                            return False
                    else:
                        self.log_test("Verify Ticket Creation", False, 
                                    f"No ticket found for client_id={self.client_id[:8]}... (total tickets: {len(tickets)})")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Verify Ticket Creation", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Verify Ticket Creation", False, f"Exception: {str(e)}")
            return False
    
    async def test_agent_dashboard_query(self):
        """Test 5: Agent Dashboard Query for status='open'"""
        try:
            url = f"{BACKEND_URL}/api/tickets?status=open"
            headers = {"Authorization": f"Bearer {self.agent_token}"}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    tickets = await response.json()
                    
                    # Check if our ticket appears
                    our_ticket = None
                    for ticket in tickets:
                        if ticket.get("id") == self.ticket_id:
                            our_ticket = ticket
                            break
                    
                    if our_ticket:
                        self.log_test("Agent Dashboard Query", True, 
                                    f"Ticket appears in status=open query (total: {len(tickets)} tickets)")
                        return True
                    else:
                        self.log_test("Agent Dashboard Query", False, 
                                    f"Ticket NOT found in status=open query (total: {len(tickets)} tickets)")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Agent Dashboard Query", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Agent Dashboard Query", False, f"Exception: {str(e)}")
            return False
    
    async def test_message_retrieval(self):
        """Test 6: Message Retrieval"""
        try:
            url = f"{BACKEND_URL}/api/messages?ticket_id={self.ticket_id}"
            headers = {"Authorization": f"Bearer {self.agent_token}"}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    messages = await response.json()
                    
                    # Find client message
                    client_messages = [msg for msg in messages if msg.get("from_type") == "client"]
                    
                    if client_messages:
                        self.log_test("Message Retrieval", True, 
                                    f"Found {len(client_messages)} client message(s) in ticket")
                        return True
                    else:
                        self.log_test("Message Retrieval", False, 
                                    f"No client messages found (total messages: {len(messages)})")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Message Retrieval", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Message Retrieval", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🔴 CRITICAL TEST: Client Message → Ticket Creation Flow")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Client: {TEST_CLIENT_WHATSAPP}")
        print("=" * 60)
        
        tests = [
            ("1️⃣ Client Login", self.test_client_login),
            ("2️⃣ Get Agents", self.test_get_agents), 
            ("3️⃣ Send Client Message", self.test_send_client_message),
            ("4️⃣ Verify Ticket Creation", self.test_verify_ticket_creation),
            ("5️⃣ Agent Dashboard Query", self.test_agent_dashboard_query),
            ("6️⃣ Message Retrieval", self.test_message_retrieval)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{test_name}")
            print("-" * 40)
            
            success = await test_func()
            if success:
                passed += 1
            else:
                print(f"❌ STOPPING - Critical test failed: {test_name}")
                break
        
        print("\n" + "=" * 60)
        print("🎯 FINAL RESULTS")
        print("=" * 60)
        
        success_rate = (passed / total) * 100
        
        if passed == total:
            print(f"🎉 ALL TESTS PASSED! ({passed}/{total}) - {success_rate:.0f}%")
            print("✅ Client Message → Ticket Creation flow is WORKING!")
            print("✅ Status mismatch issue has been RESOLVED!")
        else:
            print(f"❌ TESTS FAILED: {passed}/{total} passed ({success_rate:.0f}%)")
            print("🔴 Client Message → Ticket Creation flow has ISSUES!")
        
        print("\n📊 Test Summary:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        return passed == total

async def main():
    """Main test execution"""
    try:
        async with BackendTester() as tester:
            success = await tester.run_all_tests()
            return 0 if success else 1
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)