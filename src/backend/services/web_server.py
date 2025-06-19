"""
Web Server Service

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

"""
Web Server Service - Web-based interface for AI Coder Assistant.
"""

import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.services.llm_manager import LLMManager

logger = logging.getLogger(__name__)


@dataclass
class WebServerConfig:
    """Web server configuration."""
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    enable_cors: bool = True
    static_files_path: Optional[str] = None


class WebServerService:
    """Main web server service."""
    
    def __init__(self, config: WebServerConfig):
        self.config = config
        self.app = FastAPI(title="AI Coder Assistant Web Interface")
        self.llm_manager = LLMManager()
        self.active_connections: List[WebSocket] = []
        self.server_thread: Optional[threading.Thread] = None
        self.server_running = False
        
        self.setup_middleware()
        self.setup_routes()
        self.setup_websockets()
    
    def setup_middleware(self):
        """Setup middleware."""
        if self.config.enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
    
    def setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {"message": "AI Coder Assistant Web Interface", "status": "running"}
        
        @self.app.get("/api/status")
        async def get_status():
            """Get server status."""
            return {
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "connections": len(self.active_connections)
            }
        
        @self.app.post("/api/analyze")
        async def analyze_code(request: Dict[str, Any]):
            """Analyze code."""
            try:
                code = request.get("code", "")
                language = request.get("language", "python")
                
                # Use LLM manager for analysis
                result = await self.llm_manager.analyze_code(code, language)
                return {"success": True, "result": result}
            except Exception as e:
                logger.error(f"Error analyzing code: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/scan")
        async def scan_directory(request: Dict[str, Any]):
            """Scan directory for issues."""
            try:
                directory = request.get("directory", "")
                if not directory or not Path(directory).exists():
                    raise HTTPException(status_code=400, detail="Invalid directory")
                
                # Use LLM manager for scanning
                result = await self.llm_manager.scan_directory(directory)
                return {"success": True, "result": result}
            except Exception as e:
                logger.error(f"Error scanning directory: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/providers")
        async def get_providers():
            """Get available LLM providers."""
            try:
                providers = self.llm_manager.get_available_providers()
                return {"success": True, "providers": providers}
            except Exception as e:
                logger.error(f"Error getting providers: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/chat")
        async def chat(request: Dict[str, Any]):
            """Chat with AI."""
            try:
                message = request.get("message", "")
                provider = request.get("provider", "default")
                
                if not message:
                    raise HTTPException(status_code=400, detail="Message is required")
                
                # Use LLM manager for chat
                response = await self.llm_manager.chat(message, provider)
                return {"success": True, "response": response}
            except Exception as e:
                logger.error(f"Error in chat: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def setup_websockets(self):
        """Setup WebSocket endpoints."""
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication."""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle different message types
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    elif message.get("type") == "analyze":
                        # Handle real-time analysis
                        result = await self.handle_realtime_analysis(message)
                        await websocket.send_text(json.dumps(result))
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Unknown message type"
                        }))
                        
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
    
    async def handle_realtime_analysis(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle real-time analysis requests."""
        try:
            code = message.get("code", "")
            language = message.get("language", "python")
            
            # Perform analysis
            result = await self.llm_manager.analyze_code(code, language)
            
            return {
                "type": "analysis_result",
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "type": "analysis_result",
                "success": False,
                "error": str(e)
            }
    
    def start_server(self):
        """Start the web server in a separate thread."""
        if self.server_running:
            logger.warning("Server is already running")
            return
        
        def run_server():
            try:
                uvicorn.run(
                    self.app,
                    host=self.config.host,
                    port=self.config.port,
                    log_level="info" if self.config.debug else "warning"
                )
            except Exception as e:
                logger.error(f"Error starting server: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.server_running = True
        
        logger.info(f"Web server started on http://{self.config.host}:{self.config.port}")
    
    def stop_server(self):
        """Stop the web server."""
        if not self.server_running:
            logger.warning("Server is not running")
            return
        
        # Close all WebSocket connections
        for websocket in self.active_connections[:]:
            try:
                websocket.close()
            except Exception:
                pass
        self.active_connections.clear()
        
        self.server_running = False
        logger.info("Web server stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status."""
        return {
            "running": self.server_running,
            "host": self.config.host,
            "port": self.config.port,
            "connections": len(self.active_connections),
            "timestamp": datetime.now().isoformat()
        }
    
    def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = []
        
        for websocket in self.active_connections:
            try:
                websocket.send_text(message_json)
            except Exception:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket) 