"""
v0.0.1.0 - Initial base code
v0.0.2.0 - Change serial configuration
"""
import socket
import serial
import struct
import threading
import time
from  fileSender import FileSender

SOFTWARE_VERSION = "0.0.2.0"
BINARY_START_BYTE = 0x7E

LISTEN_IP = "0.0.0.0"
COMMAND_PORT = 1235
TELEMETRY_PORT = 1234
TELEMETRY_IP = "cosmos-project_pwnsat-openc3-operator-1"

satellite_mode = "NORMAL"

ser = serial.Serial("/dev/ttyACM0", 115200)

sock_command = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_command.bind((LISTEN_IP, COMMAND_PORT))

sock_telemetry = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#define APID_TM_PING_ACK 201     // Response <- APID_TC_PING_SYNC
#define APID_TM_SEND_STATUS 450  // Response <- APID_TC_GET_STATUS
#define APID_TM_SEND_TEMP 451    // Response <- APID_TC_GET_TEMP
#define APID_TM_SEND_GYRO 452    // Response <- APID_TC_GET_GYRO
#define APID_TM_SEND_TM 453      // Response <- APID_TC_GET_TM

packet_chunck_count = 0

FLAG_SEGMENT_CONT = 0
FLAG_SEGMENT_START = 1
FLAG_SEGMENT_END = 2

def send_chunck_data(segment, length, chunck):
    command = f"{BINARY_START_BYTE}{segment}{length}{packet_chunck_count}{chunck}\r\n"
    ser.write(command.encode())

tlm_ids = {
    "ERROR": 0x4320,
    "STATUS": 0x4321,
    "PING": 0x4322,
    "TM": 0x4323,
    "TEMP": 0x4324,
    "GYRO": 0x4325,
    "IDLE": 0x4330
}

tlm_map = {
    "PING"  : "send_ping",
    "STATUS": "get_status",
    "GET_TEMP": "get_temp",
    "GET_GYRO": "get_gyro",
    "GET_TM": "get_tm",
    "MESSAGE": "send",
    "ERROR" : 0x4320
}

def send_gs_tc_response(command, message):
    id = tlm_ids[command]
    fmt = f'>h{len(message)}s'
    packed = struct.pack(fmt, id, message)
    sock_telemetry.sendto(packed, (TELEMETRY_IP, TELEMETRY_PORT))
    print(f"Sending {command} response: {message}")


def send_gs_serial_cmd(cmd, data=None):
    if data is not None:
        ser_cmd = f"{tlm_map[cmd]} {data}\r\n"
    else:
        ser_cmd = f"{tlm_map[cmd]}\r\n"
    ser.write(ser_cmd.encode())

def recv_worker():
    while True:
        try:
            data = ser.readline()
            if b"@;" in data:
                apid = data.split(b"@;")[0].replace(b"\r\n", b"")
                data = data.split(b"@;")[1].replace(b"\r\n", b"")
                if int(apid) == 201:
                    send_gs_tc_response("PING", f"PING:{data.decode()}".encode())
                elif int(apid) == 450:
                    send_gs_tc_response("STATUS", f"STATUS:{data.decode()}".encode())
                elif int(apid) == 451:  
                    send_gs_tc_response("TEMP", data)
                elif int(apid) == 452:
                    send_gs_tc_response("GYRO", data)
                elif int(apid) == 453 or int(apid) == 100:
                    send_gs_tc_response("TM", data)
                elif int(apid) == 100:
                    send_gs_tc_response("TM", data)
                elif int(apid) == 1023:
                    send_gs_tc_response("IDLE", data)
            time.sleep(0.1)
        except KeyboardInterrupt:
            ser.close()
            break


print("Satellite Ground Station Connector")
print(f"Version: {SOFTWARE_VERSION}")
print("Waiting for commands...")

threading.Thread(target=recv_worker, daemon=True).start()

while True:
    try:
        data, addr = sock_command.recvfrom(1024)
        try:
            command = struct.unpack_from(">h", data)[0]            
            if(command == 0):
                payload = struct.unpack_from(">f", data[2:])[0]
                send_gs_tc_response("STATUS", f"STATUS:FREQ:OK:{payload}")
            elif (command == 1):
                send_gs_serial_cmd("STATUS")
            elif (command == 2):
                send_gs_serial_cmd("GET_TEMP")
            elif (command == 3):
                send_gs_serial_cmd("GET_GYRO")
            elif (command == 4):
                send_gs_serial_cmd("GET_TM")
            elif (command == 5):
                str_cmd = data.decode('utf-8')
                send_gs_serial_cmd(str_cmd)
            elif (command == 9):
                send_gs_serial_cmd("PING")
            else:
                str_cmd = data.decode('utf-8')
                fileHandler = FileSender(str_cmd)
                print(fileHandler.getChunckArray())
                # send_chunck_data()
                # send_gs_serial_cmd(str_cmd)
        except Exception as e:
            print(e)
    except KeyboardInterrupt:
        ser.close()
        break
