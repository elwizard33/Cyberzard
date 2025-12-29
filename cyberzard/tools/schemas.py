"""Pydantic schemas for all Cyberzard tools.

This module defines input/output schemas for the unified tool registry,
enabling type validation and auto-documentation for LangChain and MCP.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================


class ToolCategory(str, Enum):
    """Categories for organizing tools."""

    SECURITY = "security"
    FILE = "file"
    SHELL = "shell"
    CYBERPANEL = "cyberpanel"
    EMAIL = "email"
    EXTERNAL = "external"


class PermissionLevel(str, Enum):
    """Permission levels for tool execution."""

    READ = "read"  # Read-only operations
    WRITE = "write"  # File/config modifications
    EXECUTE = "execute"  # Command execution
    ADMIN = "admin"  # Administrative actions (kill processes, etc.)


# ============================================================================
# File Operations Schemas
# ============================================================================


class ReadFileInput(BaseModel):
    """Input schema for read_file tool."""

    path: str = Field(..., description="Path to the file to read")
    max_bytes: Optional[int] = Field(
        32000, description="Maximum bytes to read (default 32KB)"
    )


class ReadFileOutput(BaseModel):
    """Output schema for read_file tool."""

    success: bool = Field(..., description="Whether the operation succeeded")
    path: str = Field(..., description="Path that was read")
    content: Optional[str] = Field(None, description="File content if successful")
    truncated: Optional[bool] = Field(
        None, description="Whether content was truncated"
    )
    error: Optional[str] = Field(None, description="Error message if failed")


class ListDirInput(BaseModel):
    """Input schema for list_dir tool."""

    path: str = Field(..., description="Path to the directory to list")


class ListDirOutput(BaseModel):
    """Output schema for list_dir tool."""

    items: Optional[List[str]] = Field(None, description="List of items in directory")
    status: str = Field(..., description="Operation status")
    error: Optional[str] = Field(None, description="Error message if failed")


# ============================================================================
# Security Scanning Schemas
# ============================================================================


class ScanServerInput(BaseModel):
    """Input schema for scan_server tool."""

    include_encrypted: bool = Field(
        False, description="Whether to scan for encrypted files"
    )


class ProcessIndicator(BaseModel):
    """A suspicious process indicator."""

    indicator: str = Field(..., description="Process name pattern matched")
    matches: List[str] = Field(..., description="Matching process lines from ps")


class CronSuspiciousEntry(BaseModel):
    """A suspicious cron entry."""

    file: str = Field(..., description="Cron file path")
    line_no: int = Field(..., description="Line number")
    text: str = Field(..., description="Cron line content")
    matched: str = Field(..., description="Matched suspicious pattern")


class SystemdUnit(BaseModel):
    """Information about a systemd unit."""

    name: str = Field(..., description="Unit name without .service suffix")
    unit: str = Field(..., description="Full unit name")
    status: str = Field(..., description="Unit status")
    unit_file: Optional[str] = Field(None, description="Path to unit file if exists")
    excerpt: Optional[str] = Field(None, description="First 20 lines of unit file")


class UserInfo(BaseModel):
    """Information about a system user."""

    name: str = Field(..., description="Username")
    uid: int = Field(..., description="User ID")
    home: str = Field(..., description="Home directory path")


class SSHFinding(BaseModel):
    """SSH-related finding for a user."""

    user: str = Field(..., description="Username")
    authorized_keys_file: str = Field(..., description="Path to authorized_keys")
    key_count: int = Field(..., description="Number of keys in file")
    sample_keys: List[str] = Field(..., description="First few key fingerprints")


class ScanServerOutput(BaseModel):
    """Output schema for scan_server tool."""

    success: bool = Field(..., description="Whether scan completed")
    processes: List[ProcessIndicator] = Field(
        default_factory=list, description="Suspicious processes found"
    )
    malicious_files: List[str] = Field(
        default_factory=list, description="Known malicious files found"
    )
    encrypted_files: List[str] = Field(
        default_factory=list, description="Encrypted files found"
    )
    cron_scan: Optional[Dict[str, Any]] = Field(
        None, description="Cron job scan results"
    )
    systemd_scan: Optional[Dict[str, Any]] = Field(
        None, description="Systemd unit scan results"
    )
    users_ssh_scan: Optional[Dict[str, Any]] = Field(
        None, description="Users and SSH scan results"
    )
    world_writable_scan: Optional[Dict[str, Any]] = Field(
        None, description="World-writable files scan results"
    )
    network_scan: Optional[Dict[str, Any]] = Field(
        None, description="Network connections scan results"
    )


class RunScanInput(BaseModel):
    """Input schema for run_scan tool."""

    target: Optional[str] = Field(None, description="Target to scan (optional)")


class RunScanOutput(BaseModel):
    """Output schema for run_scan tool."""

    target: str = Field(..., description="Target that was scanned")
    findings: List[Dict[str, Any]] = Field(
        default_factory=list, description="Scan findings"
    )
    status: str = Field(..., description="Scan status")


# ============================================================================
# Remediation Schemas
# ============================================================================


class RemediationAction(BaseModel):
    """A single remediation action."""

    action: str = Field(..., description="Action type (remove, kill, disable, etc.)")
    target: str = Field(..., description="Target of the action")
    reason: str = Field(..., description="Why this action is recommended")
    risk: str = Field("medium", description="Risk level (low, medium, high)")


class ProposeRemediationInput(BaseModel):
    """Input schema for propose_remediation tool."""

    scan_result: Dict[str, Any] = Field(
        ..., description="Scan result from scan_server"
    )


class ProposeRemediationOutput(BaseModel):
    """Output schema for propose_remediation tool."""

    success: bool = Field(..., description="Whether proposal was generated")
    actions: List[RemediationAction] = Field(
        default_factory=list, description="Recommended remediation actions"
    )
    summary: str = Field("", description="Summary of recommendations")


class ExecuteRemediationInput(BaseModel):
    """Input schema for execute_remediation tool."""

    action: str = Field(..., description="Action to execute (remove, kill, etc.)")
    target: str = Field(..., description="Target of the action")
    dry_run: bool = Field(True, description="Whether to simulate (default: true)")


class ExecuteRemediationOutput(BaseModel):
    """Output schema for execute_remediation tool."""

    status: str = Field(..., description="Result status")
    target: str = Field(..., description="Target that was acted upon")
    error: Optional[str] = Field(None, description="Error message if failed")


# ============================================================================
# Shell Command Schemas
# ============================================================================


class RunShellCommandInput(BaseModel):
    """Input schema for run_shell_command tool."""

    command: str = Field(..., description="Shell command to execute")


class RunShellCommandOutput(BaseModel):
    """Output schema for run_shell_command tool."""

    output: str = Field(..., description="Command output or error message")
    success: bool = Field(..., description="Whether command succeeded")


class DebugShellCommandInput(BaseModel):
    """Input schema for debug_shell_command tool."""

    command: str = Field(..., description="Shell command to debug")


class DebugShellCommandOutput(BaseModel):
    """Output schema for debug_shell_command tool."""

    result: str = Field(..., description="Debug result or suggestion")


class CompleteShellCommandInput(BaseModel):
    """Input schema for complete_shell_command tool."""

    partial: str = Field(..., description="Partial command to complete")


class CompleteShellCommandOutput(BaseModel):
    """Output schema for complete_shell_command tool."""

    suggestion: str = Field(..., description="Suggested completion")


# ============================================================================
# Sandbox Schemas
# ============================================================================


class SandboxRunInput(BaseModel):
    """Input schema for sandbox_run tool."""

    source: str = Field(..., description="Python source code to execute in sandbox")


class SandboxRunOutput(BaseModel):
    """Output schema for sandbox_run tool."""

    status: str = Field(..., description="Execution status")
    returncode: int = Field(..., description="Exit code (0 = success)")
    stdout: Optional[str] = Field(None, description="Standard output")
    output: Optional[str] = Field(None, description="Result output")
    result: Optional[Any] = Field(None, description="Eval result if applicable")
    error: Optional[str] = Field(None, description="Error message if failed")


# ============================================================================
# Email Security Schemas
# ============================================================================


class ScanEmailSystemInput(BaseModel):
    """Input schema for scan_email_system tool."""

    tail_lines: int = Field(
        500, description="Number of mail log lines to analyze"
    )


class ServiceStatus(BaseModel):
    """Status of a system service."""

    status: str = Field(..., description="Service status string")
    active: bool = Field(..., description="Whether service is active")


class SASLFailure(BaseModel):
    """SASL authentication failure information."""

    ip: str = Field(..., description="Source IP address")
    count: int = Field(..., description="Number of failures from this IP")


class ScanEmailSystemOutput(BaseModel):
    """Output schema for scan_email_system tool."""

    success: bool = Field(..., description="Whether scan completed")
    services: Dict[str, ServiceStatus] = Field(
        default_factory=dict, description="Service statuses"
    )
    queue_size: Optional[int] = Field(None, description="Mail queue size")
    sasl_failures: List[SASLFailure] = Field(
        default_factory=list, description="SASL auth failures"
    )
    tls_config: Dict[str, str] = Field(
        default_factory=dict, description="TLS configuration"
    )
    rate_limits: Dict[str, str] = Field(
        default_factory=dict, description="Rate limit configuration"
    )
    fail2ban_status: Optional[str] = Field(None, description="Fail2Ban jail status")
    flags: Dict[str, bool] = Field(
        default_factory=dict, description="Summary flags for quick assessment"
    )


class ProposeEmailHardeningInput(BaseModel):
    """Input schema for propose_email_hardening tool."""

    scan_result: Dict[str, Any] = Field(
        ..., description="Scan result from scan_email_system"
    )


class EmailHardeningAction(BaseModel):
    """A single email hardening recommendation."""

    action: str = Field(..., description="Action type")
    description: str = Field(..., description="What the action does")
    config_change: Optional[str] = Field(None, description="Config change if applicable")
    risk: str = Field("low", description="Risk level of the change")


class ProposeEmailHardeningOutput(BaseModel):
    """Output schema for propose_email_hardening tool."""

    success: bool = Field(..., description="Whether proposal was generated")
    actions: List[EmailHardeningAction] = Field(
        default_factory=list, description="Recommended hardening actions"
    )
    priority: str = Field("medium", description="Overall priority level")


# ============================================================================
# Tool Definition Schema
# ============================================================================


class ToolDefinition(BaseModel):
    """Schema for a registered tool in the unified registry."""

    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Human-readable description")
    category: ToolCategory = Field(..., description="Tool category")
    handler: str = Field(
        ..., description="Fully qualified name of the handler function"
    )
    input_schema: type = Field(..., description="Pydantic model for input validation")
    output_schema: type = Field(..., description="Pydantic model for output")
    permission_level: PermissionLevel = Field(
        PermissionLevel.READ, description="Required permission level"
    )
    tags: List[str] = Field(default_factory=list, description="Searchable tags")

    model_config = {"arbitrary_types_allowed": True}


__all__ = [
    # Enums
    "ToolCategory",
    "PermissionLevel",
    # File schemas
    "ReadFileInput",
    "ReadFileOutput",
    "ListDirInput",
    "ListDirOutput",
    # Security schemas
    "ScanServerInput",
    "ScanServerOutput",
    "ProcessIndicator",
    "CronSuspiciousEntry",
    "SystemdUnit",
    "UserInfo",
    "SSHFinding",
    "RunScanInput",
    "RunScanOutput",
    # Remediation schemas
    "RemediationAction",
    "ProposeRemediationInput",
    "ProposeRemediationOutput",
    "ExecuteRemediationInput",
    "ExecuteRemediationOutput",
    # Shell schemas
    "RunShellCommandInput",
    "RunShellCommandOutput",
    "DebugShellCommandInput",
    "DebugShellCommandOutput",
    "CompleteShellCommandInput",
    "CompleteShellCommandOutput",
    # Sandbox schemas
    "SandboxRunInput",
    "SandboxRunOutput",
    # Email schemas
    "ScanEmailSystemInput",
    "ScanEmailSystemOutput",
    "ServiceStatus",
    "SASLFailure",
    "ProposeEmailHardeningInput",
    "ProposeEmailHardeningOutput",
    "EmailHardeningAction",
    # Tool definition
    "ToolDefinition",
]
