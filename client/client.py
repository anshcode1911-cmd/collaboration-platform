import grpc
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import service_pb2
import service_pb2_grpc

class CollaborationClient:
    def __init__(self, host='localhost', port=50051):
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = service_pb2_grpc.CollaborationServiceStub(self.channel)
        self.token = None
        self.username = None
    
    def login(self, username, password):
        request = service_pb2.LoginRequest(username=username, password=password)
        response = self.stub.Login(request)
        
        if response.status == "SUCCESS":
            self.token = response.token
            self.username = username
            print(f"✓ Login successful! Welcome, {username}")
            return True
        else:
            print("✗ Login failed. Check your credentials.")
            return False
    
    def logout(self):
        if not self.token:
            print("Not logged in")
            return
        
        request = service_pb2.LogoutRequest(token=self.token)
        response = self.stub.Logout(request)
        print(f"Logout: {response.message}")
        self.token = None
        self.username = None
    
    def create_document(self, content):
        if not self.token:
            print("Please login first")
            return
        
        request = service_pb2.PostRequest(
            token=self.token,
            type="document",
            data=content
        )
        response = self.stub.Post(request)
        print(f"✓ {response.message}")
    
    def update_document(self, doc_id, content):
        if not self.token:
            print("Please login first")
            return
        
        request = service_pb2.PostRequest(
            token=self.token,
            type="update",
            data=f"{doc_id}|{content}"
        )
        response = self.stub.Post(request)
        print(f"✓ {response.message}")
    
    def get_documents(self):
        if not self.token:
            print("Please login first")
            return
        
        request = service_pb2.GetRequest(
            token=self.token,
            type="documents",
            params=""
        )
        response = self.stub.Get(request)
        
        if response.status == "SUCCESS":
            print("\n=== Documents ===")
            for item in response.items:
                print(f"ID: {item.id}")
                print(f"Data: {item.data}")
                print("-" * 50)
        else:
            print("Failed to retrieve documents")
    
    def get_active_users(self):
        if not self.token:
            print("Please login first")
            return
        
        request = service_pb2.GetRequest(
            token=self.token,
            type="active_users",
            params=""
        )
        response = self.stub.Get(request)
        
        if response.status == "SUCCESS":
            print("\n=== Active Users ===")
            for item in response.items:
                print(f"• {item.data}")
        else:
            print("Failed to retrieve active users")
    
    def query_llm(self, query):
        if not self.token:
            print("Please login first")
            return
        
        request = service_pb2.GetRequest(
            token=self.token,
            type="llm_query",
            params=query
        )
        response = self.stub.Get(request)
        
        if response.status == "SUCCESS" and response.items:
            print("\n=== LLM Response ===")
            print(response.items[0].data)
        else:
            print("LLM query failed")
    
    def interactive_menu(self):
        while True:
            print("\n" + "="*50)
            print("Distributed Collaboration Platform - Milestone 1")
            print("="*50)
            
            if not self.token:
                print("\n1. Login")
                print("2. Exit")
                choice = input("\nChoice: ")
                
                if choice == "1":
                    username = input("Username: ")
                    password = input("Password: ")
                    self.login(username, password)
                elif choice == "2":
                    break
            else:
                print(f"\nLogged in as: {self.username}")
                print("\n1. Create Document")
                print("2. View All Documents")
                print("3. View Active Users")
                print("4. Query LLM (Grammar/Summarize/Suggest)")
                print("5. Logout")
                print("6. Exit")
                
                choice = input("\nChoice: ")
                
                if choice == "1":
                    content = input("Document content: ")
                    self.create_document(content)
                elif choice == "2":
                    self.get_documents()
                elif choice == "3":
                    self.get_active_users()
                elif choice == "4":
                    query = input("Enter your query (e.g., 'check grammar', 'summarize', 'suggest improvements'): ")
                    self.query_llm(query)
                elif choice == "5":
                    self.logout()
                elif choice == "6":
                    if self.token:
                        self.logout()
                    break

def main():
    print("Connecting to Application Server...")
    client = CollaborationClient()
    
    print("\n" + "="*50)
    print("Available test credentials:")
    print("  Username: admin  | Password: admin123")
    print("  Username: user1  | Password: password1")
    print("  Username: user2  | Password: password2")
    print("="*50)
    
    client.interactive_menu()
    print("\nGoodbye!")

if __name__ == '__main__':
    main()