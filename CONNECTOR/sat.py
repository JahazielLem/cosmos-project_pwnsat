import socket
import serial
import struct
import threading
import time

SOFTWARE_VERSION = "0.0.1"

LISTEN_IP = "0.0.0.0"
COMMAND_PORT = 1236
TELEMETRY_PORT = 1234
TELEMETRY_IP = "cosmos-project-openc3-operator-1"

satellite_mode = "NORMAL"

ser = serial.Serial("/dev/tty.usbmodem2123401", 115200)

sock_command = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_command.bind((LISTEN_IP, COMMAND_PORT))

sock_telemetry = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

tlm_ids = {
    "ERROR"   : 0x4320,
    "STATUS"  : 0x4321,
    "PING"    : 0x4322,
    "GET_TM"  : 0x4323,
    "GET_TEMP": 0x4324,
    "GET_GYRO": 0x4325
}

tlm_map = {
    "STATUS": "get_config",
    "PING"  : "ping",
    "GET_TM": "get_tm",
    "ERROR" : 0x4320
}

def recv_worker():
    while True:
        try:
            data = ser.readline()
            print(f"[SERIAL] Recv -> {data}")
            time.sleep(0.1)
        except KeyboardInterrupt:
            ser.close()
            break


print("Satellite Ground Station Connector")
print(f"Version: {SOFTWARE_VERSION}")
print("Waiting for commands...")

def send_gs_tc_response(command, message):
    id = tlm_ids[command]
    fmt = '>h12s'
    packed = struct.pack(fmt, id, message.encode("latin1"))
    sock_telemetry.sendto(packed, (TELEMETRY_IP, TELEMETRY_PORT))
    print(f"Sending TC response: {message}")


threading.Thread(target=recv_worker, daemon=True).start()

while True:
    try:
        data, addr = sock_command.recvfrom(1024)
        print(data)
        try:
            command = struct.unpack_from(">b", data)[0]
            print(f"[{addr}] Received command: {command}")
            if(command == 0):
                payload = struct.unpack_from(">f", data[1:])[0]
                send_gs_tc_response("STATUS", f"STATUS:FREQ:OK:{payload}")
            elif(command == 1):
                payload = struct.unpack_from(">f", data[1:])[0]
                send_gs_tc_response("STATUS", f"STATUS:BW:OK:{payload}")
            elif command == 2:
                payload = struct.unpack_from(">i", data[1:])[0]
                send_gs_tc_response("STATUS", f"STATUS:SP:OK:{payload}")
            elif command == 3:
                payload = struct.unpack_from(">i", data[1:])[0]
                send_gs_tc_response("STATUS", f"STATUS:CR:OK:{payload}")
            elif command == 4:
                payload = struct.unpack_from(">i", data[1:])[0]
                send_gs_tc_response("STATUS", f"STATUS:PL:OK:{payload}")
            else:
                str_cmd = data.decode('utf-8')
                if str_cmd == "PING":
                    send_gs_tc_response(str_cmd, "PING:ACK")
                elif str_cmd == "STATUS":
                    send_gs_tc_response(str_cmd, "STATUS:OK")
                elif str_cmd == "MODE":
                    send_gs_tc_response(str_cmd, "MODE:OK")
                elif str_cmd == "GET_TEMP":
                    send_gs_tc_response(str_cmd, "TEMP:OK")
                elif str_cmd == "GET_GYRO":
                    send_gs_tc_response(str_cmd, "GYRO:OK")
                elif str_cmd == "GET_TM":
                    send_gs_tc_response(str_cmd, "TM:OK")
                else:
                    send_gs_tc_response("ERROR", "UNKNOWN_CMD")

        except Exception as e:
            print(e)
    except KeyboardInterrupt:
        break