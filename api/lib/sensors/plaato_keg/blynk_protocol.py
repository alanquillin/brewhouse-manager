import struct
from enum import IntEnum
from typing import List, Optional, Union


class BlynkCommand(IntEnum):
    RESPONSE = 0
    REGISTER = 1
    LOGIN = 2
    SAVE_PROF = 3
    LOAD_PROF = 4
    GET_TOKEN = 5
    PING = 6
    ACTIVATE = 7
    DEACTIVATE = 8
    REFRESH = 9
    GET_GRAPH_DATA = 10
    GET_GRAPH_DATA_RESPONSE = 11
    TWEET = 12
    EMAIL = 13
    NOTIFY = 14
    BRIDGE = 15
    HARDWARE_SYNC = 16
    INTERNAL = 17
    SMS = 18
    PROPERTY = 19
    HARDWARE = 20
    CREATE_DASH = 21
    SAVE_DASH = 22
    DELETE_DASH = 23
    LOAD_PROF_GZ = 24
    SYNC = 25
    SHARING = 26
    ADD_PUSH_TOKEN = 27
    GET_SHARED_DASH = 29
    GET_SHARE_TOKEN = 30
    REFRESH_SHARE_TOKEN = 31
    SHARE_LOGIN = 32
    REDIRECT = 41
    DEBUG_PRINT = 55
    EVENT_LOG = 64


class BlynkStatus(IntEnum):
    SUCCESS = 200
    QUOTA_LIMIT_EXCEPTION = 1
    ILLEGAL_COMMAND = 2
    NOT_REGISTERED = 3
    ALREADY_REGISTERED = 4
    NOT_AUTHENTICATED = 5
    NOT_ALLOWED = 6
    DEVICE_NOT_IN_NETWORK = 7
    NO_ACTIVE_DASHBOARD = 8
    INVALID_TOKEN = 9
    ILLEGAL_COMMAND_BODY = 11
    GET_GRAPH_DATA_EXCEPTION = 12
    NTF_INVALID_BODY = 13
    NTF_NOT_AUTHORIZED = 14
    NTF_EXCEPTION = 15
    TIMEOUT = 16
    NO_DATA_EXCEPTION = 17
    DEVICE_WENT_OFFLINE = 18
    SERVER_EXCEPTION = 19
    NOT_SUPPORTED_VERSION = 20
    ENERGY_LIMIT = 21
    UNKNOWN = -1


class BlynkMessage:
    command: BlynkCommand
    msg_id: int
    status: Optional[BlynkStatus]
    length: Optional[int]
    body: bytes

    def __init__(self, command: BlynkCommand = None, msg_id: int = None, status: BlynkStatus = None, length: int = None, body: bytes = None, **kwargs):
        self.command = command
        self.msg_id = msg_id
        self.status = status
        self.length = length
        self.body = body

    def __repr__(self):
        if self.command == BlynkCommand.RESPONSE:
            return f"BlynkMessage(command=RESPONSE, msg_id={self.msg_id}, status={self.status}, body={self.body})"
        return f"BlynkMessage(command={self.command}, msg_id={self.msg_id}, length={self.length}, body={self.body})"
    
    def __len__(self):
        if not self.length:
            return -1
        
        return self.length

    
def decode(data: bytes) -> List[BlynkMessage]:
    """Decode Blynk protocol messages from binary data"""
    messages = []
    offset = 0
    
    while offset < len(data):
        if len(data) - offset < 5:
            break
            
        cmd = data[offset]
        msg_id = struct.unpack('>H', data[offset+1:offset+3])[0]
        length = struct.unpack('>H', data[offset+3:offset+5])[0]
        
        try:
            cmd_enum = BlynkCommand(cmd)
        except ValueError:
            cmd_enum = f"unknown_cmd_{cmd}"
        
        if cmd_enum == BlynkCommand.RESPONSE:
            try:
                status = BlynkStatus(length)
            except ValueError:
                status = f"unknown_status_{length}"
            
            body_start = offset + 5
            if body_start < len(data):
                body = data[body_start:]
            else:
                body = b''
                
            messages.append(BlynkMessage(
                command=cmd_enum,
                msg_id=msg_id,
                status=status,
                body=body
            ))
            break
        else:
            body_start = offset + 5
            body_end = body_start + length
            
            if body_end > len(data):
                break
                
            body = data[body_start:body_end]
            
            messages.append(BlynkMessage(
                command=cmd_enum,
                msg_id=msg_id,
                length=length,
                body=body
            ))
            
            offset = body_end
            
    return messages

def encode_command(cmd: Union[BlynkCommand, int], msg_id: int, body: bytes = b'') -> bytes:
    """Encode a Blynk command message"""
    if isinstance(cmd, BlynkCommand):
        cmd_byte = cmd.value
    else:
        cmd_byte = cmd
        
    length = len(body)
    return struct.pack('>BHH', cmd_byte, msg_id, length) + body

def encode_response(msg_id: int, status: Union[BlynkStatus, int], body: bytes = b'') -> bytes:
    """Encode a Blynk response message"""
    if isinstance(status, BlynkStatus):
        status_value = status.value
    else:
        status_value = status
        
    length = len(body)
    return struct.pack('>BHHH', 0, msg_id, status_value, length) + body

def response_success(msg_id: int = 1) -> bytes:
    """Generate a standard success response"""
    return struct.pack('>BHH', 0, msg_id, BlynkStatus.SUCCESS.value)