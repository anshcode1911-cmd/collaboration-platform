import grpc
from concurrent import futures
import sys
import os
import uuid
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import service_pb2
import service_pb2_grpc
from app_server.auth import AuthManager
from app_server.document_manager import DocumentManager

class CollaborationServicer(service_pb2_grpc.CollaborationServiceServicer):
    def __init__(self, llm_stub):
        self.auth_manager = AuthManager()
        self.doc_manager = DocumentManager()
        self.llm_stub = llm_stub
        print("Application Server initialized")
    
    def Login(self, request, context):
        print(f"Login attempt: {request.username}")
        success, token = self.auth_manager.authenticate(request.username, request.password)
        
        if success:
            self.doc_manager.add_active_user(request.username)
            print(f"Login successful: {request.username}")
            return service_pb2.LoginResponse(
                status="SUCCESS",
                token=token
            )
        else:
            print(f"Login failed: {request.username}")
            return service_pb2.LoginResponse(
                status="FAILURE",
                token=""
            )
    
    def Logout(self, request, context):
        print(f"Logout request with token: {request.token[:8]}...")
        valid, username = self.auth_manager.validate_token(request.token)
        
        if valid:
            self.auth_manager.logout(request.token)
            self.doc_manager.remove_active_user(username)
            print(f"Logout successful: {username}")
            return service_pb2.StatusResponse(
                status="SUCCESS",
                message="Logged out successfully"
            )
        else:
            return service_pb2.StatusResponse(
                status="FAILURE",
                message="Invalid token"
            )
    
    def Post(self, request, context):
        print(f"Post request: type={request.type}")
        valid, username = self.auth_manager.validate_token(request.token)
        
        if not valid:
            return service_pb2.StatusResponse(
                status="FAILURE",
                message="Invalid token"
            )
        
        if request.type == "document":
            doc_id = self.doc_manager.create_document(username, request.data)
            print(f"Document created: {doc_id} by {username}")
            return service_pb2.StatusResponse(
                status="SUCCESS",
                message=f"Document created with ID: {doc_id}"
            )
        elif request.type == "update":
            parts = request.data.split("|", 1)
            if len(parts) == 2:
                doc_id, content = parts
                if self.doc_manager.update_document(doc_id, content, username):
                    print(f"Document updated: {doc_id}")
                    return service_pb2.StatusResponse(
                        status="SUCCESS",
                        message="Document updated"
                    )
        
        return service_pb2.StatusResponse(
            status="FAILURE",
            message="Invalid request"
        )
    
    def Get(self, request, context):
        print(f"Get request: type={request.type}")
        valid, username = self.auth_manager.validate_token(request.token)
        
        if not valid:
            return service_pb2.GetResponse(
                status="FAILURE",
                items=[]
            )
        
        if request.type == "documents":
            docs = self.doc_manager.get_all_documents()
            items = [
                service_pb2.DataItem(
                    id=doc["id"],
                    data=f"{doc['content']} | Author: {doc['author']} | Version: {doc['version']}"
                )
                for doc in docs
            ]
            return service_pb2.GetResponse(status="SUCCESS", items=items)
        
        elif request.type == "active_users":
            users = self.doc_manager.get_active_users()
            items = [
                service_pb2.DataItem(id=str(i), data=user)
                for i, user in enumerate(users)
            ]
            return service_pb2.GetResponse(status="SUCCESS", items=items)
        
        elif request.type == "llm_query":
            try:
                print(f"Forwarding query to LLM: {request.params}")
                llm_response = self.llm_stub.GetLLMAnswer(
                    service_pb2.LLMRequest(
                        request_id=str(uuid.uuid4()),
                        query=request.params,
                        context="Document collaboration system"
                    ),
                    timeout=10  # Add timeout
                )
                print(f"LLM response received: {llm_response.answer[:50]}...")
                items = [
                    service_pb2.DataItem(
                        id="llm_response",
                        data=llm_response.answer
                    )
                ]
                return service_pb2.GetResponse(status="SUCCESS", items=items)
            except grpc.RpcError as e:
                error_msg = f"LLM Server connection error: {e.code()} - {e.details()}"
                print(error_msg)
                return service_pb2.GetResponse(
                    status="FAILURE",
                    items=[service_pb2.DataItem(id="error", data="LLM Server is not running. Please start it first.")]
                )
            except Exception as e:
                print(f"LLM query error: {e}")
                return service_pb2.GetResponse(
                    status="FAILURE",
                    items=[service_pb2.DataItem(id="error", data=f"Error: {str(e)}")]
                )
        
        return service_pb2.GetResponse(status="FAILURE", items=[])

def serve():
    # Connect to LLM server with retry logic
    print("Connecting to LLM Server at localhost:50052...")
    max_retries = 5
    retry_delay = 2
    
    llm_channel = None
    llm_stub = None
    
    for attempt in range(max_retries):
        try:
            llm_channel = grpc.insecure_channel('localhost:50052')
            llm_stub = service_pb2_grpc.LLMServiceStub(llm_channel)
            
            # Test connection
            test_request = service_pb2.LLMRequest(
                request_id="test",
                query="test connection",
                context="test"
            )
            llm_stub.GetLLMAnswer(test_request, timeout=5)
            print("✓ Successfully connected to LLM Server")
            break
        except grpc.RpcError as e:
            if attempt < max_retries - 1:
                print(f"⚠ LLM Server not ready, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print("✗ WARNING: Could not connect to LLM Server!")
                print("  The Application Server will start, but LLM queries will fail.")
                print("  Please ensure LLM Server is running on port 50052")
                # Create a dummy stub that will fail gracefully
                llm_channel = grpc.insecure_channel('localhost:50052')
                llm_stub = service_pb2_grpc.LLMServiceStub(llm_channel)
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_CollaborationServiceServicer_to_server(
        CollaborationServicer(llm_stub), server
    )
    
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Application Server started on port 50051")
    print("\nReady to accept client connections!")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()