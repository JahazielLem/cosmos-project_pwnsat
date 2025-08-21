import os
#/Users/astrobyte/Repos/PWNSAT_REPOS/FlatSat_Firmware/flatsat_v1/.pio/build/seeed_xiao_esp32s3/firmware.bin
class FileSender:
  def __init__(self, path=""):
    self.filepath = path
    self.open_file = None
    
  
  def open_binary(self):
    try:
      self.open_file = open(self.filepath, "rb")
      self.file_size = os.path.getsize(self.filepath)
      print(f"File size: {self.file_size}")
    except Exception as e:
      print(e)
  

  def getChunckArray(self):
    self.open_binary()
    offset = 0
    bytes_read = 0
    chuncks = []
    while (offset < self.file_size):
      self.open_file.seek(offset)
      file_data = self.open_file.read(128)
      bytes_read += len(file_data)
      offset += len(file_data)
      chuncks.append({
        "data": file_data,
        "len": len(file_data)
      })
    return chuncks

if __name__ == "__main__":
  fileHandler = FileSender("/Users/astrobyte/Documents/Arduino/esp32wipe/build/esp32.esp32.XIAO_ESP32S3_Plus/esp32wipe.ino.partitions.bin")
  print(fileHandler.getChunckArray())